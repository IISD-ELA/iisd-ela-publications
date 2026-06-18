import html
import math
import os

from .config import (
    AUTHOR_TYPE_OPTIONS,
    DATA_TYPES,
    ENVIRONMENTAL_ISSUES,
    IGNORED_GENERAL_SEARCH_COLUMNS,
)
from .google_sheets import get_sheet_rows


def get_options(force_refresh=False):
    data = _load_normalized_data(force_refresh=force_refresh)
    publications = data["publications"]
    return {
        "data_types": DATA_TYPES,
        "environmental_issues": ENVIRONMENTAL_ISSUES,
        "author_type_options": AUTHOR_TYPE_OPTIONS,
        "authors": data["authors"],
        "lakes": _unique_lakes(publications),
        "year_range": _year_range(publications),
    }


def search_publications(params, force_refresh=False):
    data = _load_normalized_data(force_refresh=force_refresh)
    publications = data["publications"]

    data_type_query = params.get("data_type_tags", [])
    env_issue_query = params.get("env_issue_tags", [])
    lake_query = params.get("lake_tags", [])
    author_query = params.get("author_tags", [])
    author_type = _first(params.get("author_type"))
    year_start = _first(params.get("year_start"))
    year_end = _first(params.get("year_end"))
    general_search = _first(params.get("general_search"))

    results = list(publications)
    tag_queries_present = any(
        [data_type_query, env_issue_query, lake_query, author_query]
    )
    if tag_queries_present:
        results = [
            row
            for row in results
            if _matches_any_tag_query(
                row,
                data_type_query,
                env_issue_query,
                lake_query,
                author_query,
            )
        ]

    if year_start:
        results = [row for row in results if row.get("year", "") >= str(year_start)]
    if year_end:
        results = [row for row in results if row.get("year", "") <= str(year_end)]

    if general_search:
        needle = str(general_search).casefold()
        results = [
            row
            for row in results
            if any(
                needle in str(value).casefold()
                for key, value in row.items()
                if key not in IGNORED_GENERAL_SEARCH_COLUMNS
            )
        ]

    if author_type in (AUTHOR_TYPE_OPTIONS[1], AUTHOR_TYPE_OPTIONS[2]):
        relationship_map = {
            "authored": AUTHOR_TYPE_OPTIONS[1],
            "supported": AUTHOR_TYPE_OPTIONS[2],
        }
        results = [
            row
            for row in results
            if relationship_map.get(row.get("relationship_to_iisd_ela"))
            == author_type
            and row.get("type") not in ("msc", "phd")
        ]
    elif author_type == AUTHOR_TYPE_OPTIONS[3]:
        results = [row for row in results if row.get("type") in ("msc", "phd")]

    results = sorted(results, key=lambda row: (row.get("authors", ""), row.get("year", "")))
    return {
        "count": len(results),
        "results": [_format_result(row) for row in results],
    }


def _load_normalized_data(force_refresh=False):
    cache_ttl = int(os.getenv("PUBLICATIONS_CACHE_TTL_SECONDS", "300"))
    payload = get_sheet_rows(cache_ttl_seconds=cache_ttl, force_refresh=force_refresh)
    publications = [
        _normalize_publication(row)
        for row in payload["publications"]
        if row.get("approved") in ("Yes", "Not applicable")
    ]
    authors = sorted(
        {
            row.get("authors", "").strip()
            for row in payload["authors"]
            if row.get("authors", "").strip()
        }
    )
    return {"publications": publications, "authors": authors}


def _normalize_publication(row):
    normalized = {key: "" if value is None else str(value).strip() for key, value in row.items()}
    normalized["year"] = _year_string(normalized.get("year"))
    normalized["lake_tags"] = str(normalized.get("lake_tags", ""))
    normalized["type"] = normalized.get("type", "").lower()
    return normalized


def _matches_any_tag_query(row, data_type_query, env_issue_query, lake_query, author_query):
    return any(
        [
            data_type_query
            and _has_any(row.get("data_type_tags"), data_type_query),
            env_issue_query
            and _has_any(row.get("environmental_issue_tags"), env_issue_query),
            lake_query and _has_any(row.get("lake_tags"), [str(value) for value in lake_query]),
            author_query and _has_any_author(row.get("authors"), author_query),
        ]
    )


def _has_any(value, queries):
    values = {part.strip() for part in str(value or "").split("; ")}
    return any(str(query).strip() in values for query in queries)


def _has_any_author(value, queries):
    values = {_normalize_author_query(part) for part in str(value or "").split("; ")}
    return any(_normalize_author_query(query) in values for query in queries)


def _normalize_author_query(value):
    return str(value or "").replace("& ", "").strip().rstrip(";").strip()


def _unique_lakes(publications):
    lakes = set()
    for row in publications:
        for lake in str(row.get("lake_tags", "")).split("; "):
            if lake.isdigit():
                lakes.add(int(lake))
    return [str(lake) for lake in sorted(lakes)] + ["Other or Unspecified"]


def _year_range(publications):
    years = [row.get("year") for row in publications if row.get("year")]
    return {
        "min": min(years) if years else "",
        "max": max(years) if years else "",
    }


def _format_result(row):
    return {
        "citation_html": _format_citation(row),
        "tag_info": (
            f"Lakes: {row.get('lake_tags', '')}\n"
            f"Data Types: {row.get('data_type_tags', '')}\n"
            f"Environmental Issues: {row.get('environmental_issue_tags', '')}"
        ),
        "authors": row.get("authors", ""),
        "year": row.get("year", ""),
        "title": row.get("title", ""),
        "type": row.get("type", ""),
    }


def _format_citation(row):
    publication_type = row.get("type")
    authors = _escape(row.get("authors", "").replace(";", ","))
    year = _escape(row.get("year", ""))
    title = _escape(row.get("title", ""))
    doi_or_url = _link_or_text(row.get("doi_or_url", ""))

    if publication_type == "journal":
        journal = _escape(row.get("journal_name", ""))
        volume = _int_string(row.get("journal_vol_no"))
        issue = _int_string(row.get("journal_issue_no"))
        pages = str(row.get("journal_page_range", "")).strip()
        citation = f"{authors} ({year}). {title}. <em>{journal}</em>"
        if volume:
            citation += f", <em>{_escape(volume)}</em>"
        if issue:
            citation += f"({_escape(issue)})"
        if pages:
            citation += f", {_escape(pages)}"
        citation += "."
        if doi_or_url:
            citation += f" {doi_or_url}"
        return citation

    if publication_type in ("msc", "phd"):
        dissertation_type = (
            "Doctoral dissertation" if publication_type == "phd" else "Master of Science dissertation"
        )
        university = _escape(row.get("thesis_uni", ""))
        database = _escape(row.get("thesis_db", ""))
        citation = (
            f"{authors} ({year}). <em>{title}</em> "
            f"[{dissertation_type}, {university}]."
        )
        if database:
            citation += f" {database}."
        if doi_or_url:
            citation += f" {doi_or_url}"
        return citation

    return f"{authors} ({year}). {title}. {doi_or_url}".strip()


def _year_string(value):
    if value in (None, ""):
        return ""
    try:
        return str(int(float(str(value).strip())))
    except (TypeError, ValueError):
        return str(value).strip()


def _int_string(value):
    if value in (None, ""):
        return ""
    try:
        numeric = float(str(value).strip())
    except ValueError:
        return str(value).strip()
    if math.isnan(numeric):
        return ""
    return str(int(numeric))


def _escape(value):
    return html.escape(str(value or "").strip(), quote=True)


def _link_or_text(value):
    value = str(value or "").strip()
    if not value:
        return ""
    escaped = _escape(value)
    if value.startswith(("http://", "https://")):
        return f'<a href="{escaped}" target="_blank" rel="noopener noreferrer">{escaped}</a>'
    return escaped


def _first(values):
    if not values:
        return ""
    return values[0] if isinstance(values, list) else values

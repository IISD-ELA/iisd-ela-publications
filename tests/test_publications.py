import json

from publications_app import handler as handler_module
from publications_app import publications


PUBLICATION_ROWS = [
    {
        "approved": "Yes",
        "authors": "Alpha, A.; Paterson, M. J.",
        "year": "2021",
        "title": "Fish response",
        "type": "journal",
        "data_type_tags": "Fish",
        "environmental_issue_tags": "Climate Change",
        "lake_tags": "239",
        "relationship_to_iisd_ela": "authored",
        "journal_name": "Journal of Lakes",
        "journal_vol_no": "12.0",
        "journal_issue_no": "3.0",
        "journal_page_range": "1-2",
        "doi_or_url": "https://doi.org/10.0000/example",
        "approved_by": "reviewer-only",
    },
    {
        "approved": "Not applicable",
        "authors": "Student, S.",
        "year": "2020",
        "title": "Mercury thesis",
        "type": "msc",
        "data_type_tags": "Chemistry",
        "environmental_issue_tags": "Mercury",
        "lake_tags": "Other or Unspecified",
        "relationship_to_iisd_ela": "supported",
        "thesis_uni": "Lakehead University",
        "thesis_db": "Thesis Database",
        "doi_or_url": "",
    },
    {
        "approved": "No",
        "authors": "Hidden, H.",
        "year": "2022",
        "title": "Unapproved paper",
        "type": "journal",
        "data_type_tags": "Fish",
        "environmental_issue_tags": "Mercury",
        "lake_tags": "239",
    },
]


AUTHOR_ROWS = [
    {"authors": "Paterson, M. J."},
    {"authors": "Student, S."},
]


def fake_sheet_rows(cache_ttl_seconds=300, force_refresh=False):
    return {
        "publications": PUBLICATION_ROWS,
        "authors": AUTHOR_ROWS,
    }


def test_options_are_normalized_from_approved_publications(monkeypatch):
    monkeypatch.setattr(publications, "get_sheet_rows", fake_sheet_rows)

    options = publications.get_options()

    assert options["authors"] == ["Paterson, M. J.", "Student, S."]
    assert options["lakes"] == ["239", "Other or Unspecified"]
    assert options["year_range"] == {"min": "2020", "max": "2021"}


def test_tag_filters_use_or_logic(monkeypatch):
    monkeypatch.setattr(publications, "get_sheet_rows", fake_sheet_rows)

    result = publications.search_publications(
        {
            "data_type_tags": ["Fish"],
            "env_issue_tags": ["Mercury"],
        }
    )

    assert result["count"] == 2


def test_narrowing_filters_and_author_types(monkeypatch):
    monkeypatch.setattr(publications, "get_sheet_rows", fake_sheet_rows)

    current = publications.search_publications(
        {"author_type": ["Current IISD-ELA researchers"]}
    )
    students = publications.search_publications({"author_type": ["Students (theses)"]})
    ignored_metadata = publications.search_publications(
        {"general_search": ["reviewer-only"]}
    )

    assert current["count"] == 1
    assert "Fish response" in current["results"][0]["citation_html"]
    assert students["count"] == 1
    assert "Mercury thesis" in students["results"][0]["citation_html"]
    assert ignored_metadata["count"] == 0


def test_citation_html_escapes_and_links_journal_fields(monkeypatch):
    monkeypatch.setattr(publications, "get_sheet_rows", fake_sheet_rows)

    result = publications.search_publications({"author_tags": ["Paterson, M. J."]})
    citation = result["results"][0]["citation_html"]

    assert "<em>Journal of Lakes</em>, <em>12</em>(3), 1-2." in citation
    assert '<a href="https://doi.org/10.0000/example"' in citation


def test_empty_refresh_query_does_not_error(monkeypatch):
    monkeypatch.setattr(
        handler_module,
        "get_options",
        lambda force_refresh=False: {"force_refresh": force_refresh},
    )

    response = handler_module.handler(
        {
            "rawPath": "/api/options",
            "rawQueryString": "refresh=",
            "requestContext": {"http": {"method": "GET"}},
        },
        None,
    )

    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"force_refresh": False}


def test_removed_data_alias_returns_not_found():
    response = handler_module.handler(
        {
            "rawPath": "/api/data",
            "rawQueryString": "",
            "requestContext": {"http": {"method": "GET"}},
        },
        None,
    )

    assert response["statusCode"] == 404

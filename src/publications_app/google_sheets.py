import os
import time

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
from requests import RequestException

from .config import AUTHORS_WORKSHEET, PUBLICATIONS_WORKSHEET, get_spreadsheet_id
from .credentials import get_google_credentials_info


SCOPES = ("https://www.googleapis.com/auth/spreadsheets.readonly",)
_CACHE = {"expires_at": 0, "value": None}


def get_sheet_rows(cache_ttl_seconds=300, force_refresh=False):
    now = time.monotonic()
    if (
        not force_refresh
        and _CACHE["value"] is not None
        and _CACHE["expires_at"] > now
    ):
        return _CACHE["value"]

    credentials = service_account.Credentials.from_service_account_info(
        get_google_credentials_info(),
        scopes=SCOPES,
    )
    session = AuthorizedSession(credentials)
    response = _get_values(session)
    value_ranges = response.json().get("valueRanges", [])

    rows_by_sheet = {}
    for value_range in value_ranges:
        range_name = value_range.get("range", "")
        sheet_name = range_name.split("!", 1)[0].strip("'")
        rows_by_sheet[sheet_name] = value_range.get("values", [])

    payload = {
        "publications": _table_to_records(rows_by_sheet.get(PUBLICATIONS_WORKSHEET, [])),
        "authors": _table_to_records(rows_by_sheet.get(AUTHORS_WORKSHEET, [])),
    }
    _CACHE["value"] = payload
    _CACHE["expires_at"] = now + cache_ttl_seconds
    return payload


def _get_values(session):
    timeout_seconds = float(os.getenv("GOOGLE_SHEETS_TIMEOUT_SECONDS", "30"))
    max_attempts = max(1, int(os.getenv("GOOGLE_SHEETS_MAX_ATTEMPTS", "2")))
    last_error = None

    for attempt in range(max_attempts):
        try:
            response = session.get(
                f"https://sheets.googleapis.com/v4/spreadsheets/{get_spreadsheet_id()}/values:batchGet",
                params=[
                    ("ranges", PUBLICATIONS_WORKSHEET),
                    ("ranges", AUTHORS_WORKSHEET),
                    ("majorDimension", "ROWS"),
                ],
                timeout=timeout_seconds,
            )
            if response.status_code in (429, 500, 502, 503, 504):
                response.raise_for_status()
            if not response.ok:
                response.raise_for_status()
            return response
        except RequestException as error:
            last_error = error
            if attempt == max_attempts - 1:
                raise
            time.sleep(0.5 * (attempt + 1))

    raise last_error


def _table_to_records(rows):
    if not rows:
        return []

    headers = [str(header).strip() for header in rows[0]]
    records = []
    for row in rows[1:]:
        record = {}
        for index, header in enumerate(headers):
            record[header] = str(row[index]).strip() if index < len(row) else ""
        records.append(record)
    return records

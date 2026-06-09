import os

PUBLICATIONS_WORKSHEET = os.getenv("PUBLICATIONS_WORKSHEET", "Publications")
AUTHORS_WORKSHEET = os.getenv("AUTHORS_WORKSHEET", "Current_IISD-ELA_Authors")
SSM_PARAMETER_PREFIX = os.getenv(
    "GOOGLE_SHEETS_CREDENTIAL_PARAMETER_PREFIX",
    "/iisd-ela/config/publications",
)

GOOGLE_CREDENTIAL_FIELDS = (
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
)

DATA_TYPES = sorted(
    [
        "Physical Limnology",
        "Zooplankton",
        "Hydrology",
        "Meteorology",
        "Fish",
        "Chemistry",
        "Algae",
    ]
) + ["Other"]

ENVIRONMENTAL_ISSUES = sorted(
    [
        "Acid Rain",
        "Algal Blooms",
        "Climate Change",
        "Drugs",
        "Mercury",
        "Oil Spills",
        "Plastics",
    ]
) + ["Other"]

AUTHOR_TYPE_OPTIONS = [
    "<select a filter>",
    "Current IISD-ELA researchers",
    "Other researchers (supported by IISD-ELA)",
    "Students (theses)",
]

IGNORED_GENERAL_SEARCH_COLUMNS = {
    "source",
    "approved_date",
    "approved_by",
    "approved",
    "account",
    "update_date",
}


def get_spreadsheet_id():
    spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID", "").strip()
    if not spreadsheet_id:
        raise RuntimeError("GOOGLE_SPREADSHEET_ID must be set")
    return spreadsheet_id

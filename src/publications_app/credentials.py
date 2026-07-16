import os
from functools import lru_cache

from .config import GOOGLE_CREDENTIAL_FIELDS, SSM_PARAMETER_PREFIX


def _env_name(field_name):
    return f"GOOGLE_{field_name.upper()}"


def _normalise_private_key(value):
    return value.replace("\\n", "\n") if value else value


@lru_cache(maxsize=1)
def get_google_credentials_info():
    credentials = {
        field: os.getenv(_env_name(field))
        for field in GOOGLE_CREDENTIAL_FIELDS
        if os.getenv(_env_name(field))
    }

    missing_fields = [
        field for field in GOOGLE_CREDENTIAL_FIELDS if field not in credentials
    ]
    if missing_fields:
        credentials.update(_fetch_from_ssm(missing_fields))

    if "private_key" in credentials:
        credentials["private_key"] = _normalise_private_key(credentials["private_key"])

    missing_fields = [
        field for field in GOOGLE_CREDENTIAL_FIELDS if not credentials.get(field)
    ]
    if missing_fields:
        raise RuntimeError(
            "Missing Google service account settings: " + ", ".join(missing_fields)
        )

    credentials["type"] = "service_account"
    return credentials


def _fetch_from_ssm(fields):
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is required to load Google credentials from SSM"
        ) from exc

    parameter_names = [f"{SSM_PARAMETER_PREFIX}/{field}" for field in fields]
    client = boto3.client("ssm")
    response = client.get_parameters(
        Names=parameter_names,
        WithDecryption=True,
    )

    invalid = response.get("InvalidParameters", [])
    if invalid:
        raise RuntimeError("Missing SSM parameters: " + ", ".join(invalid))

    values_by_name = {
        parameter["Name"]: parameter["Value"]
        for parameter in response.get("Parameters", [])
    }
    return {
        field: values_by_name.get(f"{SSM_PARAMETER_PREFIX}/{field}", "")
        for field in fields
    }


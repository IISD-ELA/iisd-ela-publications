import json
import logging
from urllib.parse import parse_qs

from .publications import get_options, search_publications


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


def handler(event, context):
    try:
        return _dispatch(event)
    except Exception:
        LOGGER.exception("Unhandled publications API error")
        return _json_response(
            500,
            {"error": "The publications search service could not complete the request."},
        )


def _dispatch(event):
    path = event.get("rawPath") or event.get("path") or "/"
    method = (
        event.get("requestContext", {})
        .get("http", {})
        .get("method", event.get("httpMethod", "GET"))
    )

    if method == "OPTIONS":
        return _json_response(204, {})

    if path == "/health":
        return _json_response(200, {"ok": True})

    if path == "/api/options":
        params = _query_params(event)
        return _json_response(
            200,
            get_options(force_refresh=_truthy(_first(params.get("refresh")))),
        )

    if path == "/api/search":
        params = _query_params(event)
        return _json_response(
            200,
            search_publications(
                params,
                force_refresh=_truthy(_first(params.get("refresh"))),
            ),
        )

    return _json_response(404, {"error": "Not found"})


def _query_params(event):
    raw_query = event.get("rawQueryString")
    if raw_query is not None:
        return {
            key: [value for value in values if value != ""]
            for key, values in parse_qs(raw_query, keep_blank_values=True).items()
        }

    params = event.get("multiValueQueryStringParameters")
    if params:
        return params

    params = event.get("queryStringParameters") or {}
    return {key: [value] for key, value in params.items() if value is not None}


def _json_response(status_code, payload):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Cache-Control": "no-store",
        },
        "body": "" if status_code == 204 else json.dumps(payload),
    }


def _truthy(value):
    return str(value).lower() in ("1", "true", "yes")


def _first(values):
    if not values:
        return ""
    return values[0] if isinstance(values, list) else values

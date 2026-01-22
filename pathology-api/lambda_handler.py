import json
import logging
from functools import reduce
from typing import Any

from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pathology_api.fhir.r4.resources import Bundle
from pathology_api.handler import handle_request
from pydantic import ValidationError

_INVALID_PAYLOAD_MESSAGE = "Invalid payload provided."

logging.config.dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s - %(module)s: %(message)s",
            },
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["stdout"]},
    }
)

_logger = logging.getLogger(__name__)

app = APIGatewayHttpResolver()


def _with_default_headers(status_code: int, body: str) -> Response[str]:
    content_type = "application/fhir+json" if status_code == 200 else "text/plain"
    return Response(
        status_code=status_code,
        headers={"Content-Type": content_type},
        body=body,
    )


@app.get("/_status")
def status() -> Response[str]:
    _logger.debug("Status check endpoint called")
    return Response(status_code=200, body="OK", headers={"Content-Type": "text/plain"})


@app.post("/FHIR/R4/Bundle")
def post_result() -> Response[str]:
    _logger.debug("Post result endpoint called.")
    try:
        payload = app.current_event.json_body
    except json.JSONDecodeError as err:
        _logger.error("Error decoding JSON payload. error: %s", err)
        return _with_default_headers(status_code=400, body=_INVALID_PAYLOAD_MESSAGE)
    _logger.debug("Payload received: %s", payload)

    if not payload:
        _logger.error("No payload provided.")
        return _with_default_headers(status_code=400, body="No payload provided.")

    try:
        bundle = Bundle.model_validate(payload, by_alias=True)
    except ValidationError as err:
        _logger.error(
            "Error parsing payload. error: %s issues: %s",
            err,
            reduce(lambda acc, e: acc + "," + str(e), err.errors(), ""),
        )
        return _with_default_headers(status_code=400, body=_INVALID_PAYLOAD_MESSAGE)
    except TypeError as err:
        _logger.error("Error parsing payload. error: %s", err)
        return _with_default_headers(status_code=400, body=_INVALID_PAYLOAD_MESSAGE)

    try:
        response = handle_request(bundle)

        return _with_default_headers(
            status_code=200,
            body=response.model_dump_json(by_alias=True, exclude_none=True),
        )
    except ValueError as err:
        _logger.error("Error processing payload. error: %s", err)
        return _with_default_headers(
            status_code=400, body="Error processing provided bundle."
        )


def handler(data: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    return app.resolve(data, context)

import logging
from collections.abc import Callable
from typing import Any

from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pathology_api.fhir.r4.resources import Bundle
from pathology_api.handler import handle_request

_INVALID_PAYLOAD_MESSAGE = "Invalid payload provided."

_logger = logging.getLogger(__name__)

app = APIGatewayHttpResolver()

type _ExceptionHandler[T: Exception] = Callable[[T], Response[str]]


def _exception_handler[T: Exception](
    exception_type: type[T],
) -> Callable[[_ExceptionHandler[T]], _ExceptionHandler[T]]:
    """
    Exception handler decorator that registers a function as an exception handler with
    the created app whilst maintaining type information.
    """

    def decorator(func: _ExceptionHandler[T]) -> _ExceptionHandler[T]:
        def wrapper(exception: T) -> Response[str]:
            return func(exception)

        app.exception_handler(exception_type)(wrapper)
        return wrapper

    return decorator


def _with_default_headers(status_code: int, body: str) -> Response[str]:
    content_type = "application/fhir+json" if status_code == 200 else "text/plain"
    return Response(
        status_code=status_code,
        headers={"Content-Type": content_type},
        body=body,
    )


@_exception_handler(ValueError)
def handle_value_error(exception: ValueError) -> Response[str]:
    """Exception handler for handling ValueError exceptions."""

    # LOG014: False positive, we are within an exception handler here.
    _logger.warning("ValueError encountered: %s", exception, exc_info=True)  # noqa: LOG014
    return _with_default_headers(status_code=400, body="Invalid payload provided.")


@_exception_handler(Exception)
def handle_exception(exception: Exception) -> Response[str]:
    """General default exception handler for handling any unhandled exceptions."""
    _logger.exception("Unhandled Exception encountered: %s", exception)
    return _with_default_headers(
        status_code=500,
        body="An unexpected error has occurred. Please try again later.",
    )


@app.get("/_status")
def status() -> Response[str]:
    _logger.debug("Status check endpoint called")
    return Response(status_code=200, body="OK", headers={"Content-Type": "text/plain"})


@app.post("/FHIR/R4/Bundle")
def post_result() -> Response[str]:
    _logger.debug("Post result endpoint called.")
    payload = app.current_event.json_body
    _logger.debug("Payload received: %s", payload)

    if not payload:
        _logger.error("No payload provided.")
        return _with_default_headers(status_code=400, body="No payload provided.")

    bundle = Bundle.model_validate(payload, by_alias=True)

    response = handle_request(bundle)

    return _with_default_headers(
        status_code=200,
        body=response.model_dump_json(by_alias=True, exclude_none=True),
    )


def handler(data: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    return app.resolve(data, context)

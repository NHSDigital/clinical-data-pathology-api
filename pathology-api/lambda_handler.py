from typing import TypedDict

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.typing import LambdaContext
from pathology_api.fhir.r4.resources import Bundle
from pathology_api.handler import handle_request


class LambdaResponse[T](TypedDict):
    """
    A lambda response including a body with a generic type.
    Parameters:
        T: The type of the body.
        statusCode: The HTTP status code to return.
        headers: The HTTP headers to return.
        body: The body of the response.
    """

    statusCode: int
    headers: dict[str, str]
    body: T


def _with_default_headers[T](status_code: int, body: T) -> LambdaResponse[T]:
    content_type = "text/plain" if isinstance(body, str) else "application/fhir+json"
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": content_type},
        "body": body,
    }


def handler(
    event: APIGatewayProxyEventV2, _: LambdaContext
) -> LambdaResponse[Bundle | str]:
    print(f"Received event: {event}")

    payload = event.body
    if not payload:
        return _with_default_headers(status_code=400, body="No payload provided.")

    try:
        bundle = Bundle.model_validate_json(payload, by_alias=True)
    except ValueError:
        return _with_default_headers(status_code=400, body="Invalid payload provided.")

    try:
        return _with_default_headers(status_code=200, body=handle_request(bundle))
    except ValueError as err:
        return _with_default_headers(
            status_code=404, body=f"Error processing provided bundle. Error: {err}"
        )

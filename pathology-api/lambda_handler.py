from typing import Any, TypedDict

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2
from aws_lambda_powertools.utilities.typing import LambdaContext
from pathology_api.fhir.r4.resources import Bundle
from pathology_api.handler import handle_request
from pydantic import ValidationError


class LambdaResponse(TypedDict):
    """
    A lambda response including a body with a generic type.
    Parameters:
        statusCode: The HTTP status code to return.
        headers: The HTTP headers to return.
        body: The body of the response.
    """

    statusCode: int
    headers: dict[str, str]
    body: str


def _with_default_headers(status_code: int, body: str) -> LambdaResponse:
    content_type = "application/fhir+json"
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": content_type},
        "body": body,
    }


def handler(data: dict[str, Any], _: LambdaContext) -> LambdaResponse:
    print(f"Received event: {data}")
    event = APIGatewayProxyEventV2(data)

    payload = event.body
    if not payload:
        return _with_default_headers(status_code=400, body="No payload provided.")

    try:
        bundle = Bundle.model_validate_json(payload, by_alias=True)
    except ValidationError as err:
        print(f"Error parsing payload. error: {str(err)}")
        print("Errors:")
        for e in err.errors():
            print(e)
        return _with_default_headers(status_code=400, body="Invalid payload provided.")

    try:
        response = handle_request(bundle)

        return _with_default_headers(
            status_code=200,
            body=response.model_dump_json(by_alias=True),
        )
    except ValueError as err:
        return _with_default_headers(
            status_code=404, body=f"Error processing provided bundle. Error: {err}"
        )

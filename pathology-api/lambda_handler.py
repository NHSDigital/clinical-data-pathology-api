from typing import Any, TypedDict

from aws_lambda_powertools.event_handler import (
    APIGatewayHttpResolver,
    Response,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from pathology_api.fhir.r4.resources import Bundle
from pathology_api.handler import handle_request
from pydantic import ValidationError

app = APIGatewayHttpResolver()


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


def _with_default_headers(status_code: int, body: str) -> Response[str]:
    content_type = "application/fhir+json" if status_code == 200 else "text/plain"
    return Response(
        status_code=status_code,
        headers={"Content-Type": content_type},
        body=body,
    )


@app.get("/_status")
def status() -> Response[str]:
    return Response(status_code=200, body="OK")


@app.post("/FHIR/R4/Bundle")
def post_result() -> Response[str]:
    payload = app.current_event.json_body
    if not payload:
        return _with_default_headers(status_code=400, body="No payload provided.")

    try:
        bundle = Bundle.model_validate(payload, by_alias=True)
    except ValidationError as err:
        print(f"Error parsing payload. error: {str(err)}")
        print("Errors:")
        for e in err.errors():
            print(e)
        return _with_default_headers(status_code=400, body="Invalid payload provided.")
    except TypeError as err:
        print(f"Error parsing payload. error: {str(err)}")
        return _with_default_headers(status_code=400, body="Invalid payload provided.")

    try:
        response = handle_request(bundle)

        return _with_default_headers(
            status_code=200,
            body=response.model_dump_json(by_alias=True, exclude_none=True),
        )
    except ValueError as err:
        return _with_default_headers(
            status_code=400, body=f"Error processing provided bundle. Error: {err}"
        )


def handler(data: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    print(f"Received event: {data}")
    return app.resolve(data, context)

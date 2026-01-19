"""Step definitions for pathology API hello world feature."""

import requests
from pathology_api.fhir.r4.resources import Bundle, BundleType, Patient
from pytest_bdd import given, parsers, then, when

from tests.acceptance.conftest import ResponseContext
from tests.conftest import Client


@given("the API is running")
def step_api_is_running(client: Client) -> None:
    """Verify the API test client is available.

    Args:
        client: Test client from conftest.py
    """
    response = client.send("")
    assert response.text is not None
    assert response.status_code == 400


@when("I send a valid Bundle to the Pathology API")
def step_send_valid_bundle(client: Client, response_context: ResponseContext) -> None:
    """
    Send a valid Bundle to the API.

    Args:
        client: Test client
        response_context: Context to store the response
    """
    response_context.response = client.send(
        Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="patient",
                    resource=Patient.create(
                        identifier=Patient.PatientIdentifier.from_nhs_number(
                            "nhs_number"
                        )
                    ),
                )
            ],
        ).model_dump_json(by_alias=True, exclude_none=True)
    )


@when("I send an invalid Bundle to the Pathology API")
def step_send_invalid_bundle(client: Client, response_context: ResponseContext) -> None:
    """
    Send an invalid request to the API.

    Args:
        client: Test client
        response_context: Context to store the response
    """
    bundle = Bundle.empty(bundle_type="document").model_dump_json(
        by_alias=True, exclude_none=True
    )

    response_context.response = client.send(bundle)


# fmt: off
@then(parsers.cfparse("the response status code should be {expected_status:d}",extra_types={"expected_status": int}))  # noqa: E501 - BDD steps must be declared on a singular line.
# fmt: on
def step_check_status_code(
    response_context: ResponseContext, expected_status: int
) -> None:
    """Verify the response status code matches expected value.

    Args:
        context: Behave context containing the response
        expected_status: Expected HTTP status code
    """
    response = _validate_response_set(response_context)

    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, "
        f"got {response.status_code}"
    )


@then(parsers.cfparse('the response should contain "{expected_text}"'))
def step_check_response_contains(
    response_context: ResponseContext, expected_text: str
) -> None:
    """Verify the response contains the expected text.

    Args:
        context: Behave context containing the response
        expected_text: Text that should be in the response
    """
    response = _validate_response_set(response_context)

    assert expected_text in response.text, (
        f"Expected '{expected_text}' in response, got: {response.text}"
    )

@then(parsers.cfparse('the response should contain a valid "{expected_type}" Bundle'))
def step_check_response_contains_valid_bundle(
    response_context: ResponseContext,
    expected_type: BundleType
) -> None:
    """Verify the response contains a valid FHIR Bundle.

    Args:
        context: Behave context containing the response
    """
    response = _validate_response_set(response_context)

    response_data = response.json()
    bundle = Bundle.model_validate(response_data, by_alias=True)

    assert bundle.bundle_type == expected_type, (
        f"Expected bundle type '{expected_type}', got: '{bundle.bundle_type}'"
    )

    assert bundle.identifier is not None, "Bundle identifier is missing."
    assert bundle.identifier.system == "https://tools.ietf.org/html/rfc4122"
    assert bundle.identifier.value is not None, "Bundle identifier value is missing."

def _validate_response_set(response_context: ResponseContext) -> requests.Response:
    assert response_context.response is not None, "Response has not been set."
    return response_context.response

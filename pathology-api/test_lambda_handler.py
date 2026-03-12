from typing import Any
from unittest.mock import patch

import pydantic
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from lambda_handler import handler
from pathology_api.exception import ValidationError
from pathology_api.fhir.r4.elements import LogicalReference, PatientIdentifier
from pathology_api.fhir.r4.resources import Bundle, Composition, OperationOutcome
from pathology_api.request_context import get_correlation_id


class TestHandler:
    def _create_test_event(
        self,
        body: str | None = None,
        path_params: str | None = None,
        request_method: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return {
            "body": body,
            "headers": headers or {},
            "requestContext": {
                "http": {
                    "path": f"/{path_params}",
                    "method": request_method,
                },
                "requestId": "request-id",
                "stage": "$default",
            },
            "httpMethod": request_method,
            "rawPath": f"/{path_params}",
            "rawQueryString": "",
            "pathParameters": {"proxy": path_params},
        }

    def _parse_returned_issue(self, response: str) -> OperationOutcome.Issue:
        response_outcome = OperationOutcome.model_validate_json(response)

        assert len(response_outcome.issue) == 1
        returned_issue = response_outcome.issue[0]
        return returned_issue

    def test_create_test_result_success(self) -> None:
        bundle = Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="composition",
                    resource=Composition.create(
                        subject=LogicalReference(
                            PatientIdentifier.from_nhs_number("nhs_number")
                        )
                    ),
                )
            ],
        )
        event = self._create_test_event(
            body=bundle.model_dump_json(by_alias=True),
            path_params="FHIR/R4/Bundle",
            request_method="POST",
            headers={"nhsd-correlation-id": "test-correlation-id"},
        )
        context = LambdaContext()

        response = handler(event, context)

        assert response["statusCode"] == 200
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

        response_body = response["body"]
        assert isinstance(response_body, str)

        response_bundle = Bundle.model_validate_json(response_body, by_alias=True)
        assert response_bundle.bundle_type == bundle.bundle_type
        assert response_bundle.entries == bundle.entries

        # A UUID value so can only check its presence.
        assert response_bundle.id is not None

    def test_correlation_id_is_set_from_request_header(self) -> None:
        correlation_id = "test-correlation-id-abc-123"
        bundle = Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="composition",
                    resource=Composition.create(
                        subject=LogicalReference(
                            PatientIdentifier.from_nhs_number("nhs_number")
                        )
                    ),
                )
            ],
        )
        event = self._create_test_event(
            body=bundle.model_dump_json(by_alias=True),
            path_params="FHIR/R4/Bundle",
            request_method="POST",
            headers={"nhsd-correlation-id": correlation_id},
        )
        context = LambdaContext()

        handler(event, context)

        assert get_correlation_id() == correlation_id

    def test_missing_correlation_id_header_returns_400(self) -> None:
        bundle = Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="composition",
                    resource=Composition.create(
                        subject=LogicalReference(
                            PatientIdentifier.from_nhs_number("nhs_number")
                        )
                    ),
                )
            ],
        )
        event = self._create_test_event(
            body=bundle.model_dump_json(by_alias=True),
            path_params="FHIR/R4/Bundle",
            request_method="POST",
        )
        context = LambdaContext()

        response = handler(event, context)

        assert response["statusCode"] == 400
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

        returned_issue = self._parse_returned_issue(response["body"])
        assert returned_issue["severity"] == "error"
        assert returned_issue["code"] == "invalid"
        assert (
            returned_issue["diagnostics"]
            == "Missing required header: nhsd-correlation-id"
        )

    def test_create_test_result_no_payload(self) -> None:
        event = self._create_test_event(
            path_params="FHIR/R4/Bundle",
            request_method="POST",
            headers={"nhsd-correlation-id": "test-correlation-id"},
        )
        context = LambdaContext()

        response = handler(event, context)

        assert response["statusCode"] == 400
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

        returned_issue = self._parse_returned_issue(response["body"])

        assert returned_issue["severity"] == "error"
        assert returned_issue["code"] == "invalid"
        assert (
            returned_issue["diagnostics"]
            == "Resources must be provided as a bundle of type 'document'"
        )

    def test_create_test_result_empty_payload(self) -> None:
        event = self._create_test_event(
            body="{}",
            path_params="FHIR/R4/Bundle",
            request_method="POST",
            headers={"nhsd-correlation-id": "test-correlation-id"},
        )
        context = LambdaContext()

        response = handler(event, context)

        assert response["statusCode"] == 400
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

        returned_issue = self._parse_returned_issue(response["body"])

        assert returned_issue["severity"] == "error"
        assert returned_issue["code"] == "invalid"
        assert (
            returned_issue["diagnostics"]
            == "('resourceType',) - Field required \n('type',) - Field required \n"
        )

    def test_create_test_result_invalid_json(self) -> None:
        event = self._create_test_event(
            body="invalid json",
            path_params="FHIR/R4/Bundle",
            request_method="POST",
            headers={"nhsd-correlation-id": "test-correlation-id"},
        )
        context = LambdaContext()

        response = handler(event, context)

        assert response["statusCode"] == 400
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

        returned_issue = self._parse_returned_issue(response["body"])
        assert returned_issue["severity"] == "error"
        assert returned_issue["code"] == "invalid"
        assert returned_issue["diagnostics"] == "Invalid payload provided."

    @pytest.mark.parametrize(
        ("error", "expected_issue", "expected_status_code"),
        [
            pytest.param(
                ValidationError("Test processing error"),
                OperationOutcome.Issue(
                    severity="error",
                    code="invalid",
                    diagnostics="Test processing error",
                ),
                400,
                id="ValidationError",
            ),
            pytest.param(
                Exception("Test general error"),
                {
                    "severity": "fatal",
                    "code": "exception",
                    "diagnostics": "An unexpected error has occurred. "
                    "Please try again later.",
                },
                500,
                id="Unexpected exception",
            ),
        ],
    )
    def test_create_test_result_processing_error(
        self,
        error: type[Exception],
        expected_issue: OperationOutcome.Issue,
        expected_status_code: int,
    ) -> None:
        bundle = Bundle.empty(bundle_type="document")
        event = self._create_test_event(
            body=bundle.model_dump_json(by_alias=True),
            path_params="FHIR/R4/Bundle",
            request_method="POST",
            headers={"nhsd-correlation-id": "test-correlation-id"},
        )
        context = LambdaContext()

        with patch("lambda_handler.handle_request", side_effect=error):
            response = handler(event, context)

        assert response["statusCode"] == expected_status_code
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

        returned_issue = self._parse_returned_issue(response["body"])
        assert returned_issue == expected_issue

    @pytest.mark.parametrize(
        ("expected_error", "expected_diagnostic"),
        [
            pytest.param(
                ValidationError("Test validation error"),
                "Test validation error",
                id="ValidationError",
            ),
            pytest.param(
                pydantic.ValidationError.from_exception_data(
                    "Test validation error",
                    [{"type": "missing", "loc": ("field",), "input": "is invalid"}],
                ),
                "('field',) - Field required \n",
                id="Pydantic ValidationError",
            ),
        ],
    )
    def test_create_test_result_model_validate_error(
        self, expected_error: Exception, expected_diagnostic: str
    ) -> None:
        bundle = Bundle.empty(bundle_type="document")
        event = self._create_test_event(
            body=bundle.model_dump_json(by_alias=True),
            path_params="FHIR/R4/Bundle",
            request_method="POST",
            headers={"nhsd-correlation-id": "test-correlation-id"},
        )
        context = LambdaContext()

        with patch(
            "pathology_api.fhir.r4.resources.Bundle.model_validate",
            side_effect=expected_error,
        ):
            response = handler(event, context)

            assert response["statusCode"] == 400
            assert response["headers"] == {"Content-Type": "application/fhir+json"}

            returned_issue = self._parse_returned_issue(response["body"])
            assert returned_issue["severity"] == "error"
            assert returned_issue["code"] == "invalid"
            assert returned_issue["diagnostics"] == expected_diagnostic

    def test_status_success(self) -> None:
        event = self._create_test_event(path_params="_status", request_method="GET")
        context = LambdaContext()

        response = handler(event, context)

        assert response["statusCode"] == 200
        assert response["body"] == "OK"
        assert response["headers"] == {"Content-Type": "text/plain"}

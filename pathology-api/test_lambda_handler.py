import json
from typing import Any
from unittest.mock import patch

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from lambda_handler import handler
from pathology_api.fhir.r4.resources import Bundle, Patient
from pydantic import ValidationError


class TestHandler:
    """Unit tests for the Lambda handler function."""

    def _create_test_event(
        self,
        body: str | None = None,
        path_params: str | None = None,
        request_method: str | None = None,
    ) -> dict[str, Any]:
        return {
            "body": body,
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

    def test_create_test_result_success(self) -> None:
        """Test create test result returns 200 with processed bundle for valid input."""
        bundle = Bundle.create(
            type="transaction",
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
        )
        event = self._create_test_event(
            body=bundle.model_dump_json(by_alias=True),
            path_params="FHIR/R4/Bundle",
            request_method="POST",
        )
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

        response_body = response["body"]
        assert isinstance(response_body, str)

        response_bundle = Bundle.model_validate_json(response_body, by_alias=True)
        assert response_bundle.bundle_type == bundle.bundle_type
        assert response_bundle.entries == bundle.entries

        assert response_bundle.identifier is not None
        assert (
            response_bundle.identifier.system == "https://tools.ietf.org/html/rfc4122"
        )
        # A UUID value so can only check its presence.
        assert response_bundle.identifier.value is not None

    def test_create_test_result_no_payload(self) -> None:
        """Test create test result returns 400 when no payload is provided."""
        # Arrange
        event = self._create_test_event(
            path_params="FHIR/R4/Bundle", request_method="POST"
        )
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "No payload provided."
        assert response["headers"] == {"Content-Type": "text/plain"}

    def test_create_test_result_empty_payload(self) -> None:
        """Test create test result returns 400 when empty payload is provided."""
        # Arrange
        event = self._create_test_event(
            body="{}", path_params="FHIR/R4/Bundle", request_method="POST"
        )
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "No payload provided."
        assert response["headers"] == {"Content-Type": "text/plain"}

    def test_create_test_result_invalid_json(self) -> None:
        """Test create test result handles invalid JSON payload."""
        # Arrange
        event = self._create_test_event(
            body="invalid json", path_params="FHIR/R4/Bundle", request_method="POST"
        )
        context = LambdaContext()

        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "Invalid payload provided."
        assert response["headers"] == {"Content-Type": "text/plain"}

    def test_create_test_result_processing_error(self) -> None:
        """Test create test result returns 400 when handle_request raises ValueError."""
        # Arrange
        bundle = Bundle.empty(bundle_type="transaction")
        event = self._create_test_event(
            body=bundle.model_dump_json(by_alias=True),
            path_params="FHIR/R4/Bundle",
            request_method="POST",
        )
        context = LambdaContext()
        error_message = "Test processing error"

        expected_error = ValueError(error_message)
        with patch("lambda_handler.handle_request", side_effect=expected_error):
            # Act
            response = handler(event, context)

            # Assert
            assert response["statusCode"] == 400
            assert response["body"] == "Error processing provided bundle."
            assert response["headers"] == {"Content-Type": "text/plain"}

    @pytest.mark.parametrize(
        "expected_error",
        [
            pytest.param(
                TypeError("Test type error"),
                id="TypeError",
            ),
            pytest.param(
                ValidationError("Test validation error", []),
                id="ValidationError",
            ),
        ],
    )
    def test_create_test_result_parse_json_error(
        self, expected_error: Exception
    ) -> None:
        """Test create test result returns 400 when handle_request raises TypeError."""
        # Arrange
        bundle = Bundle.empty(bundle_type="transaction")
        event = self._create_test_event(
            body=bundle.model_dump_json(by_alias=True),
            path_params="FHIR/R4/Bundle",
            request_method="POST",
        )
        context = LambdaContext()

        with patch(
            "pathology_api.fhir.r4.resources.Bundle.model_validate",
            side_effect=expected_error,
        ):
            # Act
            response = handler(event, context)

            # Assert
            assert response["statusCode"] == 400
            assert response["body"] == "Invalid payload provided."
            assert response["headers"] == {"Content-Type": "text/plain"}

    def test_status_success(self) -> None:
        """Test status function returns 200 OK."""
        # Arrange
        event = self._create_test_event(path_params="_status", request_method="GET")
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        assert response["body"] == "OK"
        assert response["headers"] == {"Content-Type": "text/plain"}

    @pytest.mark.parametrize(
        ("request_method", "request_parameter"),
        [
            pytest.param("GET", "unknown_path", id="Unknown path"),
            pytest.param("GET", "FHIR/R4/Bundle", id="Unknown GET method"),
            pytest.param("POST", "_status", id="Unknown POST method"),
        ],
    )
    def test_invalid_request(self, request_method: str, request_parameter: str) -> None:
        """Test that unknown request methods and paths return a 404."""
        # Arrange
        event = self._create_test_event(
            path_params=request_parameter, request_method=request_method
        )
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 404
        assert json.loads(response["body"]) == {
            "statusCode": 404,
            "message": "Not found",
        }
        assert response["headers"] == {"Content-Type": "application/json"}

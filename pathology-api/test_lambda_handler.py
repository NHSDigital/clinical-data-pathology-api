from typing import Any
from unittest.mock import patch

from aws_lambda_powertools.utilities.typing import LambdaContext
from lambda_handler import handler
from pathology_api.fhir.r4.resources import Bundle, Patient


class TestHandler:
    """Unit tests for the Lambda handler function."""

    def test_handler_success(self) -> None:
        """Test handler returns 200 with processed bundle for valid input."""
        bundle = Bundle(
            type="transaction",
            entry=[
                Bundle.Entry(
                    fullUrl="patient",
                    resource=Patient(
                        identifier=Patient.PatientIdentifier.from_nhs_number(
                            "nhs_number"
                        )
                    ),
                )
            ],
        )
        event = {"body": bundle.model_dump_json(by_alias=True)}
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

    def test_handler_no_patient_resource(self) -> None:
        """
        Test handler returns 400 when provided bundle doesn't include a patient
        resource.
        """
        bundle = Bundle(
            type="transaction",
            entry=[],
        )
        event = {"body": bundle.model_dump_json(by_alias=True)}
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["headers"] == {"Content-Type": "application/fhir+json"}
        assert (
            response["body"] == "Error processing provided bundle. "
            "Error: Test Result Bundle must reference at least one Patient resource."
        )

    def test_handler_multiple_patient_resources(self) -> None:
        """
        Test handler returns 400 when provided bundle includes multiple patient
        resources.
        """
        bundle = Bundle(
            type="transaction",
            entry=[
                Bundle.Entry(
                    fullUrl="patient1",
                    resource=Patient(
                        identifier=Patient.PatientIdentifier.from_nhs_number(
                            "nhs_number1"
                        )
                    ),
                ),
                Bundle.Entry(
                    fullUrl="patient2",
                    resource=Patient(
                        identifier=Patient.PatientIdentifier.from_nhs_number(
                            "nhs_number2"
                        )
                    ),
                ),
            ],
        )
        event = {"body": bundle.model_dump_json(by_alias=True)}
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["headers"] == {"Content-Type": "application/fhir+json"}
        assert (
            response["body"] == "Error processing provided bundle. "
            "Error: Test Result Bundle must not reference more than one Patient "
            "resource."
        )

    def test_handler_no_payload(self) -> None:
        """Test handler returns 400 when no payload is provided."""
        # Arrange
        event = {"body": None}
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "No payload provided."
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

    def test_handler_empty_payload(self) -> None:
        """Test handler returns 400 when empty payload is provided."""
        # Arrange
        event: dict[str, Any] = {}
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "No payload provided."
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

    def test_handler_invalid_json(self) -> None:
        """Test handler handles invalid JSON payload."""
        # Arrange
        event = {"body": "invalid json"}
        context = LambdaContext()

        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "Invalid payload provided."
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

    def test_handler_processing_error(self) -> None:
        """Test handler returns 404 when handle_request raises ValueError."""
        # Arrange
        bundle = Bundle(
            type="transaction",
        )
        event = {"body": bundle.model_dump_json(by_alias=True)}
        context = LambdaContext()
        error_message = "Test processing error"

        with patch(
            "lambda_handler.handle_request", side_effect=ValueError(error_message)
        ):
            # Act
            response = handler(event, context)

            # Assert
            assert response["statusCode"] == 400
            assert (
                response["body"]
                == f"Error processing provided bundle. Error: {error_message}"
            )
            assert response["headers"] == {"Content-Type": "application/fhir+json"}

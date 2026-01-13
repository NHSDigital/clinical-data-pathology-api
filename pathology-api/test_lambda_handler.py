from unittest.mock import MagicMock, patch

from aws_lambda_powertools.utilities.typing import LambdaContext
from lambda_handler import handler
from pathology_api.fhir.r4.resources import Bundle, Patient


class TestHandler:
    """Unit tests for the Lambda handler function."""

    @patch("aws_lambda_powertools.utilities.data_classes.APIGatewayProxyEventV2")
    def test_handler_success(self, APIGatewayProxyEventV2: type[MagicMock]) -> None:
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
        event = APIGatewayProxyEventV2()
        event.body = bundle.model_dump_json(by_alias=True)
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        assert response["headers"] == {"Content-Type": "application/fhir+json"}

        response_body = response["body"]
        assert isinstance(response_body, Bundle)
        assert response_body.bundle_type == bundle.bundle_type
        assert response_body.entries == bundle.entries

        assert response_body.identifier is not None
        assert response_body.identifier.system == "https://tools.ietf.org/html/rfc4122"
        # A UUID value so can only check its presence.
        assert response_body.identifier.value is not None

    @patch("aws_lambda_powertools.utilities.data_classes.APIGatewayProxyEventV2")
    def test_handler_no_payload(self, APIGatewayProxyEventV2: type[MagicMock]) -> None:
        """Test handler returns 400 when no payload is provided."""
        # Arrange
        event = APIGatewayProxyEventV2()
        event.body = None
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "No payload provided."
        assert response["headers"] == {"Content-Type": "text/plain"}

    @patch("aws_lambda_powertools.utilities.data_classes.APIGatewayProxyEventV2")
    def test_handler_empty_payload(
        self, APIGatewayProxyEventV2: type[MagicMock]
    ) -> None:
        """Test handler returns 400 when empty payload is provided."""
        # Arrange
        event = APIGatewayProxyEventV2()
        event.body = ""
        context = LambdaContext()

        # Act
        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "No payload provided."
        assert response["headers"] == {"Content-Type": "text/plain"}

    @patch("aws_lambda_powertools.utilities.data_classes.APIGatewayProxyEventV2")
    def test_handler_invalid_json(
        self, APIGatewayProxyEventV2: type[MagicMock]
    ) -> None:
        """Test handler handles invalid JSON payload."""
        # Arrange
        event = APIGatewayProxyEventV2()
        event.body = "invalid json"
        context = LambdaContext()

        response = handler(event, context)

        # Assert
        assert response["statusCode"] == 400
        assert response["body"] == "Invalid payload provided."
        assert response["headers"] == {"Content-Type": "text/plain"}

    @patch("aws_lambda_powertools.utilities.data_classes.APIGatewayProxyEventV2")
    def test_handler_processing_error(
        self, APIGatewayProxyEventV2: type[MagicMock]
    ) -> None:
        """Test handler returns 404 when handle_request raises ValueError."""
        # Arrange
        bundle = Bundle(
            type="transaction",
        )
        event = APIGatewayProxyEventV2()
        event.body = bundle.model_dump_json(by_alias=True)
        context = LambdaContext()
        error_message = "Test processing error"

        with patch(
            "lambda_handler.handle_request", side_effect=ValueError(error_message)
        ):
            # Act
            response = handler(event, context)

            # Assert
            assert response["statusCode"] == 404
            assert (
                response["body"]
                == f"Error processing provided bundle. Error: {error_message}"
            )
            assert response["headers"] == {"Content-Type": "text/plain"}

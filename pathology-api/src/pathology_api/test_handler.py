from pathology_api.fhir.r4.resources import Bundle, Patient
from pathology_api.handler import handle_request


class TestHandleRequest:
    """Test suite for the handle_request function."""

    def test_handle_request(self) -> None:
        """Test that handle_request processes a valid bundle correctly."""
        # Arrange
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

        # Act
        result_bundle = handle_request(bundle)

        # Assert
        assert result_bundle is not None
        assert result_bundle.identifier is not None
        assert result_bundle.bundle_type == bundle.bundle_type
        assert result_bundle.entries == bundle.entries

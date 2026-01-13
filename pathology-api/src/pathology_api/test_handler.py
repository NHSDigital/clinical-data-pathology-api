import pytest

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
        result_identifier = result_bundle.identifier
        assert result_identifier.system == "https://tools.ietf.org/html/rfc4122"

        assert result_bundle.bundle_type == bundle.bundle_type
        assert result_bundle.entries == bundle.entries

    def test_handle_request_raises_error_when_no_patient_resource(self) -> None:
        """
        Test that handle_request raises ValueError when bundle has no Patient resource.
        """
        # Arrange
        bundle = Bundle(
            type="transaction",
            entry=[],
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Test Result Bundle must reference at least one Patient resource.",
        ):
            handle_request(bundle)

    def test_handle_request_raises_error_when_multiple_patient_resources(
        self,
    ) -> None:
        """
        Test that handle_request raises ValueError when bundle has multiple Patient
        resources.
        """
        # Arrange
        bundle = Bundle(
            type="transaction",
            entry=[
                Bundle.Entry(
                    fullUrl="patient1",
                    resource=Patient(
                        identifier=Patient.PatientIdentifier.from_nhs_number(
                            "nhs_number_1"
                        )
                    ),
                ),
                Bundle.Entry(
                    fullUrl="patient2",
                    resource=Patient(
                        identifier=Patient.PatientIdentifier.from_nhs_number(
                            "nhs_number_2"
                        )
                    ),
                ),
            ],
        )

        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Test Result Bundle must not reference more than one Patient "
            "resource.",
        ):
            handle_request(bundle)

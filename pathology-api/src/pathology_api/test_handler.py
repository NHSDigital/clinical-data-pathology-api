import datetime

import pytest

from pathology_api.fhir.r4.resources import Bundle, Patient
from pathology_api.handler import handle_request


class TestHandleRequest:
    """Test suite for the handle_request function."""

    def test_handle_request(self) -> None:
        """Test that handle_request processes a valid bundle correctly."""
        # Arrange
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

        # Act
        before_call = datetime.datetime.now(tz=datetime.timezone.utc)
        result_bundle = handle_request(bundle)
        after_call = datetime.datetime.now(tz=datetime.timezone.utc)

        # Assert
        assert result_bundle is not None

        assert result_bundle.identifier is not None
        result_identifier = result_bundle.identifier
        assert result_identifier.system == "https://tools.ietf.org/html/rfc4122"

        assert result_bundle.bundle_type == bundle.bundle_type
        assert result_bundle.entries == bundle.entries

        # Verify last_updated field
        assert result_bundle.meta is not None
        created_meta = result_bundle.meta

        assert created_meta.last_updated is not None
        assert before_call <= created_meta.last_updated
        assert created_meta.last_updated <= after_call

        assert created_meta.version_id is None

    def test_handle_request_raises_error_when_no_patient_resource(self) -> None:
        """
        Test that handle_request raises ValueError when bundle has no Patient resource.
        """
        # Arrange
        bundle = Bundle.create(
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
        patient = Patient.create(
            identifier=Patient.PatientIdentifier.from_nhs_number("nhs_number_1")
        )

        bundle = Bundle.create(
            type="transaction",
            entry=[
                Bundle.Entry(
                    fullUrl="patient1",
                    resource=patient,
                ),
                Bundle.Entry(
                    fullUrl="patient2",
                    resource=patient,
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

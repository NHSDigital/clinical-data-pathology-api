import pytest

from .resources import Bundle, Patient


class TestBundle:
    def test_create(self) -> None:
        """Test creating a Bundle resource."""
        expected_entry = Bundle.Entry(
            fullUrl="http://example.com/resource1",
            resource=Patient(
                identifier=Patient.PatientIdentifier.from_nhs_number("nhs_number")
            ),
        )

        bundle = Bundle(
            type="document",
            entry=[expected_entry],
        )

        assert bundle.bundle_type == "document"
        assert bundle.identifier is None
        assert bundle.entries == [expected_entry]

    def test_create_without_entries(self) -> None:
        """Test creating a Bundle resource without entries."""
        bundle = Bundle.empty("document")

        assert bundle.bundle_type == "document"
        assert bundle.identifier is None
        assert bundle.entries is None

    def test_find_resources(self) -> None:
        expected_resource = Patient(
            identifier=Patient.PatientIdentifier.from_nhs_number("nhs_number")
        )

        bundle = Bundle(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="http://example.com/resource1",
                    resource=expected_resource,
                ),
            ],
        )

        result = bundle.find_resources(Patient)
        assert result == [expected_resource]

    @pytest.mark.parametrize(
        "bundle",
        [
            pytest.param(Bundle.empty("document"), id="Bundle has no entries at all"),
            pytest.param(
                Bundle(type="document", entry=[]), id="Bundle has an empty entries list"
            ),
            pytest.param(
                Bundle(
                    type="document",
                    entry=[
                        Bundle.Entry(
                            fullUrl="http://example.com/resource1",
                            resource=Bundle.empty("document"),
                        ),
                    ],
                ),
                id="different_resource_type",
            ),
        ],
    )
    def test_find_resources_returns_empty_list(self, bundle: Bundle) -> None:
        """
        Test that find_resources returns an empty list when no matching resources exist.
        """
        result = bundle.find_resources(Patient)
        assert result == []


class TestPatient:
    def test_create(self) -> None:
        """Test creating a Patient resource."""
        nhs_number = "1234567890"

        expected_identifier = Patient.PatientIdentifier.from_nhs_number(nhs_number)
        patient = Patient(identifier=expected_identifier)

        assert patient.identifier == expected_identifier


class TestPatientIdentifier:
    def test_create_from_nhs_number(self) -> None:
        """Test creating a PatientIdentifier from an NHS number."""
        nhs_number = "1234567890"
        identifier = Patient.PatientIdentifier.from_nhs_number(nhs_number)

        assert identifier.system == "https://fhir.nhs.uk/Id/nhs-number"
        assert identifier.value == nhs_number

import datetime
import uuid

import pydantic
import pytest
from pydantic import BaseModel

from pathology_api.exception import ValidationError

from .elements import (
    Identifier,
    LogicalReference,
    Meta,
    PatientIdentifier,
    UUIDIdentifier,
)


class TestMeta:
    def test_create(self) -> None:
        meta = Meta(
            version_id="1",
            last_updated=datetime.datetime.fromisoformat("2023-10-01T12:00:00Z"),
        )
        assert meta.version_id == "1"
        assert meta.last_updated == datetime.datetime.fromisoformat(
            "2023-10-01T12:00:00Z"
        )

    def test_create_without_last_updated(self) -> None:
        meta = Meta(version_id="2")

        assert meta.version_id == "2"
        assert meta.last_updated is None

    def test_create_without_version(self) -> None:
        meta = Meta(
            last_updated=datetime.datetime.fromisoformat("2023-10-01T12:00:00Z")
        )

        assert meta.version_id is None
        assert meta.last_updated == datetime.datetime.fromisoformat(
            "2023-10-01T12:00:00Z"
        )

    def test_with_last_updated(self) -> None:
        last_updated = datetime.datetime.fromisoformat("2023-10-01T12:00:00Z")
        meta = Meta.with_last_updated(last_updated)

        assert meta.last_updated == last_updated
        assert meta.version_id is None

    def test_with_last_updated_defaults_to_now(self) -> None:
        before_create = datetime.datetime.now(tz=datetime.timezone.utc)
        meta = Meta.with_last_updated(None)
        after_create = datetime.datetime.now(tz=datetime.timezone.utc)

        assert meta.last_updated is not None
        assert meta.version_id is None

        assert before_create <= meta.last_updated
        assert meta.last_updated <= after_create


class TestUUIDIdentifier:
    def test_create_with_value(self) -> None:
        expected_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        identifier = UUIDIdentifier(value=expected_uuid)

        assert identifier.system == "https://tools.ietf.org/html/rfc4122"
        assert identifier.value == str(expected_uuid)

    def test_create_without_value(self) -> None:
        identifier = UUIDIdentifier()

        assert identifier.system == "https://tools.ietf.org/html/rfc4122"
        # Validates that value is a valid UUID v4
        parsed_uuid = uuid.UUID(identifier.value)
        assert parsed_uuid.version == 4


class _TestContainer(BaseModel):
    identifier: "IdentifierStub"

    class IdentifierStub(Identifier, expected_system="expected-system"):
        pass


class TestIdentifier:
    def test_invalid_system(self) -> None:
        with pytest.raises(
            ValidationError,
            match="Identifier system 'invalid-system' does not match expected "
            "system 'expected-system'.",
        ):
            _TestContainer.model_validate(
                {"identifier": {"system": "invalid-system", "value": "some-value"}}
            )

    def test_without_value(self) -> None:
        with pytest.raises(
            pydantic.ValidationError,
            match="1 validation error for _TestContainer\nidentifier.value\n  "
            "Field required [type=missing, input_value={'system': 'expected-system'},"
            " input_type=dict]*",
        ):
            _TestContainer.model_validate({"identifier": {"system": "expected-system"}})


class TestPatientIdentifier:
    def test_create_from_nhs_number(self) -> None:
        """Test creating a PatientIdentifier from an NHS number."""
        nhs_number = "1234567890"
        identifier = PatientIdentifier.from_nhs_number(nhs_number)

        assert identifier.system == "https://fhir.nhs.uk/Id/nhs-number"
        assert identifier.value == nhs_number


class TestLogicalReference:
    class _TestContainer(BaseModel):
        reference: LogicalReference[PatientIdentifier]

    def test_create_with_patient_identifier(self) -> None:
        nhs_number = "nhs_number"
        patient_id = PatientIdentifier.from_nhs_number(nhs_number)

        reference = LogicalReference(identifier=patient_id)

        assert reference.identifier == patient_id
        assert reference.identifier.system == "https://fhir.nhs.uk/Id/nhs-number"
        assert reference.identifier.value == nhs_number

    def test_serialization(self) -> None:
        nhs_number = "nhs_number"
        patient_id = PatientIdentifier.from_nhs_number(nhs_number)
        reference = LogicalReference(identifier=patient_id)

        container = self._TestContainer(reference=reference)
        serialized = container.model_dump(by_alias=True)

        expected = {
            "reference": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "nhs_number",
                }
            }
        }
        assert serialized == expected

    def test_deserialization(self) -> None:
        data = {
            "reference": {
                "identifier": {
                    "system": "https://fhir.nhs.uk/Id/nhs-number",
                    "value": "nhs_number",
                }
            }
        }

        container = self._TestContainer.model_validate(data)

        created_identifier = container.reference.identifier
        assert isinstance(created_identifier, PatientIdentifier)
        assert created_identifier.system == "https://fhir.nhs.uk/Id/nhs-number"
        assert created_identifier.value == "nhs_number"

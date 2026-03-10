import datetime
import os

import pytest

os.environ["CLIENT_TIMEOUT"] = "1s"
os.environ["APIM_TOKEN_URL"] = "apim_url"  # noqa S105 - dummy value
os.environ["APIM_PRIVATE_KEY_NAME"] = "apim_private_key_name"
os.environ["APIM_API_KEY_NAME"] = "apim_api_key_name"
os.environ["APIM_TOKEN_EXPIRY_THRESHOLD"] = "1s"  # noqa S105 - dummy value
os.environ["APIM_KEY_ID"] = "apim_key"
os.environ["PDM_BUNDLE_URL"] = "pdm_bundle_url"

from pathology_api.exception import ValidationError
from pathology_api.fhir.r4.elements import (
    LogicalReference,
    PatientIdentifier,
)
from pathology_api.fhir.r4.resources import Bundle, Composition
from pathology_api.handler import handle_request


class TestHandleRequest:
    def test_handle_request(self) -> None:
        # Arrange
        bundle = Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="patient",
                    resource=Composition.create(
                        subject=LogicalReference(
                            PatientIdentifier.from_nhs_number("nhs_number")
                        )
                    ),
                )
            ],
        )

        before_call = datetime.datetime.now(tz=datetime.timezone.utc)
        result_bundle = handle_request(bundle)
        after_call = datetime.datetime.now(tz=datetime.timezone.utc)

        assert result_bundle is not None

        assert result_bundle.id is not None

        assert result_bundle.bundle_type == bundle.bundle_type
        assert result_bundle.entries == bundle.entries

        # Verify last_updated field
        assert result_bundle.meta is not None
        created_meta = result_bundle.meta

        assert created_meta.last_updated is not None
        assert before_call <= created_meta.last_updated
        assert created_meta.last_updated <= after_call

        assert created_meta.version_id is None

    def test_handle_request_raises_error_when_no_composition_resource(self) -> None:
        bundle = Bundle.create(
            type="document",
            entry=[],
        )

        with pytest.raises(
            ValidationError,
            match="Document must include a single Composition resource",
        ):
            handle_request(bundle)

    def test_handle_request_raises_error_when_multiple_composition_resources(
        self,
    ) -> None:
        composition = Composition.create(
            subject=LogicalReference(PatientIdentifier.from_nhs_number("nhs_number_1"))
        )

        bundle = Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="composition1",
                    resource=composition,
                ),
                Bundle.Entry(
                    fullUrl="composition2",
                    resource=composition,
                ),
            ],
        )

        with pytest.raises(
            ValidationError,
            match="Document must include a single Composition resource",
        ):
            handle_request(bundle)

    @pytest.mark.parametrize(
        ("composition", "expected_error_message"),
        [
            pytest.param(
                Composition.create(subject=None),
                "Composition does not define a valid subject identifier",
                id="No subject",
            )
        ],
    )
    def test_handle_request_raises_error_when_invalid_composition(
        self, composition: Composition, expected_error_message: str
    ) -> None:
        bundle = Bundle.create(
            type="document",
            entry=[
                Bundle.Entry(
                    fullUrl="composition",
                    resource=composition,
                )
            ],
        )

        with pytest.raises(
            ValidationError,
            match=expected_error_message,
        ):
            handle_request(bundle)

    def test_handle_request_raises_error_when_bundle_includes_id(
        self,
    ) -> None:
        composition = Composition.create(
            subject=LogicalReference(PatientIdentifier.from_nhs_number("nhs_number_1"))
        )

        bundle = Bundle.create(
            id="id",
            type="document",
            entry=[Bundle.Entry(fullUrl="composition1", resource=composition)],
        )

        with pytest.raises(
            ValidationError,
            match="Bundles cannot be defined with an existing ID",
        ):
            handle_request(bundle)

    def test_handle_request_raises_error_when_bundle_not_document_type(
        self,
    ) -> None:
        composition = Composition.create(
            subject=LogicalReference(PatientIdentifier.from_nhs_number("nhs_number_1"))
        )

        bundle = Bundle.create(
            type="collection",
            entry=[Bundle.Entry(fullUrl="composition1", resource=composition)],
        )

        with pytest.raises(
            ValidationError,
            match="Resource must be a bundle of type 'document'",
        ):
            handle_request(bundle)

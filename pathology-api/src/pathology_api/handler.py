import logging
from collections.abc import Callable

from pathology_api.fhir.r4.elements import Meta, UUIDIdentifier
from pathology_api.fhir.r4.resources import Bundle, Patient

_logger = logging.getLogger(__name__)


def _ensure_test_result_references_patient(bundle: Bundle) -> None:
    patient_references = [
        patient.identifier for patient in bundle.find_resources(t=Patient)
    ]
    if not patient_references:
        raise ValueError(
            "Test Result Bundle must reference at least one Patient resource."
        )

    _logger.debug("Bundle.entries %s", bundle.entries)
    _logger.debug("Patient references found: %s", patient_references)

    if len(patient_references) > 1:
        raise ValueError(
            "Test Result Bundle must not reference more than one Patient resource."
        )


type ValidationFunction = Callable[[Bundle], None]
_validation_functions: list[ValidationFunction] = [
    _ensure_test_result_references_patient,
]


def handle_request(bundle: Bundle) -> Bundle:
    if bundle.identifier:
        raise ValueError("Bundle with identifier is not allowed.")

    for validate_function in _validation_functions:
        validate_function(bundle)

    _logger.debug("Bundle entries: %s", bundle.entries)
    return_bundle = Bundle.create(
        meta=Meta.with_last_updated(),
        identifier=UUIDIdentifier(),
        type=bundle.bundle_type,
        entry=bundle.entries,
    )
    _logger.debug("Return bundle: %s", return_bundle)

    return return_bundle

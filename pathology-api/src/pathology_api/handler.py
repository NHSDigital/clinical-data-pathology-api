from collections.abc import Callable

from pathology_api.fhir.r4.elements import Meta, UUIDIdentifier
from pathology_api.fhir.r4.resources import Bundle, Patient


def _ensure_test_result_references_patient(bundle: Bundle) -> None:
    patient_references = {
        patient.identifier for patient in bundle.find_resources(t=Patient)
    }
    if not patient_references:
        raise ValueError(
            "Test Result Bundle must reference at least one Patient resource."
        )

    if len(patient_references) > 1:
        raise ValueError(
            "Test Result Bundle must not reference more than one Patient resource."
        )


type ValidationFunction = Callable[[Bundle], None]
_VALIDATION_FUNCTIONS: list[ValidationFunction] = [
    _ensure_test_result_references_patient,
]


def handle_request(bundle: Bundle) -> Bundle:
    if bundle.identifier:
        raise ValueError("Bundle with identifier is not allowed.")

    for validate_function in _VALIDATION_FUNCTIONS:
        validate_function(bundle)

    print(f"Bundle entries: {bundle.entries}")
    return_bundle = Bundle(
        meta=Meta.with_last_updated(),
        identifier=UUIDIdentifier(),
        type=bundle.bundle_type,
        entry=bundle.entries,
    )
    print(f"Return bundle: {return_bundle}")

    return return_bundle

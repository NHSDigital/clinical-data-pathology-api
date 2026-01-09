from collections.abc import Callable

from pathology_api.fhir.r4.elements import UUIDIdentifier
from pathology_api.fhir.r4.resources import Bundle, Patient


def _ensure_test_result_references_patient(bundle: Bundle) -> None:
    patient_references = {
        patient.identifier.value for patient in bundle.find_resources(t=Patient)
    }
    if not patient_references:
        raise ValueError(
            "TestResultBundle must reference at least one Patient resource."
        )

    if len(patient_references) > 1:
        raise ValueError(
            "TestResultBundle must not reference more than one Patient resource."
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

    return_bundle = Bundle(
        identifier=UUIDIdentifier(),
        type=bundle.bundle_type,
        entries=bundle.entries,
    )

    return return_bundle

import uuid
from collections.abc import Callable

from pathology_api.exception import ValidationError
from pathology_api.fhir.r4.elements import Meta
from pathology_api.fhir.r4.resources import Bundle, Composition
from pathology_api.logging import get_logger

_logger = get_logger(__name__)


def _validate_composition(bundle: Bundle) -> None:
    compositions = bundle.find_resources(t=Composition)
    if len(compositions) != 1:
        raise ValidationError("Document must include a single Composition resource")

    subject = compositions[0].subject
    if subject is None:
        raise ValidationError("Composition does not define a valid subject identifier")


def _validate_bundle(bundle: Bundle) -> None:
    if bundle.id is not None:
        raise ValidationError("Bundles cannot be defined with an existing ID")

    if bundle.bundle_type != "document":
        raise ValidationError("Resource must be a bundle of type 'document'")


type ValidationFunction = Callable[[Bundle], None]
_validation_functions: list[ValidationFunction] = [
    _validate_composition,
    _validate_bundle,
]


def handle_request(bundle: Bundle) -> Bundle:
    for validate_function in _validation_functions:
        validate_function(bundle)

    _logger.debug("Bundle entries: %s", bundle.entries)
    return_bundle = Bundle.create(
        id=str(uuid.uuid4()),
        meta=Meta.with_last_updated(),
        identifier=bundle.identifier,
        type=bundle.bundle_type,
        entry=bundle.entries,
    )
    _logger.debug("Return bundle: %s", return_bundle)

    return return_bundle

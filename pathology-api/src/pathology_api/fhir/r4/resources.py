from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from .elements import Identifier, Meta, UUIDIdentifier


class Resource(BaseModel):
    """A FHIR R4 Resource base class."""

    meta: Annotated[Meta, Field(alias="meta", frozen=True)] = Meta()
    # This field is set automatically for subclasses via the __init_subclass__ method.
    # Just setting a default value here so mypy doesn't require this field is set when
    # instantiating an object.
    resource_type: str = Field("__resource_type__", alias="resourceType", frozen=True)

    def __init_subclass__(cls, resource_type: str, **kwargs: Any) -> None:
        cls.resource_type = resource_type
        super().__init_subclass__(**kwargs)


type BundleType = Literal["document", "transaction"]


class TestResultBundle(Resource, resource_type="Bundle"):
    """A FHIR R4 Bundle resource."""

    bundle_type: BundleType = Field(..., alias="type", frozen=True)
    identifier: Annotated[UUIDIdentifier | None, Field(frozen=True)] = None
    entries: Annotated[list["TestResultBundle.Entry"] | None, Field(frozen=True)] = None

    class Entry(BaseModel):
        full_url: Annotated[str, Field(frozen=True)]
        resource: Annotated["AnyResource", Field(frozen=True)]

    def find_resources[T: Resource](self, t: type[T]) -> list[T]:
        """
        Find all resources of a given type in the bundle entries. If the bundle has no
        entries, an empty list is returned.
        Args:
            t: The resource type to search for.
        Returns:
            A list of resources of the specified type.
        """
        if not self.entries:
            return []

        return [
            entry.resource for entry in self.entries if isinstance(entry.resource, t)
        ]


class Patient(Resource, resource_type="Patient"):
    """A FHIR R4 Patient resource."""

    class PatientIdentifier(
        Identifier,
        system="https://fhir.nhs.uk/Id/nhs-number",
    ):
        """A FHIR R4 Patient Identifier utilising the NHS Number system."""

        @classmethod
        def from_nhs_number(cls, nhs_number: str) -> "Patient.PatientIdentifier":
            """Create a PatientIdentifier from an NHS number."""
            return cls(value=nhs_number)

    identifier: Annotated[PatientIdentifier, Field(frozen=True)]


type AnyResource = TestResultBundle | Patient

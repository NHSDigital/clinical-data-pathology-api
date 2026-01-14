from typing import Annotated, Any, ClassVar, Literal

from pydantic import (
    BaseModel,
    Field,
    SerializeAsAny,
    ValidatorFunctionWrapHandler,
    model_validator,
)

from .elements import Identifier, Meta, UUIDIdentifier


class Resource(BaseModel):
    """A FHIR R4 Resource base class."""

    # class variable to hold class mappings per resource_type
    __resource_types__: ClassVar[dict[str, type["Resource"]]] = {}

    meta: Annotated[Meta, Field(alias="meta", frozen=True)] = Meta()
    # Defaulted to "Resource" for type hinting, set based on subclass within
    # __init_subclass__
    resource_type: Annotated[str, Field(alias="resourceType", frozen=True)] = "Resource"

    def __init_subclass__(cls, resource_type: str, **kwargs: Any) -> None:
        cls.__resource_types__[resource_type] = cls

        cls.resource_type = resource_type
        super().__init_subclass__(**kwargs)

    @model_validator(mode="wrap")
    @classmethod
    def validate_with_subtype(
        cls, value: dict[str, Any], handler: ValidatorFunctionWrapHandler
    ) -> Any:
        """
        Provides a model validator that instantiates the correct Resource subclass
        based on the its defined resource_type.
        """
        # If we're not currently acting on a top level Resource, and we've not been
        # provided a generic dictonary object, delegate to the normal handler.
        if cls != Resource or not isinstance(value, dict):
            return handler(value)

        resource_type = value["resourceType"]

        if not resource_type:
            raise TypeError("resource_type is required for Resource validation.")

        subclass = cls.__resource_types__.get(resource_type)
        if not subclass:
            raise TypeError(f"Unknown resource type: {resource_type}")

        # Instantiate the subclass using the dictionary values.
        return subclass.model_validate(value)


type BundleType = Literal["document", "transaction"]


class Bundle(Resource, resource_type="Bundle"):
    """A FHIR R4 Bundle resource."""

    bundle_type: BundleType = Field(alias="type", frozen=True)
    identifier: Annotated[UUIDIdentifier | None, Field(frozen=True)] = None
    entries: list["Bundle.Entry"] | None = Field(None, frozen=True, alias="entry")

    class Entry(BaseModel):
        full_url: str = Field(..., alias="fullUrl", frozen=True)
        resource: Annotated[SerializeAsAny[Resource], Field(frozen=True)]

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

    @classmethod
    def empty(cls, bundle_type: BundleType) -> "Bundle":
        """Create an empty Bundle of the specified type."""
        return cls(type=bundle_type, entry=None)


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

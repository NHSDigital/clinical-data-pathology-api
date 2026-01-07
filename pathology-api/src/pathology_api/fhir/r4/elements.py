import datetime
import uuid
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class Meta:
    """
    A FHIR R4 Meta element. See https://hl7.org/fhir/R4/datatypes.html#Meta.
    Attributes:
        version_id: The version id of the resource.
        last_updated: The last updated timestamp of the resource.
    """

    version_id: str | None = None
    last_updated: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)


@dataclass(frozen=True)
class Identifier:
    """
    A FHIR R4 Identifier element. See https://hl7.org/fhir/R4/datatypes.html#Identifier.
    Attributes:
        system: The namespace for the identifier value.
        value: The value that is unique within the system.
    """

    system: ClassVar[str]
    value: str

    def __init_subclass__(cls: type["Identifier"], system: str, **kwargs: Any) -> None:
        """
        Subclass constructor to enforce system value.
        Args:
            system: The system value for the identifier subclass.
            **kwargs: Additional keyword arguments.
        """

        super().__init_subclass__(**kwargs)
        cls.system = system


class UUIDIdentifier(Identifier, system="https://tools.ietf.org/html/rfc4122"):
    """A UUID identifier utilising the standard RFC 4122 system."""

    def __init__(self, value: uuid.UUID | None = None):
        super().__init__(value=str(value or uuid.uuid4()))


@dataclass(frozen=True)
class LiteralReference:
    """Class representing a literal FHIR Reference. See https://hl7.org/fhir/R4/references.html#literal"""

    reference: str


@dataclass(frozen=True)
class LogicalReference[T: Identifier]:
    """Class representing a logical FHIR Reference. See https://hl7.org/fhir/R4/references.html#logical"""

    identifier: T


"""Type defining a FHIR Reference. See https://hl7.org/fhir/R4/references.html#Reference"""
type Reference[T] = LiteralReference | LogicalReference[T]

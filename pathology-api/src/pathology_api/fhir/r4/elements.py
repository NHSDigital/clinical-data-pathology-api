import datetime
import uuid
from abc import ABC
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

    last_updated: datetime.datetime | None = None
    version_id: str | None = None

    @classmethod
    def with_last_updated(cls, last_updated: datetime.datetime | None) -> "Meta":
        """
        Create a Meta instance with the provided last_updated timestamp.
        Args:
            last_updated: The last updated timestamp.
        Returns:
            A Meta instance with the specified last_updated.
        """
        return cls(
            last_updated=last_updated or datetime.datetime.now(tz=datetime.timezone.utc)
        )


@dataclass(frozen=True)
class Identifier(ABC):
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

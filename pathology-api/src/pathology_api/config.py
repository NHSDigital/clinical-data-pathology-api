import os
import re
from dataclasses import dataclass
from datetime import timedelta
from enum import StrEnum
from typing import cast


class ConfigError(Exception):
    pass


class DurationUnit(StrEnum):
    SECONDS = "s"
    MINUTES = "m"


@dataclass(frozen=True)
class Duration:
    def __init__(self, unit: DurationUnit, value: int):
        self.unit = unit
        self.value = value

    @property
    def timedelta(self) -> timedelta:
        match self.unit:
            case DurationUnit.SECONDS:
                return timedelta(seconds=self.value)
            case DurationUnit.MINUTES:
                return timedelta(minutes=self.value)


def get_optional_environment_variable[T](name: str, _type: type[T]) -> T | None:
    value = os.getenv(name)

    if _type is Duration and value is not None:
        parsed = re.fullmatch(r"(?P<value>\d+)(?P<unit>[sm])", value)
        if parsed is None:
            raise ConfigError(f"Invalid duration value: {value!r}")

        raw_value = parsed.group("value")
        raw_unit = parsed.group("unit")

        if not raw_value or not raw_value.isdigit():
            raise ConfigError(f"Invalid duration value: {value!r}")

        return cast(
            "T",
            Duration(
                unit=DurationUnit(raw_unit),
                value=int(raw_value),
            ),
        )
    elif value is not None:
        if not isinstance(value, _type):
            raise ConfigError(f"Environment variable {name!r} is not of type {_type!r}")

        return value
    else:
        return None


def get_environment_variable[T](name: str, _type: type[T]) -> T:
    value = get_optional_environment_variable(name=name, _type=_type)
    if value is None:
        raise ConfigError(f"Environment variable {name!r} is not set")
    return value

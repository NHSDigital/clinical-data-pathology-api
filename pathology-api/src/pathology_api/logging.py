from typing import Any, Protocol

from aws_lambda_powertools import Logger


class LogProvider(Protocol):
    """Protocol defining required contract for a logger."""

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None: ...


def get_logger(service: str) -> LogProvider:
    """Get a configured logger instance."""
    return Logger(service=service, level="DEBUG", serialize_stacktrace=True)

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


@contextmanager
def set_correlation_id(value: str) -> Generator[None, None, None]:
    """Set the correlation ID for the current request context."""
    _correlation_id.set(value)
    try:
        yield None
    finally:
        _correlation_id.set("")


def get_correlation_id() -> str:
    """Get the correlation ID for the current request context."""
    return _correlation_id.get()

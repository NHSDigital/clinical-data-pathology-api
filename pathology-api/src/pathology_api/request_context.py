from contextvars import ContextVar

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def set_correlation_id(value: str) -> None:
    """Set the correlation ID for the current request context."""
    _correlation_id.set(value)


def get_correlation_id() -> str:
    """Get the correlation ID for the current request context."""
    return _correlation_id.get()

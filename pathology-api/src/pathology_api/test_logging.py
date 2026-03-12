import logging

from pathology_api.logging import (
    _CorrelationIdFilter,
    get_logger,
)
from pathology_api.request_context import set_correlation_id


class TestCorrelationIdFilter:
    def test_filter_injects_correlation_id_into_log_record(self) -> None:
        set_correlation_id("test-abc-123")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=None,
            exc_info=None,
        )

        f = _CorrelationIdFilter()
        result = f.filter(record)

        assert result is True
        assert record.correlation_id == "test-abc-123"  # type: ignore[attr-defined]

    def test_filter_uses_empty_default_when_no_correlation_id_set(self) -> None:
        set_correlation_id("")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=None,
            exc_info=None,
        )

        f = _CorrelationIdFilter()
        f.filter(record)

        assert record.correlation_id == ""  # type: ignore[attr-defined]


class TestGetLogger:
    def test_get_logger_attaches_correlation_id_filter(self) -> None:
        logger = get_logger("test-service")

        filters = getattr(logger, "filters", [])
        assert any(isinstance(f, _CorrelationIdFilter) for f in filters)

from pathology_api.request_context import get_correlation_id, set_correlation_id


class TestSetAndGetCorrelationId:
    def test_set_and_get_correlation_id(self) -> None:
        set_correlation_id("round-trip-test-123")
        assert get_correlation_id() == "round-trip-test-123"

    def test_default_correlation_id_is_empty(self) -> None:
        set_correlation_id("")
        assert get_correlation_id() == ""

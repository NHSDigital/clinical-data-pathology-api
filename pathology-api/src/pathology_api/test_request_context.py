from pathology_api.request_context import get_correlation_id, set_correlation_id


class TestSetAndGetCorrelationId:
    def test_set_and_get_correlation_id_within_context(self) -> None:
        with set_correlation_id("round-trip-test-123"):
            assert get_correlation_id() == "round-trip-test-123"

    def test_correlation_id_is_cleared_after_context_exit(self) -> None:
        with set_correlation_id("round-trip-test-123"):
            assert get_correlation_id() == "round-trip-test-123"

        assert get_correlation_id() == ""

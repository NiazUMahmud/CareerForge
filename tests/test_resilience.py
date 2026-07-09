import pytest

from careerforge.resilience import call_with_retry, extract_retry_seconds, is_rate_limit_error


class FakeRateLimitError(Exception):
    status_code = 429


def test_is_rate_limit_error_via_status_code():
    assert is_rate_limit_error(FakeRateLimitError("boom"))


def test_is_rate_limit_error_via_message():
    assert is_rate_limit_error(Exception("rate_limit_exceeded: too many tokens"))


def test_is_rate_limit_error_false_for_unrelated_error():
    assert not is_rate_limit_error(ValueError("bad input"))


def test_extract_retry_seconds_parses_message():
    exc = Exception("Please try again in 14.074s.")
    assert extract_retry_seconds(exc, default=99) == pytest.approx(15.074)


def test_extract_retry_seconds_falls_back_to_default():
    exc = Exception("rate_limit_exceeded, no timing hint")
    assert extract_retry_seconds(exc, default=42) == 42


def test_call_with_retry_succeeds_after_transient_rate_limit(monkeypatch):
    sleeps = []
    monkeypatch.setattr("careerforge.resilience.time.sleep", lambda s: sleeps.append(s))

    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise Exception("rate_limit_exceeded, try again in 1s")
        return "ok"

    result = call_with_retry(flaky, max_retries=3, default_wait=5)
    assert result == "ok"
    assert attempts["count"] == 3
    assert len(sleeps) == 2


def test_call_with_retry_reraises_non_rate_limit_errors(monkeypatch):
    def always_fails():
        raise ValueError("not a rate limit issue")

    with pytest.raises(ValueError):
        call_with_retry(always_fails, max_retries=3)


def test_call_with_retry_reraises_after_exhausting_attempts(monkeypatch):
    monkeypatch.setattr("careerforge.resilience.time.sleep", lambda s: None)

    def always_rate_limited():
        raise Exception("rate_limit_exceeded")

    with pytest.raises(Exception, match="rate_limit_exceeded"):
        call_with_retry(always_rate_limited, max_retries=2, default_wait=0.01)

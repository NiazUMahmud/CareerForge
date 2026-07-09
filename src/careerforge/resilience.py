"""Retry helper for transient rate-limit errors from LLM providers.

A deep agent can burn through a provider's tokens-per-minute budget quickly
— the main planner plus several subagent calls can all fire within the same
60-second window — so a 429/rate-limit response here is an expected,
recoverable condition, not a fatal error worth surfacing raw to the user.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_RETRY_SECONDS_RE = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)


def is_rate_limit_error(exc: BaseException) -> bool:
    """Best-effort provider-agnostic check (OpenAI, Groq, Anthropic clients
    all vary in exception type but converge on a 429 status / message)."""
    status = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "response", None), "status_code", None
    )
    if status == 429:
        return True
    text = str(exc).lower()
    return "rate_limit" in text or "429" in text


def extract_retry_seconds(exc: BaseException, default: float) -> float:
    """Parse a provider-suggested wait (e.g. "...try again in 14.074s") when
    present; otherwise fall back to ``default``."""
    match = _RETRY_SECONDS_RE.search(str(exc))
    if match:
        return float(match.group(1)) + 1  # small buffer
    return default


def call_with_retry(
    fn: Callable[[], T],
    max_retries: int = 3,
    default_wait: float = 20.0,
    on_retry: Callable[[int, float], None] | None = None,
) -> T:
    """Call ``fn()``, retrying only on rate-limit errors. Any other
    exception, or a rate-limit error on the final attempt, propagates."""
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — provider error types vary by SDK
            if not is_rate_limit_error(exc) or attempt == max_retries:
                raise
            wait = extract_retry_seconds(exc, default_wait * (attempt + 1))
            if on_retry:
                on_retry(attempt + 1, wait)
            time.sleep(wait)
    raise AssertionError("unreachable")  # pragma: no cover

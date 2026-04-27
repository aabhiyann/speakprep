"""Unit tests for LLMService — all provider SDK clients are mocked."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch


from app.services.llm_service import (
    CircuitBreaker,
    LLMService,
    Message,
    _CBState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _groq_response(content: str = "Great answer.", tokens: int = 42) -> MagicMock:
    response = MagicMock()
    response.choices[0].message.content = content
    response.usage.total_tokens = tokens
    response.model = "llama-3.3-70b-versatile"
    return response


def _make_service(groq_mock: MagicMock) -> LLMService:
    """Build an LLMService with only a mocked Groq client."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
        with patch("app.services.llm_service.AsyncGroq", return_value=groq_mock):
            return LLMService()


MESSAGES = [
    Message(role="system", content="You are an interview coach."),
    Message(role="user", content="Tell me about yourself."),
]


# ---------------------------------------------------------------------------
# CircuitBreaker state machine
# ---------------------------------------------------------------------------


def test_circuit_breaker_starts_closed() -> None:
    cb = CircuitBreaker()
    assert cb.state == _CBState.CLOSED
    assert cb.is_available() is True


def test_circuit_breaker_stays_closed_below_threshold() -> None:
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == _CBState.CLOSED
    assert cb.is_available() is True


def test_circuit_breaker_opens_at_threshold() -> None:
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == _CBState.OPEN
    assert cb.is_available() is False


def test_circuit_breaker_transitions_to_half_open_after_timeout() -> None:
    fake_time = [0.0]
    cb = CircuitBreaker(
        failure_threshold=1, recovery_timeout=60.0, _clock=lambda: fake_time[0]
    )
    cb.record_failure()
    assert cb.state == _CBState.OPEN

    fake_time[0] = 61.0
    assert cb.is_available() is True
    assert cb.state == _CBState.HALF_OPEN


def test_circuit_breaker_half_open_blocks_second_request() -> None:
    fake_time = [0.0]
    cb = CircuitBreaker(
        failure_threshold=1, recovery_timeout=60.0, _clock=lambda: fake_time[0]
    )
    cb.record_failure()
    fake_time[0] = 61.0

    assert cb.is_available() is True  # first — allowed
    assert cb.is_available() is False  # second — blocked


def test_circuit_breaker_closes_on_success_in_half_open() -> None:
    fake_time = [0.0]
    cb = CircuitBreaker(
        failure_threshold=1, recovery_timeout=60.0, _clock=lambda: fake_time[0]
    )
    cb.record_failure()
    fake_time[0] = 61.0
    cb.is_available()  # transition to HALF_OPEN

    cb.record_success()
    assert cb.state == _CBState.CLOSED
    assert cb.is_available() is True


def test_circuit_breaker_reopens_on_failure_in_half_open() -> None:
    fake_time = [0.0]
    cb = CircuitBreaker(
        failure_threshold=1, recovery_timeout=60.0, _clock=lambda: fake_time[0]
    )
    cb.record_failure()
    fake_time[0] = 61.0
    cb.is_available()  # transition to HALF_OPEN

    cb.record_failure()
    assert cb.state == _CBState.OPEN
    assert cb.is_available() is False

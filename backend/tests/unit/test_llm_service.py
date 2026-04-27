"""Unit tests for LLMService — all provider SDK clients are mocked."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.llm_service import (
    CircuitBreaker,
    LLMResponse,
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


# ---------------------------------------------------------------------------
# LLMService.generate — Groq success path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_groq_success_returns_llm_response() -> None:
    groq_mock = MagicMock()
    groq_mock.chat.completions.create = AsyncMock(
        return_value=_groq_response("Start with your background.")
    )
    svc = _make_service(groq_mock)

    result = await svc.generate(MESSAGES)

    assert isinstance(result, LLMResponse)
    assert result.content == "Start with your background."
    assert result.provider == "groq"
    assert result.model == "llama-3.3-70b-versatile"
    assert result.tokens_used == 42
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_generate_groq_calls_api_with_correct_messages() -> None:
    groq_mock = MagicMock()
    groq_mock.chat.completions.create = AsyncMock(return_value=_groq_response())
    svc = _make_service(groq_mock)

    await svc.generate(MESSAGES)

    call_kwargs = groq_mock.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "llama-3.3-70b-versatile"
    assert call_kwargs["messages"] == [m.model_dump() for m in MESSAGES]
    assert call_kwargs["max_tokens"] == 200
    assert call_kwargs["temperature"] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# LLMService.generate — fallback to Cerebras on Groq failure
# ---------------------------------------------------------------------------


def _make_service_two_providers(
    groq_mock: MagicMock, cerebras_mock: MagicMock
) -> LLMService:
    """Build LLMService with Groq + Cerebras, both mocked."""
    with patch.dict(os.environ, {"GROQ_API_KEY": "g-key", "CEREBRAS_API_KEY": "c-key"}):
        with patch("app.services.llm_service.AsyncGroq", return_value=groq_mock):
            with patch("app.services.llm_service._CEREBRAS_AVAILABLE", True):
                with patch(
                    "app.services.llm_service.AsyncCerebras", return_value=cerebras_mock
                ):
                    return LLMService()


@pytest.mark.asyncio
async def test_generate_falls_back_to_cerebras_on_groq_rate_limit() -> None:
    from groq import RateLimitError

    groq_mock = MagicMock()
    groq_mock.chat.completions.create = AsyncMock(
        side_effect=RateLimitError("rate limited", response=MagicMock(), body={})
    )

    cerebras_mock = MagicMock()
    cerebras_mock.chat.completions.create = AsyncMock(
        return_value=_groq_response("Cerebras fallback response.", tokens=30)
    )

    svc = _make_service_two_providers(groq_mock, cerebras_mock)
    result = await svc.generate(MESSAGES)

    assert result.provider == "cerebras"
    assert result.content == "Cerebras fallback response."
    assert result.tokens_used == 30
    # Groq circuit breaker should have recorded a failure
    groq_provider = svc._providers[0]
    assert groq_provider.circuit_breaker._failures == 1

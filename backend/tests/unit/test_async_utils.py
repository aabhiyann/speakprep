"""Unit tests for async utility examples."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from app.utils import async_examples


class DummyLogger:
    """Simple logger test double for structlog calls."""

    def __init__(self) -> None:
        self.records: list[tuple[str, str, dict[str, Any]]] = []

    def info(self, event: str, **kwargs: Any) -> None:
        self.records.append(("info", event, kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        self.records.append(("warning", event, kwargs))


@pytest.mark.asyncio
async def test_run_concurrently_returns_results_in_input_order() -> None:
    async def fast() -> str:
        await asyncio.sleep(0.01)
        return "fast"

    async def slow() -> str:
        await asyncio.sleep(0.03)
        return "slow"

    logger = DummyLogger()
    original_logger = async_examples.logger
    async_examples.logger = logger
    try:
        results = await async_examples.run_concurrently([slow(), fast()])
    finally:
        async_examples.logger = original_logger

    assert results == ["slow", "fast"]
    assert logger.records
    level, event, payload = logger.records[0]
    assert level == "info"
    assert event == "run_concurrently_completed"
    assert payload["total_tasks"] == 2
    assert payload["estimated_sequential_secs"] >= payload["concurrent_secs"]


@pytest.mark.asyncio
async def test_retry_with_backoff_retries_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = {"count": 0}

    async def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("transient failure")
        return "ok"

    logger = DummyLogger()
    original_logger = async_examples.logger
    async_examples.logger = logger

    slept_for: list[float] = []

    async def fake_sleep(duration: float) -> None:
        slept_for.append(duration)

    monkeypatch.setattr(async_examples.random, "uniform", lambda _a, _b: 1.0)
    monkeypatch.setattr(async_examples.asyncio, "sleep", fake_sleep)

    try:
        result = await async_examples.retry_with_backoff(flaky, max_retries=3)
    finally:
        async_examples.logger = original_logger

    assert result == "ok"
    assert attempts["count"] == 3
    assert slept_for == [1.0, 2.0]
    warning_events = [record for record in logger.records if record[0] == "warning"]
    assert len(warning_events) == 2
    assert warning_events[0][2]["reason"] == "transient failure"


@pytest.mark.asyncio
async def test_retry_with_backoff_raises_last_exception_when_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def always_fails() -> None:
        raise ValueError("permanent failure")

    async def fake_sleep(_duration: float) -> None:
        return None

    monkeypatch.setattr(async_examples.random, "uniform", lambda _a, _b: 1.0)
    monkeypatch.setattr(async_examples.asyncio, "sleep", fake_sleep)

    with pytest.raises(ValueError, match="permanent failure"):
        await async_examples.retry_with_backoff(always_fails, max_retries=2)


@pytest.mark.asyncio
async def test_timeout_with_fallback_returns_fallback_on_timeout() -> None:
    async def never_finishes() -> str:
        await asyncio.sleep(0.2)
        return "late"

    logger = DummyLogger()
    original_logger = async_examples.logger
    async_examples.logger = logger
    try:
        result = await async_examples.timeout_with_fallback(
            never_finishes(),
            timeout_secs=0.01,
            fallback="fallback",
        )
    finally:
        async_examples.logger = original_logger

    assert result == "fallback"
    warning_events = [record for record in logger.records if record[0] == "warning"]
    assert warning_events
    assert warning_events[0][1] == "timeout_with_fallback_used"

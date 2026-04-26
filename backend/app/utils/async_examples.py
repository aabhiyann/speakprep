"""Async utility examples for concurrent execution and resilience."""

from __future__ import annotations

import asyncio
import random
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

import structlog

logger = structlog.get_logger(__name__)

T = TypeVar("T")


async def run_concurrently(tasks: list[Coroutine[Any, Any, T]]) -> list[T]:
    """Run coroutines concurrently and log concurrent vs sequential timing."""

    async def _run_timed(task: Coroutine[Any, Any, T]) -> tuple[T, float]:
        started_at = time.perf_counter()
        result = await task
        duration_secs = time.perf_counter() - started_at
        return result, duration_secs

    started_at = time.perf_counter()
    timed_results = await asyncio.gather(*(_run_timed(task) for task in tasks))
    total_concurrent_secs = time.perf_counter() - started_at

    results = [result for result, _ in timed_results]
    estimated_sequential_secs = sum(duration for _, duration in timed_results)

    logger.info(
        "run_concurrently_completed",
        total_tasks=len(tasks),
        concurrent_secs=round(total_concurrent_secs, 4),
        estimated_sequential_secs=round(estimated_sequential_secs, 4),
    )
    return results


async def retry_with_backoff(
    coro_func: Callable[[], Coroutine[Any, Any, T]],
    max_retries: int = 3,
) -> T:
    """Retry a coroutine function with exponential backoff and jitter."""

    if max_retries < 0:
        raise ValueError("max_retries must be >= 0")

    last_exception: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return await coro_func()
        except Exception as exc:  # noqa: BLE001
            last_exception = exc
            if attempt >= max_retries:
                break

            base_delay_secs = float(2**attempt)
            delay_secs = base_delay_secs * random.uniform(0.75, 1.25)
            logger.warning(
                "retry_with_backoff_attempt_failed",
                attempt_number=attempt + 1,
                max_retries=max_retries,
                retry_in_secs=round(delay_secs, 4),
                reason=str(exc),
            )
            await asyncio.sleep(delay_secs)

    assert last_exception is not None  # Helps static type checkers.
    raise last_exception


async def timeout_with_fallback(
    coro: Coroutine[Any, Any, T],
    timeout_secs: float,
    fallback: T,
) -> T:
    """Run a coroutine with timeout and return fallback on timeout."""

    try:
        return await asyncio.wait_for(coro, timeout=timeout_secs)
    except asyncio.TimeoutError:
        logger.warning(
            "timeout_with_fallback_used",
            timeout_secs=timeout_secs,
        )
        return fallback

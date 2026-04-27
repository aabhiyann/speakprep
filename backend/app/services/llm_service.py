"""LLM service with multi-provider fallback and per-provider circuit breakers."""

from __future__ import annotations

import time
from enum import Enum


class _CBState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Per-provider circuit breaker.

    CLOSED  → normal operation, tracks consecutive failures
    OPEN    → rejects all requests immediately
    HALF_OPEN → allows exactly one test request after recovery_timeout seconds
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
        _clock=time.time,  # injectable for tests — avoids monkeypatching
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._clock = _clock
        self._state = _CBState.CLOSED
        self._failures = 0
        self._opened_at: float | None = None
        self._half_open_in_flight = False

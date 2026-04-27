"""LLM service with multi-provider fallback and per-provider circuit breakers."""

from __future__ import annotations

import time
from enum import Enum
from typing import Literal

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    latency_ms: int
    tokens_used: int


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

    def is_available(self) -> bool:
        """Return True if a request should be allowed through."""
        if self._state == _CBState.CLOSED:
            return True

        if self._state == _CBState.OPEN:
            if self._clock() - (self._opened_at or 0) >= self._recovery_timeout:
                self._state = _CBState.HALF_OPEN
            else:
                return False

        # HALF_OPEN: allow exactly one in-flight request
        if self._half_open_in_flight:
            return False
        self._half_open_in_flight = True
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._half_open_in_flight = False
        self._state = _CBState.CLOSED

    def record_failure(self) -> None:
        self._half_open_in_flight = False
        if self._state == _CBState.HALF_OPEN:
            # test request failed — go back to OPEN
            self._state = _CBState.OPEN
            self._opened_at = self._clock()
        elif self._state == _CBState.CLOSED:
            self._failures += 1
            if self._failures >= self._failure_threshold:
                self._state = _CBState.OPEN
                self._opened_at = self._clock()

    @property
    def state(self) -> _CBState:
        return self._state

"""LLM service with multi-provider fallback and per-provider circuit breakers."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

import structlog
from groq import AsyncGroq
from pydantic import BaseModel

try:
    from cerebras.cloud.sdk import AsyncCerebras  # type: ignore[import-untyped]

    _CEREBRAS_AVAILABLE = True
except ImportError:
    AsyncCerebras = None  # type: ignore[assignment,misc]
    _CEREBRAS_AVAILABLE = False

try:
    import google.generativeai as genai  # type: ignore[import-untyped]

    _GEMINI_AVAILABLE = True
except ImportError:
    genai = None  # type: ignore[assignment]
    _GEMINI_AVAILABLE = False

logger = structlog.get_logger(__name__)


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


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    latency_ms: int
    tokens_used: int


@dataclass
class _Provider:
    """Bundles an SDK client with its model name and circuit breaker."""

    name: str
    client: Any
    model: str
    circuit_breaker: CircuitBreaker = field(default_factory=CircuitBreaker)


class LLMService:
    def __init__(self) -> None:
        self._providers: list[_Provider] = []
        self._setup_providers()

    def _setup_providers(self) -> None:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY is required but not set")
        self._providers.append(
            _Provider(
                name="groq",
                client=AsyncGroq(api_key=groq_key),
                model="llama-3.3-70b-versatile",
            )
        )

        cerebras_key = os.getenv("CEREBRAS_API_KEY")
        if cerebras_key and _CEREBRAS_AVAILABLE:
            self._providers.append(
                _Provider(
                    name="cerebras",
                    client=AsyncCerebras(api_key=cerebras_key),
                    model="llama3.3-70b",
                )
            )

        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and _GEMINI_AVAILABLE:
            genai.configure(api_key=gemini_key)
            self._providers.append(
                _Provider(
                    name="gemini",
                    client=genai.GenerativeModel("gemini-1.5-flash"),
                    model="gemini-1.5-flash",
                )
            )

    async def _call_groq(
        self,
        provider: _Provider,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int]:
        response = await provider.client.chat.completions.create(
            model=provider.model,
            messages=[m.model_dump() for m in messages],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return content, tokens

    async def _call_cerebras(
        self,
        provider: _Provider,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int]:
        # Cerebras exposes an OpenAI-compatible chat completions API
        response = await provider.client.chat.completions.create(
            model=provider.model,
            messages=[m.model_dump() for m in messages],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return content, tokens

    def _to_gemini_messages(
        self, messages: list[Message]
    ) -> tuple[list[dict], str | None]:
        """Convert OpenAI-style messages to Gemini format.

        Gemini separates system instructions from the conversation turns,
        and uses role="model" instead of role="assistant".
        """
        system_parts: list[str] = []
        contents: list[dict] = []
        for msg in messages:
            if msg.role == "system":
                system_parts.append(msg.content)
            else:
                role = "model" if msg.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": msg.content}]})
        system = " ".join(system_parts) if system_parts else None
        return contents, system

    async def _call_gemini(
        self,
        provider: _Provider,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int]:
        contents, system_instruction = self._to_gemini_messages(messages)
        config = genai.GenerationConfig(
            max_output_tokens=max_tokens, temperature=temperature
        )
        model = (
            genai.GenerativeModel(provider.model, system_instruction=system_instruction)
            if system_instruction
            else provider.client
        )
        response = await model.generate_content_async(
            contents, generation_config=config
        )
        content = response.text or ""
        tokens = (
            response.usage_metadata.total_token_count if response.usage_metadata else 0
        )
        return content, tokens

    async def _call_provider(
        self,
        provider: _Provider,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
    ) -> tuple[str, int]:
        if provider.name == "groq":
            return await self._call_groq(provider, messages, max_tokens, temperature)
        if provider.name == "cerebras":
            return await self._call_cerebras(
                provider, messages, max_tokens, temperature
            )
        if provider.name == "gemini":
            return await self._call_gemini(provider, messages, max_tokens, temperature)
        raise ValueError(f"Unknown provider: {provider.name}")

    async def generate(
        self,
        messages: list[Message],
        max_tokens: int = 200,
        temperature: float = 0.7,
    ) -> LLMResponse:
        for provider in self._providers:
            if not provider.circuit_breaker.is_available():
                continue
            started = time.perf_counter()
            try:
                content, tokens = await self._call_provider(
                    provider, messages, max_tokens, temperature
                )
                latency_ms = int((time.perf_counter() - started) * 1000)
                provider.circuit_breaker.record_success()
                logger.info(
                    "llm.call.success",
                    provider=provider.name,
                    model=provider.model,
                    latency_ms=latency_ms,
                    tokens_used=tokens,
                )
                return LLMResponse(
                    content=content,
                    provider=provider.name,
                    model=provider.model,
                    latency_ms=latency_ms,
                    tokens_used=tokens,
                )
            except Exception as exc:
                provider.circuit_breaker.record_failure()
                logger.warning(
                    "llm.provider.failure", provider=provider.name, error=str(exc)
                )
        raise RuntimeError("All LLM providers failed or circuit breakers are open")

    async def _stream_provider(
        self,
        provider: _Provider,
        messages: list[Message],
        max_tokens: int,
        temperature: float,
    ):
        if provider.name in ("groq", "cerebras"):
            stream = await provider.client.chat.completions.create(
                model=provider.model,
                messages=[m.model_dump() for m in messages],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        elif provider.name == "gemini":
            contents, system_instruction = self._to_gemini_messages(messages)
            config = genai.GenerationConfig(
                max_output_tokens=max_tokens, temperature=temperature
            )
            model = (
                genai.GenerativeModel(
                    provider.model, system_instruction=system_instruction
                )
                if system_instruction
                else provider.client
            )
            response = await model.generate_content_async(
                contents, generation_config=config, stream=True
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text

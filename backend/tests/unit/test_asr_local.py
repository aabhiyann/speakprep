"""Unit tests for LocalASR — WhisperModel is mocked, no actual inference runs."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.services.asr_local import LocalASR, TranscriptionResult


def _make_segment(
    text: str = "Hello world.",
    no_speech_prob: float = 0.05,
    compression_ratio: float = 1.1,
) -> MagicMock:
    seg = MagicMock()
    seg.text = text
    seg.no_speech_prob = no_speech_prob
    seg.compression_ratio = compression_ratio
    return seg


def _make_info(language: str = "en", duration: float = 3.0) -> MagicMock:
    info = MagicMock()
    info.language = language
    info.duration = duration
    return info


@pytest.fixture
def mock_whisper_model() -> MagicMock:
    """A WhisperModel mock that returns a single clean segment by default."""
    model = MagicMock()
    model.transcribe.return_value = (iter([_make_segment()]), _make_info())
    return model


@pytest.fixture
def asr(mock_whisper_model: MagicMock) -> LocalASR:
    with patch("app.services.asr_local.WhisperModel", return_value=mock_whisper_model):
        return LocalASR()


# --- hallucination filters ---


@pytest.mark.asyncio
async def test_transcribe_returns_none_when_no_speech_prob_high(asr: LocalASR) -> None:
    asr._model.transcribe.return_value = (
        iter([_make_segment(no_speech_prob=0.8)]),
        _make_info(),
    )
    audio = np.ones(16000, dtype=np.int16) * 500
    result = await asr.transcribe(audio)
    assert result is None


@pytest.mark.asyncio
async def test_transcribe_returns_none_when_compression_ratio_high(
    asr: LocalASR,
) -> None:
    asr._model.transcribe.return_value = (
        iter([_make_segment(compression_ratio=3.0)]),
        _make_info(),
    )
    audio = np.ones(16000, dtype=np.int16) * 500
    result = await asr.transcribe(audio)
    assert result is None


@pytest.mark.asyncio
async def test_transcribe_returns_none_when_text_is_empty(asr: LocalASR) -> None:
    asr._model.transcribe.return_value = (
        iter([_make_segment(text="   ")]),
        _make_info(),
    )
    audio = np.ones(16000, dtype=np.int16) * 500
    result = await asr.transcribe(audio)
    assert result is None


# --- valid output ---


@pytest.mark.asyncio
async def test_transcribe_returns_result_with_correct_fields(asr: LocalASR) -> None:
    asr._model.transcribe.return_value = (
        iter([_make_segment(text="Tell me about yourself.", no_speech_prob=0.04)]),
        _make_info(language="en", duration=2.5),
    )
    audio = np.ones(16000 * 3, dtype=np.int16) * 1000
    result = await asr.transcribe(audio)

    assert result is not None
    assert isinstance(result, TranscriptionResult)
    assert result.text == "Tell me about yourself."
    assert result.language == "en"
    assert result.duration_seconds == 2.5
    assert result.no_speech_prob == pytest.approx(0.04)
    assert isinstance(result.latency_ms, int)
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_transcribe_joins_multiple_segments(asr: LocalASR) -> None:
    segments = [
        _make_segment(text="First sentence."),
        _make_segment(text="Second sentence."),
    ]
    asr._model.transcribe.return_value = (iter(segments), _make_info())
    audio = np.ones(32000, dtype=np.int16) * 1000

    result = await asr.transcribe(audio)

    assert result is not None
    assert result.text == "First sentence. Second sentence."


# --- edge cases ---


@pytest.mark.asyncio
async def test_transcribe_returns_none_for_empty_audio(asr: LocalASR) -> None:
    result = await asr.transcribe(np.zeros(0, dtype=np.int16))
    assert result is None
    asr._model.transcribe.assert_not_called()


@pytest.mark.asyncio
async def test_transcribe_returns_none_when_no_segments(asr: LocalASR) -> None:
    asr._model.transcribe.return_value = (iter([]), _make_info())
    audio = np.ones(16000, dtype=np.int16) * 500
    result = await asr.transcribe(audio)
    assert result is None


@pytest.mark.asyncio
async def test_transcribe_uses_worst_case_no_speech_across_segments(
    asr: LocalASR,
) -> None:
    """A single bad segment should filter the whole result even if others are fine."""
    segments = [
        _make_segment(text="Good speech.", no_speech_prob=0.05),
        _make_segment(text="Silent part.", no_speech_prob=0.9),
    ]
    asr._model.transcribe.return_value = (iter(segments), _make_info())
    audio = np.ones(32000, dtype=np.int16) * 1000

    result = await asr.transcribe(audio)
    assert result is None

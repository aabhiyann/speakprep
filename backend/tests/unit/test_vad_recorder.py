"""Unit tests for VADRecorder."""

from __future__ import annotations

import numpy as np
import pytest
import soundfile as sf

from app.audio.vad_recorder import VADRecorder


@pytest.fixture
def recorder() -> VADRecorder:
    return VADRecorder()


@pytest.fixture
def silent_wav(tmp_path) -> str:
    """Two seconds of pure silence at 16 kHz int16."""
    audio = np.zeros(16000 * 2, dtype=np.int16)
    path = tmp_path / "silent.wav"
    sf.write(str(path), audio, 16000, subtype="PCM_16")
    return str(path)


@pytest.fixture
def mixed_wav(tmp_path) -> str:
    """One second of 400 Hz sine wave followed by one second of silence."""
    sample_rate = 16000
    t = np.linspace(0, 1.0, sample_rate, endpoint=False)
    speech_like = (np.sin(2 * np.pi * 400 * t) * 16000).astype(np.int16)
    silence = np.zeros(sample_rate, dtype=np.int16)
    audio = np.concatenate([speech_like, silence])
    path = tmp_path / "mixed.wav"
    sf.write(str(path), audio, sample_rate, subtype="PCM_16")
    return str(path)


# --- is_speech_frame ---


def test_is_speech_frame_silence_returns_false(recorder: VADRecorder) -> None:
    frame = bytes(640)  # 320 zero samples × 2 bytes = 640 bytes of silence
    assert recorder.is_speech_frame(frame) is False


def test_is_speech_frame_noise_does_not_crash(recorder: VADRecorder) -> None:
    rng = np.random.default_rng(seed=42)
    noise = rng.integers(-3000, 3001, size=320, dtype=np.int16)
    result = recorder.is_speech_frame(noise.tobytes())
    assert isinstance(result, bool)


def test_is_speech_frame_wrong_size_raises(recorder: VADRecorder) -> None:
    with pytest.raises(ValueError, match="640 bytes"):
        recorder.is_speech_frame(bytes(100))


def test_is_speech_frame_returns_bool_type(recorder: VADRecorder) -> None:
    frame = bytes(640)
    result = recorder.is_speech_frame(frame)
    assert type(result) is bool  # noqa: E721 — exact type, not isinstance


# --- collect_from_file ---


def test_collect_from_file_silent_returns_empty(
    recorder: VADRecorder, silent_wav: str
) -> None:
    segments = recorder.collect_from_file(silent_wav)
    assert segments == []


def test_collect_from_file_mixed_returns_list_of_arrays(
    recorder: VADRecorder, mixed_wav: str
) -> None:
    segments = recorder.collect_from_file(mixed_wav)
    assert isinstance(segments, list)
    for seg in segments:
        assert isinstance(seg, np.ndarray)
        assert seg.dtype == np.int16
        assert seg.ndim == 1


def test_collect_from_file_wrong_sample_rate_raises(
    recorder: VADRecorder, tmp_path
) -> None:
    audio = np.zeros(8000, dtype=np.int16)
    path = tmp_path / "wrong_rate.wav"
    sf.write(str(path), audio, 8000, subtype="PCM_16")
    with pytest.raises(ValueError, match="sample rate"):
        recorder.collect_from_file(str(path))


def test_collect_from_file_very_short_audio_returns_empty(
    recorder: VADRecorder, tmp_path
) -> None:
    """Audio shorter than one complete frame returns no segments."""
    audio = np.zeros(100, dtype=np.int16)  # less than 320 samples (one 20ms frame)
    path = tmp_path / "short.wav"
    sf.write(str(path), audio, 16000, subtype="PCM_16")
    segments = recorder.collect_from_file(str(path))
    assert segments == []

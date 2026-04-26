"""Unit tests for audio understanding helpers."""

from __future__ import annotations

import numpy as np

from app.audio.understanding import (
    audio_stats,
    float32_to_pcm,
    pcm_to_float32,
    split_into_frames,
)


def test_audio_stats_for_silence() -> None:
    audio = np.zeros(1600, dtype=np.int16)

    stats = audio_stats(audio, sample_rate=16000)

    assert stats["duration_seconds"] == 0.1
    assert stats["size_bytes"] == 3200
    assert stats["size_kb"] == 3200 / 1024
    assert stats["frame_count_20ms"] == 5
    assert stats["max_amplitude"] == 0
    assert stats["rms_amplitude"] == 0.0
    assert stats["is_likely_silence"] is True


def test_audio_stats_for_constant_signal() -> None:
    audio = np.ones(3200, dtype=np.int16) * 1000

    stats = audio_stats(audio, sample_rate=16000)

    assert stats["duration_seconds"] == 0.2
    assert stats["frame_count_20ms"] == 10
    assert stats["max_amplitude"] == 1000
    assert np.isclose(stats["rms_amplitude"], 1000.0)
    assert stats["is_likely_silence"] is False


def test_audio_stats_for_random_noise() -> None:
    rng = np.random.default_rng(seed=42)
    audio = rng.integers(-3000, 3001, size=1600, dtype=np.int16)

    stats = audio_stats(audio, sample_rate=16000)

    assert stats["duration_seconds"] == 0.1
    assert stats["size_bytes"] == audio.nbytes
    assert stats["frame_count_20ms"] == 5
    assert stats["max_amplitude"] >= 0
    assert stats["rms_amplitude"] >= 0.0


def test_pcm_to_float32_normalizes_range() -> None:
    pcm = np.array([-32768, -16384, 0, 16384, 32767], dtype=np.int16)

    normalized = pcm_to_float32(pcm)

    assert normalized.dtype == np.float32
    assert np.isclose(normalized[0], -1.0)
    assert np.isclose(normalized[2], 0.0)
    assert np.isclose(normalized[-1], 32767 / 32768)
    assert np.max(normalized) <= 1.0
    assert np.min(normalized) >= -1.0


def test_float32_to_pcm_clips_and_converts() -> None:
    floats = np.array([-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5], dtype=np.float32)

    pcm = float32_to_pcm(floats)

    assert pcm.dtype == np.int16
    assert pcm[0] == -32767
    assert pcm[1] == -32767
    assert pcm[3] == 0
    assert pcm[-2] == 32767
    assert pcm[-1] == 32767


def test_split_into_frames_drops_incomplete_tail() -> None:
    audio = np.arange(1000, dtype=np.int16)

    frames = split_into_frames(audio, frame_duration_ms=20, sample_rate=16000)

    # 20ms at 16kHz => 320 samples/frame, so 3 full frames from 1000 samples.
    assert len(frames) == 3
    assert all(frame.shape == (320,) for frame in frames)
    assert np.array_equal(frames[0], audio[:320])
    assert np.array_equal(frames[2], audio[640:960])


def test_split_into_frames_raises_for_invalid_frame_size() -> None:
    audio = np.zeros(100, dtype=np.int16)

    try:
        split_into_frames(audio, frame_duration_ms=0, sample_rate=16000)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "positive frame size" in str(exc)

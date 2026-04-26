"""Audio utility functions for PCM analysis and framing."""

from __future__ import annotations

import numpy as np


def audio_stats(audio: np.ndarray, sample_rate: int = 16000) -> dict:
    """
    Return basic metrics for an int16 PCM audio array.

    The returned dictionary includes duration, storage size, frame count for
    20ms windows, and simple amplitude-based loudness/silence indicators.
    """

    audio_int16 = np.asarray(audio, dtype=np.int16)
    sample_count = int(audio_int16.size)

    duration_seconds = sample_count / float(sample_rate) if sample_rate > 0 else 0.0
    size_bytes = int(audio_int16.nbytes)
    size_kb = size_bytes / 1024.0

    frame_size_samples = int(sample_rate * 0.02)
    frame_count_20ms = (
        sample_count // frame_size_samples if frame_size_samples > 0 else 0
    )

    if sample_count == 0:
        max_amplitude = 0
        rms_amplitude = 0.0
    else:
        int32_audio = audio_int16.astype(np.int32)
        max_amplitude = int(np.max(np.abs(int32_audio)))
        rms_amplitude = float(
            np.sqrt(np.mean(np.square(int32_audio), dtype=np.float64))
        )

    return {
        "duration_seconds": float(duration_seconds),
        "size_bytes": size_bytes,
        "size_kb": float(size_kb),
        "frame_count_20ms": int(frame_count_20ms),
        "max_amplitude": int(max_amplitude),
        "rms_amplitude": float(rms_amplitude),
        "is_likely_silence": bool(rms_amplitude < 500.0),
    }


def pcm_to_float32(audio: np.ndarray) -> np.ndarray:
    """Convert int16 PCM audio into float32 samples normalized to [-1.0, 1.0]."""

    audio_int16 = np.asarray(audio, dtype=np.int16)
    return (audio_int16.astype(np.float32) / 32768.0).astype(np.float32)


def float32_to_pcm(audio: np.ndarray) -> np.ndarray:
    """Convert float32 audio in [-1.0, 1.0] into int16 PCM samples."""

    audio_float32 = np.asarray(audio, dtype=np.float32)
    clipped = np.clip(audio_float32, -1.0, 1.0)
    return np.round(clipped * 32767.0).astype(np.int16)


def split_into_frames(
    audio: np.ndarray,
    frame_duration_ms: int = 20,
    sample_rate: int = 16000,
) -> list[np.ndarray]:
    """Split audio into fixed-duration frames and drop any trailing remainder."""

    audio_int16 = np.asarray(audio, dtype=np.int16)
    frame_size_samples = int(sample_rate * (frame_duration_ms / 1000.0))

    if frame_size_samples <= 0:
        raise ValueError(
            "frame_duration_ms and sample_rate must produce positive frame size"
        )

    complete_samples = (audio_int16.size // frame_size_samples) * frame_size_samples
    if complete_samples == 0:
        return []

    trimmed = audio_int16[:complete_samples]
    frame_count = complete_samples // frame_size_samples
    return [
        trimmed[index * frame_size_samples : (index + 1) * frame_size_samples]
        for index in range(frame_count)
    ]

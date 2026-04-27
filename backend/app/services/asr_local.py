"""Local ASR service using faster-whisper as offline fallback transcription."""

from __future__ import annotations

import asyncio
import time

import numpy as np
import structlog
from faster_whisper import WhisperModel
from pydantic import BaseModel

from app.audio.understanding import pcm_to_float32

log = structlog.get_logger(__name__)

_NO_SPEECH_THRESHOLD = 0.6
_COMPRESSION_RATIO_THRESHOLD = 2.4


class TranscriptionResult(BaseModel):
    text: str
    no_speech_prob: float
    language: str
    duration_seconds: float
    latency_ms: int


class LocalASR:
    """Offline ASR using faster-whisper (CTranslate2 INT8 quantized Whisper).

    WhisperModel is loaded once at construction — do not create per-request.
    Loading takes 10-30 seconds; inference on small CPU is ~4-5s per minute of audio.
    """

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "en",
    ) -> None:
        self.language = language
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        log.info(
            "asr_model_loaded",
            model_size=model_size,
            device=device,
            compute_type=compute_type,
        )

    def _transcribe_sync(self, audio: np.ndarray) -> TranscriptionResult | None:
        """Run faster-whisper inference synchronously.

        Called via asyncio.to_thread — must not be awaited directly.
        faster-whisper / CTranslate2 is CPU-bound and releases the GIL during
        inference, so it is safe to run in a thread pool.
        """
        if audio.size == 0:
            return None

        # faster-whisper requires float32 normalised to [-1.0, 1.0]
        audio_f32 = pcm_to_float32(audio)

        started_at = time.perf_counter()
        segments_iter, info = self._model.transcribe(
            audio_f32,
            language=self.language,
            beam_size=5,
            vad_filter=False,  # VAD is handled upstream by VADRecorder
        )
        # Materialise the generator — faster-whisper is lazy
        segments = list(segments_iter)
        latency_ms = int((time.perf_counter() - started_at) * 1000)

        if not segments:
            return None

        # Use the worst-case value across all segments so short silence bursts
        # inside an otherwise valid utterance do not mask a bad overall result.
        max_no_speech_prob = max(s.no_speech_prob for s in segments)
        max_compression_ratio = max(s.compression_ratio for s in segments)

        if max_no_speech_prob > _NO_SPEECH_THRESHOLD:
            log.info(
                "asr_filtered_no_speech", no_speech_prob=round(max_no_speech_prob, 3)
            )
            return None

        if max_compression_ratio > _COMPRESSION_RATIO_THRESHOLD:
            log.info(
                "asr_filtered_hallucination",
                compression_ratio=round(max_compression_ratio, 3),
            )
            return None

        text = " ".join(s.text.strip() for s in segments).strip()
        if not text:
            return None

        result = TranscriptionResult(
            text=text,
            no_speech_prob=max_no_speech_prob,
            language=info.language,
            duration_seconds=info.duration,
            latency_ms=latency_ms,
        )
        log.info(
            "asr_transcribed",
            transcript=text,
            no_speech_prob=round(max_no_speech_prob, 3),
            duration_seconds=round(info.duration, 2),
            latency_ms=latency_ms,
        )
        return result

    async def transcribe(self, audio: np.ndarray) -> TranscriptionResult | None:
        """Transcribe int16 PCM audio, returning None if the result is unreliable.

        Runs faster-whisper in the default thread pool so the event loop stays
        free to serve other WebSocket connections during inference.
        """
        return await asyncio.to_thread(self._transcribe_sync, audio)

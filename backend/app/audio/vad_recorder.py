"""Voice Activity Detection recorder using WebRTC VAD."""

from __future__ import annotations

import numpy as np
import soundfile as sf
import structlog
import webrtcvad

from app.audio.understanding import split_into_frames

log = structlog.get_logger(__name__)


class VADRecorder:
    """Records audio until sustained silence, using WebRTC VAD frame classification."""

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 20,
        silence_threshold_ms: int = 400,
        min_speech_ms: int = 300,
        vad_aggressiveness: int = 2,
    ) -> None:
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.silence_threshold_ms = silence_threshold_ms
        self.min_speech_ms = min_speech_ms

        self._vad = webrtcvad.Vad(vad_aggressiveness)
        self._frame_samples = frame_duration_ms * sample_rate // 1000
        self._frame_bytes = self._frame_samples * 2  # int16 = 2 bytes per sample
        self._silence_frames_needed = silence_threshold_ms // frame_duration_ms
        self._min_speech_frames = min_speech_ms // frame_duration_ms

    def is_speech_frame(self, frame: bytes) -> bool:
        """Return True if this frame contains speech.

        Frame must be exactly frame_duration_ms * sample_rate / 1000 * 2 bytes.
        At 16 kHz / 20 ms that is 640 bytes.
        """
        if len(frame) != self._frame_bytes:
            raise ValueError(
                f"Frame must be {self._frame_bytes} bytes "
                f"({self.frame_duration_ms} ms at {self.sample_rate} Hz int16), "
                f"got {len(frame)}"
            )
        return bool(self._vad.is_speech(frame, self.sample_rate))

    def record_until_silence(self) -> np.ndarray:
        """Record from the microphone until sustained silence is detected.

        Returns an int16 numpy array of the captured speech audio, or an empty
        array if fewer than min_speech_ms of speech were detected.

        Raises sounddevice.PortAudioError if no microphone is available.
        """
        import sounddevice as sd  # lazy import — needs PortAudio at runtime

        speech_frames: list[bytes] = []
        silence_count = 0
        triggered = False
        speech_frame_count = 0

        print("🎤 Listening...")

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self._frame_samples,
                dtype="int16",
                channels=1,
            ) as stream:
                while True:
                    data, _ = stream.read(self._frame_samples)
                    frame = bytes(data)
                    is_speech = self.is_speech_frame(frame)

                    if not triggered:
                        if is_speech:
                            triggered = True
                            print("🟢 Speech detected")
                            speech_frames.append(frame)
                            speech_frame_count += 1
                    else:
                        speech_frames.append(frame)
                        if is_speech:
                            silence_count = 0
                            speech_frame_count += 1
                        else:
                            silence_count += 1
                            if silence_count >= self._silence_frames_needed:
                                print("🔇 Silence")
                                break

        except sd.PortAudioError as exc:
            log.warning("microphone_not_available", error=str(exc))
            raise

        if speech_frame_count < self._min_speech_frames:
            log.info(
                "recording_too_short",
                speech_frames=speech_frame_count,
                min_required=self._min_speech_frames,
            )
            return np.zeros(0, dtype=np.int16)

        audio_bytes = b"".join(speech_frames)
        audio = np.frombuffer(audio_bytes, dtype=np.int16)

        log.info(
            "recording_complete",
            frame_count=len(speech_frames),
            duration_seconds=round(
                len(speech_frames) * self.frame_duration_ms / 1000, 3
            ),
            audio_bytes=len(audio_bytes),
        )
        return audio

    def collect_from_file(self, path: str) -> list[np.ndarray]:
        """Read a WAV file and return a list of detected speech segments.

        Each segment is a contiguous block of speech-containing frames that ends
        with at least silence_threshold_ms of silence, and spans at least
        min_speech_ms of speech frames.  Speech that extends to the end of the
        file without trailing silence is also returned.

        Raises ValueError if the file sample rate does not match self.sample_rate.
        """
        audio, file_sample_rate = sf.read(path, dtype="int16")

        if audio.ndim > 1:
            audio = audio[:, 0]  # stereo → take left channel only

        if file_sample_rate != self.sample_rate:
            raise ValueError(
                f"File sample rate {file_sample_rate} Hz does not match "
                f"expected {self.sample_rate} Hz"
            )

        frames = split_into_frames(audio, self.frame_duration_ms, self.sample_rate)
        if not frames:
            return []

        segments: list[np.ndarray] = []
        current_segment: list[np.ndarray] = []
        silence_count = 0
        triggered = False
        speech_frame_count = 0

        for frame_array in frames:
            is_speech = self.is_speech_frame(frame_array.tobytes())

            if not triggered:
                if is_speech:
                    triggered = True
                    current_segment.append(frame_array)
                    speech_frame_count += 1
            else:
                current_segment.append(frame_array)
                if is_speech:
                    silence_count = 0
                    speech_frame_count += 1
                else:
                    silence_count += 1
                    if silence_count >= self._silence_frames_needed:
                        if speech_frame_count >= self._min_speech_frames:
                            segments.append(np.concatenate(current_segment))
                        current_segment = []
                        silence_count = 0
                        triggered = False
                        speech_frame_count = 0

        # Speech that reaches end of file without trailing silence
        if triggered and speech_frame_count >= self._min_speech_frames:
            segments.append(np.concatenate(current_segment))

        log.info(
            "file_vad_complete",
            path=path,
            total_frames=len(frames),
            segments_found=len(segments),
        )
        return segments

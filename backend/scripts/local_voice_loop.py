"""Local voice loop — Phase 1 proof-of-concept: mic → ASR → LLM → TTS."""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import tempfile
import time
from collections import deque

import edge_tts
import structlog
from dotenv import load_dotenv

from app.audio.vad_recorder import VADRecorder
from app.services.asr_local import LocalASR
from app.services.llm_service import LLMService, Message

load_dotenv()

log = structlog.get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a neutral behavioral interviewer. Ask one follow-up question per turn "
    "based on what the candidate said. Keep responses under 40 words. No bullet points."
)
_TTS_VOICE = "en-US-AriaNeural"
_MAX_HISTORY = 8  # last N messages kept (excludes system prompt)


async def tts_and_play(text: str) -> float:
    """Synthesize text with edge_tts and play via afplay. Returns elapsed ms."""
    started = time.perf_counter()
    communicate = edge_tts.Communicate(text, voice=_TTS_VOICE)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    try:
        await communicate.save(tmp_path)
        subprocess.run(["afplay", tmp_path], check=True)
    finally:
        os.unlink(tmp_path)
    return (time.perf_counter() - started) * 1000


async def run_voice_loop(
    recorder: VADRecorder,
    asr: LocalASR,
    llm: LLMService,
    rounds: int,
) -> None:
    """Run the interview loop for `rounds` turns (or indefinitely if rounds < 0)."""
    history: deque[Message] = deque(maxlen=_MAX_HISTORY)
    turn = 0
    total_latency_ms = 0.0

    print("\n--- SpeakPrep local interview session started ---")
    print("Speak when you see the mic prompt. Ctrl+C to exit.\n")

    try:
        while rounds < 0 or turn < rounds:
            turn_start = time.perf_counter()

            audio = await asyncio.to_thread(recorder.record_until_silence)
            if audio.size == 0:
                print("No speech detected. Try again.")
                continue

            result = await asr.transcribe(audio)
            if result is None:
                print("Unclear speech, try again.")
                continue

            print(f"\nYou: {result.text}")
            history.append(Message(role="user", content=result.text))

            messages = [Message(role="system", content=_SYSTEM_PROMPT), *list(history)]
            response = await llm.generate(messages, max_tokens=120, temperature=0.7)

            print(f"\nInterviewer: {response.content}")
            history.append(Message(role="assistant", content=response.content))

            tts_ms = await tts_and_play(response.content)
            turn_ms = int((time.perf_counter() - turn_start) * 1000)
            total_latency_ms += turn_ms

            print(
                f"\n[Turn {turn + 1}] "
                f"ASR={result.latency_ms}ms  "
                f"LLM={response.latency_ms}ms  "
                f"TTS={tts_ms:.0f}ms  "
                f"total={turn_ms}ms"
            )
            turn += 1

    except KeyboardInterrupt:
        pass

    print("\n--- Session complete ---")
    if turn > 0:
        print(f"Turns: {turn}  |  Avg latency: {total_latency_ms / turn:.0f}ms")
    else:
        print("No turns completed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SpeakPrep local voice interview loop")
    parser.add_argument(
        "--rounds",
        type=int,
        default=-1,
        help="Number of turns before exiting (default: infinite)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="small",
        help="Whisper model size (default: small)",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    init_start = time.perf_counter()
    print("Initializing VADRecorder...")
    recorder = VADRecorder()
    print(f"Initializing LocalASR (model={args.model})...")
    asr = LocalASR(model_size=args.model)
    print("Initializing LLMService...")
    llm = LLMService()
    init_ms = int((time.perf_counter() - init_start) * 1000)
    print(f"Ready in {init_ms}ms\n")

    await run_voice_loop(recorder, asr, llm, args.rounds)


if __name__ == "__main__":
    asyncio.run(main())

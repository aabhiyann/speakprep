# SpeakPrep — Document 3: Phase-by-Phase Build Guide + Learning Curriculum
### Version 1.0 | Author: Abhiyan Sainju | April 2026

---

> **How to use this doc:** This is your daily operational guide. It tells you WHAT to do, in what ORDER, what to LEARN before doing it, and what BUGS to expect. Read the full phase before starting it. Do every deliverable checkpoint before moving to the next phase. The learning sections are non-optional — they prevent costly mistakes.

---

## TABLE OF CONTENTS

1. [How to Use This Guide](#1-how-to-use-this-guide)
2. [Phase 0: Foundations (2–3 weeks)](#2-phase-0-foundations)
3. [Phase 1: Local Voice Pipeline (3–4 weeks)](#3-phase-1-local-voice-pipeline)
4. [Phase 2: Real-Time Streaming (3–4 weeks)](#4-phase-2-real-time-streaming)
5. [Phase 3: Interview Intelligence (3–4 weeks)](#5-phase-3-interview-intelligence)
6. [Phase 4: Deploy to Production (2–3 weeks)](#6-phase-4-deploy-to-production)
7. [Phase 5: Product Layer (4–6 weeks)](#7-phase-5-product-layer)
8. [Phase 6: Hardening + Launch (3–4 weeks)](#8-phase-6-hardening--launch)
9. [Daily Development Workflow](#9-daily-development-workflow)
10. [Master Learning Resource List](#10-master-learning-resource-list)

---

## 1. How to Use This Guide

### The Four-Column Pattern

Every task in this guide follows this pattern:

**📚 LEARN FIRST** → **🔨 BUILD** → **🐛 EXPECT THESE BUGS** → **✅ DONE WHEN**

**Why learn first?** Voice AI systems have expensive failure modes. Spending 2 hours understanding asyncio saves you from 2 days debugging a blocking event loop that silently kills all connections. The learning sections are calibrated to be the minimum you need — not exhaustive tutorials.

### Tools You Need Installed Before Starting

```bash
# Required
python 3.12+          # pyenv install 3.12.3
git                   # Already installed
docker + docker compose  # docker.com/get-started
node 20+ + npm        # nvm install 20

# Recommended
pyenv                 # Python version management
poetry                # Python dependency management (vs pip)
httpie                # Better curl: pip install httpie
wscat                 # WebSocket testing: npm install -g wscat
ngrok or cloudflared  # Local tunneling for testing
vscode + extensions:  # Python, Pylance, Docker, REST Client

# Sign up for these services NOW (before Phase 0 ends)
Deepgram              # deepgram.com — get your $200 credit API key
Groq                  # console.groq.com — free API key
Supabase              # supabase.com — create a project
GitHub                # Repo for your code
Oracle Cloud          # oracle.com/cloud/free — ARM instance (takes 1-3 days)
Cloudflare            # cloudflare.com — free account + domain
Sentry                # sentry.io — free error tracking
PostHog               # posthog.com — free analytics
New Relic             # newrelic.com — free monitoring
```

### Git Discipline (Non-Negotiable from Day 1)

```bash
# Branch strategy
main        # Production only — CI/CD deploys from here
develop     # Integration branch — merge features here
feature/*   # One branch per feature

# Commit format (Conventional Commits)
feat: add WebSocket voice streaming endpoint
fix: resolve VAD triggering on background noise
chore: update Kokoro TTS Docker image version
docs: add ADR for WebSocket protocol choice
test: add integration tests for audio pipeline
refactor: extract sentence splitter to separate module

# Never commit directly to main
# Never commit secrets (use .env + .gitignore)
# Never commit auto-generated files (__pycache__, .pyc, node_modules)
```

---

## 2. Phase 0: Foundations

**Duration:** 2–3 weeks  
**Goal:** Understand the concepts before touching product code. This phase has zero product output and 100% learning output. Do not skip it.

---

### Week 1: Audio + Python Async Foundations

#### 📚 Learn: Python asyncio (3–4 hours)

asyncio is the most important concept in this entire project. If you don't understand it, you will write blocking code that silently kills all concurrent connections.

**What to study:**
1. Read: [Real Python — Async IO in Python: A Complete Walkthrough](https://realpython.com/async-io-python/) — this one article covers 80% of what you need
2. Book chapters (optional but excellent): "Python Concurrency with asyncio" by Matthew Fowler, Chapters 1–4

**Exercises — do these yourself, don't copy-paste:**

```python
# Exercise 1: Understand the difference between synchronous and async
import asyncio
import time

# WRONG — blocks the event loop
async def bad_sleep():
    time.sleep(2)  # This blocks EVERYTHING — no other coroutine can run

# RIGHT — yields control to event loop during wait
async def good_sleep():
    await asyncio.sleep(2)  # Other coroutines can run during this 2 seconds

# Exercise 2: Run two coroutines concurrently
async def task_a():
    print("Task A starting")
    await asyncio.sleep(1)
    print("Task A done")

async def task_b():
    print("Task B starting")
    await asyncio.sleep(0.5)
    print("Task B done")

async def main():
    # Sequential (bad for our use case) — takes 1.5 seconds total
    await task_a()
    await task_b()
    
    # Concurrent (good) — takes 1 second total
    await asyncio.gather(task_a(), task_b())
    
    # Create a task (fire and forget)
    task = asyncio.create_task(task_a())
    # Do other things...
    await task  # Await when you need the result

asyncio.run(main())
```

**Key questions to be able to answer before moving on:**
- What is a coroutine? How is it different from a regular function?
- What does `await` do? What happens to a coroutine when it `await`s?
- What is the difference between `await coroutine()` and `asyncio.create_task(coroutine())`?
- Why does `time.sleep()` in an async function break everything?
- What is `asyncio.gather()` and when do you use it?

> **📚 Resources:** Real Python asyncio guide, Python docs asyncio, "Python Concurrency with asyncio" Ch. 1-4

---

#### 📚 Learn: Audio Fundamentals (2–3 hours)

```python
# Exercise: Understand audio at the byte level
# Install: pip install numpy sounddevice soundfile

import numpy as np
import sounddevice as sd
import soundfile as sf

# Record 3 seconds of audio
SAMPLE_RATE = 16000   # 16,000 samples per second
DURATION = 3          # seconds
CHANNELS = 1          # mono

print("Recording...")
audio = sd.rec(
    DURATION * SAMPLE_RATE,   # Total samples: 48,000
    samplerate=SAMPLE_RATE,
    channels=CHANNELS,
    dtype='int16'             # Each sample is a signed 16-bit integer
)
sd.wait()  # Wait until recording is done
print(f"Recorded audio shape: {audio.shape}")
# → (48000, 1) — 48,000 samples, 1 channel

# What is each sample?
print(f"First 10 samples: {audio[:10, 0]}")
# → [ 123  -45  201  -88  ...] — amplitude values between -32768 and 32767

# Audio size: 
size_bytes = audio.nbytes
print(f"Audio size: {size_bytes} bytes = {size_bytes/1024:.1f} KB")
# → 96,000 bytes = 93.75 KB for 3 seconds at 16kHz 16-bit mono

# Split into 20ms frames (640 samples each)
frame_size = int(SAMPLE_RATE * 0.020)  # 320 samples = 640 bytes
frames = [audio[i:i+frame_size] for i in range(0, len(audio), frame_size)]
print(f"Number of 20ms frames: {len(frames)}")
# → 150 frames for 3 seconds

# Save and reload to understand file formats
sf.write("test.wav", audio, SAMPLE_RATE)   # WAV: raw PCM with header
sf.write("test.flac", audio, SAMPLE_RATE)  # FLAC: lossless compressed

# Check sizes
import os
wav_size = os.path.getsize("test.wav")
flac_size = os.path.getsize("test.flac")
print(f"WAV: {wav_size} bytes, FLAC: {flac_size} bytes, Ratio: {wav_size/flac_size:.1f}x")
```

**Key questions:**
- What is sample rate and why do we use 16kHz for ASR?
- Why is audio mono for ASR (not stereo)?
- What is PCM? What format does Whisper expect?
- How many bytes is 1 second of audio at 16kHz 16-bit mono?

> **📚 Resources:** Librosa tutorial, MDN Web Audio API, "The Art of Digital Audio" Ch. 1-3

---

#### 📚 Learn: WebSocket Protocol (2 hours)

```python
# Exercise: Build a basic WebSocket echo server

from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.websocket("/ws/echo")
async def echo(websocket: WebSocket):
    await websocket.accept()
    print(f"Client connected: {websocket.client}")
    
    try:
        while True:
            # Receive text or binary
            data = await websocket.receive()
            
            if "text" in data:
                print(f"Received text: {data['text']}")
                await websocket.send_text(f"Echo: {data['text']}")
            
            elif "bytes" in data:
                print(f"Received {len(data['bytes'])} bytes")
                await websocket.send_bytes(data['bytes'])  # Echo bytes back
    
    except Exception as e:
        print(f"Client disconnected: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```bash
# Test your echo server
wscat -c ws://localhost:8000/ws/echo
# Type messages and see them echoed back
```

```javascript
// Now connect from the browser (open browser console)
const ws = new WebSocket('ws://localhost:8000/ws/echo');
ws.onopen = () => ws.send('Hello from browser!');
ws.onmessage = (e) => console.log('Received:', e.data);
```

**Build until you can answer:**
- What is the HTTP → WebSocket upgrade handshake?
- What are WebSocket frames and opcodes?
- Why does the client have to mask frames?
- What is ping/pong and why do you need it?

> **📚 Resources:** MDN WebSocket API, RFC 6455, FastAPI WebSocket docs

---

### Week 2: Docker + FastAPI Foundations

#### 📚 Learn: Docker (4 hours)

```dockerfile
# Exercise: Write a Dockerfile for FastAPI from scratch

# Multi-stage build — smaller final image
FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS production
COPY app/ ./app/
EXPOSE 8000
# Don't run as root — security best practice
RUN adduser --disabled-password --no-create-home appuser
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# Exercise: docker-compose.yml with two services
version: "3.9"
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on: [db]
    networks: [app_network]
  
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes: [postgres_data:/var/lib/postgresql/data]
    networks: [app_network]

networks:
  app_network:
    driver: bridge

volumes:
  postgres_data:
```

```bash
# Commands to know
docker compose up -d          # Start all services in background
docker compose logs -f api    # Follow logs from api service
docker compose exec api bash  # Shell into running container
docker compose down -v        # Stop and remove everything including volumes
docker stats                  # Live resource usage
docker ps                     # List running containers
docker image ls               # List images
docker system prune -af       # Clean up everything unused
```

**Key questions:**
- What is a Docker layer and why does ordering in Dockerfile matter?
- What is the difference between CMD and ENTRYPOINT?
- How do services in the same docker-compose network communicate?
- What is a volume and when do you need one?
- What does `--no-cache-dir` do and why include it?

> **📚 Resources:** Docker official docs "Get Started", Docker Compose docs, "Docker Deep Dive" by Nigel Poulton

---

### Week 3: Toy Integration

#### 🔨 Build: End-to-End Toy (No Product)

Build the simplest possible voice turn — not the real pipeline, just proof that the pieces connect.

```python
# toy_voice_turn.py — Phase 0 integration exercise

import asyncio
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
from groq import AsyncGroq
import edge_tts  # Free TTS for now
import soundfile as sf

# Initialize
whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
groq_client = AsyncGroq(api_key="your-groq-key")

async def one_voice_turn():
    # Step 1: Record 5 seconds
    print("🎤 Recording for 5 seconds...")
    SAMPLE_RATE = 16000
    audio = sd.rec(5 * SAMPLE_RATE, samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    audio_flat = audio.flatten()
    
    # Step 2: Transcribe
    print("📝 Transcribing...")
    segments, info = whisper.transcribe(audio_flat, language="en")
    transcript = " ".join(s.text for s in segments).strip()
    
    if not transcript:
        print("⚠️  No speech detected")
        return
    
    print(f"   You said: '{transcript}'")
    print(f"   No-speech probability: {info.no_speech_prob:.2f}")
    
    # Step 3: LLM
    print("🤖 Getting AI response...")
    response = await groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an interview coach. Keep responses under 2 sentences."},
            {"role": "user", "content": transcript}
        ]
    )
    ai_response = response.choices[0].message.content
    print(f"   AI says: '{ai_response}'")
    
    # Step 4: TTS
    print("🔊 Synthesizing speech...")
    communicate = edge_tts.Communicate(ai_response, voice="en-US-AriaNeural")
    await communicate.save("response.mp3")
    
    # Step 5: Play
    data, sr = sf.read("response.mp3")
    sd.play(data, sr)
    sd.wait()
    print("✅ Turn complete")

asyncio.run(one_voice_turn())
```

**🐛 Bugs You Will Hit:**

1. **Whisper hallucinating.** During silence, Whisper outputs text. Fix: check `info.no_speech_prob > 0.6` and skip transcription. You'll see this immediately on the first run.

2. **Audio format mismatch.** Whisper's transcribe method accepts either a file path or a numpy float32 array. If you pass int16, you'll get garbled results. Fix: explicitly convert or use `dtype='float32'` in `sd.rec()`.

3. **edge_tts network dependency.** Edge-TTS calls Microsoft's servers. If offline or behind a VPN, it fails silently. Fix: check internet connection, or use pyttsx3 as offline fallback.

4. **Groq model name changes.** Model strings evolve. Always check [console.groq.com/docs/models](https://console.groq.com/docs/models) for current model IDs.

5. **sounddevice PortAudio not found.** On Linux: `sudo apt-get install portaudio19-dev`. On Mac: `brew install portaudio`.

**✅ Done When:**
- [ ] Can run one complete voice turn end-to-end
- [ ] Can explain what each step does and why
- [ ] Have measured latency for each step (add `time.time()` before/after each)
- [ ] Committed to git with proper conventional commits
- [ ] Have a `README.md` explaining how to run it

---

## 3. Phase 1: Local Voice Pipeline

**Duration:** 3–4 weeks  
**Goal:** Voice in → voice out, end-to-end, on your laptop. Sequential (no streaming). Adding VAD and proper error handling.

---

### Week 4–5: VAD + Proper Pipeline

#### 📚 Learn: VAD Concepts (2 hours)

Before adding VAD, understand why fixed-time recording is wrong:

```python
# The problem with fixed-time recording
audio = sd.rec(5 * 16000)  # Always records exactly 5 seconds
# If user speaks for 1 second → we wait 4 more seconds of silence
# If user speaks for 7 seconds → we cut them off at 5 seconds
# This adds 0–4 seconds of unnecessary latency
```

**Read:** [Silero VAD README](https://github.com/snakers4/silero-vad) — especially the examples section  
**Read:** [webrtcvad GitHub](https://github.com/wiseman/py-webrtcvad) — the README is excellent

#### 🔨 Build: VAD-Triggered Recording

```python
# vad_recorder.py

import webrtcvad
import sounddevice as sd
import numpy as np
import collections
import time

class VADRecorder:
    """
    Records audio and stops when sustained silence is detected.
    Uses WebRTC VAD for speech/silence classification.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration_ms: int = 20,    # 20ms frames
        silence_threshold_ms: int = 500, # Stop after 500ms silence
        min_speech_ms: int = 300,        # Require 300ms of speech minimum
        vad_aggressiveness: int = 2,     # 0-3, higher = more aggressive filtering
    ):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)  # 320 samples
        self.silence_frames_needed = silence_threshold_ms // frame_duration_ms  # 25 frames
        self.min_speech_frames = min_speech_ms // frame_duration_ms  # 15 frames
        self.vad = webrtcvad.Vad(vad_aggressiveness)
    
    def record_until_silence(self) -> np.ndarray:
        """Record audio until 500ms of sustained silence after speech."""
        
        speech_frames = []
        silence_window = collections.deque(maxlen=self.silence_frames_needed)
        has_speech = False
        
        print("🎤 Listening... (speak now)")
        
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=self.frame_size
        ) as stream:
            
            while True:
                frame_bytes, _ = stream.read(self.frame_size)
                is_speech = self.vad.is_speech(bytes(frame_bytes), self.sample_rate)
                
                if is_speech:
                    if not has_speech:
                        print("🟢 Speech detected")
                    has_speech = True
                    speech_frames.append(np.frombuffer(frame_bytes, dtype=np.int16))
                    silence_window.clear()
                
                elif has_speech:
                    speech_frames.append(np.frombuffer(frame_bytes, dtype=np.int16))
                    silence_window.append(False)
                    
                    if len(silence_window) == silence_window.maxlen:
                        # Full window of silence — speech is done
                        print(f"🔇 Silence detected, stopping. Speech frames: {len(speech_frames)}")
                        break
        
        if len(speech_frames) < self.min_speech_frames:
            print("⚠️  Audio too short — likely noise, not speech")
            return np.array([], dtype=np.int16)
        
        audio = np.concatenate(speech_frames)
        duration_sec = len(audio) / self.sample_rate
        print(f"   Recorded {duration_sec:.1f}s of audio ({audio.nbytes} bytes)")
        return audio
```

#### 🔨 Build: Full Local Pipeline v1

```python
# speakprep_local.py — Phase 1 complete pipeline

import asyncio
import time
import numpy as np
from dataclasses import dataclass
from typing import Optional
from faster_whisper import WhisperModel
from groq import AsyncGroq
import edge_tts
import sounddevice as sd
import soundfile as sf
import tempfile
import os

# Initialize models (do this ONCE at startup — not per turn)
print("Loading models...")
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")
groq_client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
recorder = VADRecorder()

@dataclass
class TurnResult:
    transcript: str
    ai_response: str
    asr_latency_ms: int
    llm_latency_ms: int
    tts_latency_ms: int
    total_latency_ms: int
    no_speech_prob: float

async def transcribe(audio: np.ndarray) -> tuple[str, float]:
    """ASR: audio numpy array → text transcript."""
    t0 = time.monotonic()
    
    # Convert int16 to float32 (Whisper requirement)
    audio_f32 = audio.astype(np.float32) / 32768.0
    
    segments, info = whisper_model.transcribe(
        audio_f32,
        language="en",
        vad_filter=True,         # Additional VAD inside Whisper
        vad_parameters=dict(
            min_silence_duration_ms=300,
            threshold=0.5
        ),
        no_speech_threshold=0.6  # Skip if likely not speech
    )
    
    transcript = " ".join(s.text for s in segments).strip()
    latency_ms = int((time.monotonic() - t0) * 1000)
    
    print(f"   ASR: '{transcript}' ({latency_ms}ms, no_speech: {info.no_speech_prob:.2f})")
    return transcript, info.no_speech_prob

async def generate_response(
    transcript: str, 
    conversation_history: list
) -> tuple[str, int]:
    """LLM: transcript → AI response."""
    t0 = time.monotonic()
    
    messages = [
        {
            "role": "system",
            "content": """You are Sam, a neutral interviewer practicing behavioral interviews. 
            Ask one follow-up question or brief feedback per turn.
            Keep responses under 40 words. Speak conversationally, no bullet points."""
        }
    ] + conversation_history + [
        {"role": "user", "content": transcript}
    ]
    
    response = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=100,
        temperature=0.7
    )
    
    ai_response = response.choices[0].message.content
    latency_ms = int((time.monotonic() - t0) * 1000)
    
    print(f"   LLM: '{ai_response}' ({latency_ms}ms)")
    return ai_response, latency_ms

async def synthesize_and_play(text: str) -> int:
    """TTS: text → speech."""
    t0 = time.monotonic()
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        output_path = f.name
    
    try:
        communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural", rate="+10%")
        await communicate.save(output_path)
        
        data, sr = sf.read(output_path)
        latency_ms = int((time.monotonic() - t0) * 1000)
        
        sd.play(data, sr)
        sd.wait()
        
        return latency_ms
    finally:
        os.unlink(output_path)

async def run_interview_session():
    """Main interview loop."""
    conversation_history = []
    
    print("\n" + "="*60)
    print("SpeakPrep — Behavioral Interview Practice")
    print("="*60)
    print("Press Ctrl+C to end the session\n")
    
    turn_count = 0
    
    while True:
        turn_count += 1
        t_turn_start = time.monotonic()
        
        print(f"\n--- Turn {turn_count} ---")
        
        # Step 1: Record
        audio = recorder.record_until_silence()
        if len(audio) == 0:
            print("No speech detected, listening again...")
            continue
        
        # Step 2: Transcribe
        transcript, no_speech_prob = await transcribe(audio)
        
        if no_speech_prob > 0.6 or not transcript:
            print("Speech unclear, please try again")
            continue
        
        # Step 3: Generate response
        ai_response, llm_ms = await generate_response(transcript, conversation_history)
        
        # Step 4: Play response
        tts_ms = await synthesize_and_play(ai_response)
        
        # Update conversation history
        conversation_history.append({"role": "user", "content": transcript})
        conversation_history.append({"role": "assistant", "content": ai_response})
        
        # Keep last 10 turns only
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        # Log latencies
        total_ms = int((time.monotonic() - t_turn_start) * 1000)
        print(f"\n   ⏱️  Total turn latency: {total_ms}ms")

if __name__ == "__main__":
    try:
        asyncio.run(run_interview_session())
    except KeyboardInterrupt:
        print("\n\nSession ended. Great practice!")
```

**🐛 Bugs You Will Hit in Phase 1:**

1. **VAD mode 3 clips sentence endings.** You'll notice the AI responding before you finish your sentence. Fix: use mode 2, increase silence threshold to 600ms.

2. **Whisper vad_filter conflicts with external VAD.** If you use both webrtcvad AND Whisper's internal VAD filter, they sometimes fight. Fix: either use one or the other. Use Silero VAD externally, disable Whisper's internal vad_filter.

3. **Model loading takes 10–30 seconds.** Never initialize WhisperModel inside a loop. Initialize once at module level.

4. **int16 vs float32 confusion.** sounddevice gives int16 by default. Whisper.transcribe() needs float32. Never forget to divide by 32768.0.

5. **Groq returning truncated responses.** If `max_tokens` is too low, the LLM cuts off mid-sentence. Set to at least 150 for interview use cases.

6. **edge_tts adds delay proportional to text length.** For 40-word responses, edge_tts takes 2–3 seconds to generate. This is why we switch to Kokoro in Phase 2.

**✅ Done When:**
- [ ] Full voice loop working: speak → hear response
- [ ] VAD correctly stops recording after silence (not fixed time)
- [ ] Latency logged for each step in every turn
- [ ] Conversation history maintained correctly across 10+ turns
- [ ] No-speech filtering works (silence doesn't generate response)
- [ ] Committed with clear commit history

---

## 4. Phase 2: Real-Time Streaming

**Duration:** 3–4 weeks  
**Goal:** WebSocket-based streaming. Audio streams in, response streams back. Kokoro TTS replaces edge_tts. Deepgram replaces Faster-Whisper for primary ASR.

---

### Week 7–8: WebSocket Server + Deepgram Streaming

#### 📚 Learn: FastAPI WebSockets + asyncio.Queue (3 hours)

```python
# Learn: asyncio.Queue for producer-consumer pattern
# This is the core pattern for the audio pipeline

import asyncio

async def audio_producer(queue: asyncio.Queue):
    """Simulates receiving audio chunks from WebSocket."""
    for i in range(10):
        await asyncio.sleep(0.02)  # 20ms interval
        chunk = bytes(640)  # Fake 20ms audio frame
        await queue.put(chunk)
    await queue.put(None)  # Sentinel: no more audio

async def audio_consumer(queue: asyncio.Queue):
    """Simulates processing audio chunks."""
    buffer = bytearray()
    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        buffer.extend(chunk)
        # Process when buffer is large enough
        if len(buffer) >= 32000:  # 1 second of audio
            print(f"Processing {len(buffer)} bytes")
            buffer.clear()

async def main():
    queue = asyncio.Queue(maxsize=100)  # Bounded queue — backpressure
    await asyncio.gather(
        audio_producer(queue),
        audio_consumer(queue)
    )

asyncio.run(main())
```

#### 🔨 Build: WebSocket Voice Endpoint

```python
# app/main.py — FastAPI application with WebSocket

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time
import uuid
import os
from collections import deque

app = FastAPI(title="SpeakPrep API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.speakprep.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.websocket("/ws/voice/{session_id}")
async def voice_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # Session state
    audio_buffer = bytearray()
    conversation_history = []
    turn_count = 0
    is_ai_speaking = False
    
    try:
        # Auth check (simplified for Phase 2)
        try:
            auth = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)
            # In Phase 2: just check if token field exists
            # Real auth added in Phase 5
            if "token" not in auth:
                await websocket.close(code=4001)
                return
        except asyncio.TimeoutError:
            await websocket.close(code=4002)
            return
        
        await websocket.send_json({"type": "session_ready", "session_id": session_id})
        
        # Send opening question
        opening = "Welcome to your mock interview. I'm your interviewer today. Could you start by telling me about yourself and why you're interested in this role?"
        await send_tts_response(websocket, opening)
        
        # Main loop
        async for message in websocket.iter_bytes():
            if is_ai_speaking:
                # Barge-in detected — user spoke while AI was talking
                is_ai_speaking = False
                await websocket.send_json({"type": "barge_in_acknowledged"})
                audio_buffer.clear()
            
            audio_buffer.extend(message)
            
            # Check for end of utterance
            # In Phase 2: simple size-based check
            # In Phase 3: proper VAD
            if len(audio_buffer) > 32000:  # ~1 second of audio
                turn_count += 1
                t_start = time.monotonic()
                
                audio_data = bytes(audio_buffer)
                audio_buffer.clear()
                
                # Transcribe
                transcript = await transcribe_audio(audio_data)
                
                if transcript:
                    await websocket.send_json({
                        "type": "transcript",
                        "text": transcript,
                        "is_final": True
                    })
                    
                    # Generate + stream response
                    is_ai_speaking = True
                    await stream_response(
                        websocket, 
                        transcript, 
                        conversation_history,
                        session_id,
                        turn_count,
                        t_start
                    )
                    is_ai_speaking = False
                    
                    # Update history
                    conversation_history.append({"role": "user", "content": transcript})
    
    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
    except Exception as e:
        print(f"Error in session {session_id}: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})

async def transcribe_audio(audio_data: bytes) -> str:
    """Transcribe audio using Deepgram (or Whisper fallback)."""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen",
                headers={
                    "Authorization": f"Token {os.environ['DEEPGRAM_API_KEY']}",
                    "Content-Type": "audio/raw;encoding=linear16;sample_rate=16000;channels=1"
                },
                content=audio_data,
                params={
                    "model": "nova-3",
                    "language": "en",
                    "smart_format": "true"
                },
                timeout=10.0
            )
            
            result = response.json()
            return result["results"]["channels"][0]["alternatives"][0]["transcript"]
    
    except Exception as e:
        print(f"Deepgram failed, using Whisper: {e}")
        return await transcribe_with_whisper(audio_data)

async def stream_response(
    websocket: WebSocket,
    transcript: str,
    conversation_history: list,
    session_id: str,
    turn_number: int,
    t_start: float
):
    """Generate LLM response and stream TTS audio as it arrives."""
    from groq import AsyncGroq
    
    client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    
    messages = get_interview_messages(transcript, conversation_history)
    
    sentence_buffer = ""
    full_response = ""
    llm_ttft_ms = None
    tts_sequence = 0
    
    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        stream=True,
        max_tokens=150,
        temperature=0.7
    )
    
    async for chunk in stream:
        token = chunk.choices[0].delta.content
        if not token:
            continue
        
        if llm_ttft_ms is None:
            llm_ttft_ms = int((time.monotonic() - t_start) * 1000)
        
        # Stream token to client for display
        await websocket.send_json({"type": "llm_token", "token": token})
        
        sentence_buffer += token
        full_response += token
        
        # Check for sentence boundary
        if any(sentence_buffer.endswith(end) for end in ['. ', '! ', '? ', '.\n', '!\n']):
            sentence = sentence_buffer.strip()
            sentence_buffer = ""
            
            if sentence:
                # Synthesize and send this sentence
                await synthesize_and_send(websocket, sentence, tts_sequence)
                tts_sequence += 1
    
    # Handle remaining text
    if sentence_buffer.strip():
        await synthesize_and_send(websocket, sentence_buffer.strip(), tts_sequence)
    
    total_ms = int((time.monotonic() - t_start) * 1000)
    await websocket.send_json({
        "type": "turn_complete",
        "turn_id": str(uuid.uuid4()),
        "latencies": {
            "llm_ttft_ms": llm_ttft_ms,
            "total_ms": total_ms
        }
    })

async def synthesize_and_send(websocket: WebSocket, text: str, sequence: int):
    """Synthesize one sentence and stream audio chunks to client."""
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            # Call Kokoro TTS (running locally in Docker)
            async with client.stream(
                "POST",
                "http://kokoro:8880/v1/audio/speech",
                json={
                    "model": "kokoro",
                    "input": text,
                    "voice": "af_heart",
                    "response_format": "pcm"  # Raw PCM for lowest latency
                }
            ) as response:
                # Stream audio chunks to browser
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    # Prepend sequence number for client-side ordering
                    header = sequence.to_bytes(4, 'big')
                    await websocket.send_bytes(header + chunk)
    
    except Exception as e:
        print(f"TTS failed for '{text}': {e}")
```

#### 🔨 Build: Simple Browser Client

```html
<!-- index.html — Phase 2 test client -->
<!DOCTYPE html>
<html>
<head>
    <title>SpeakPrep - Test Client</title>
</head>
<body>
    <h1>SpeakPrep Voice Test</h1>
    <button id="connect">Connect</button>
    <button id="startTalk" disabled>🎤 Hold to Talk</button>
    <div id="transcript"></div>
    <div id="ai-response"></div>
    <div id="latency"></div>

    <script>
    let ws;
    let mediaRecorder;
    let audioContext;
    let audioQueue = [];
    let isPlaying = false;

    document.getElementById('connect').onclick = async () => {
        const sessionId = crypto.randomUUID();
        ws = new WebSocket(`ws://localhost:8000/ws/voice/${sessionId}`);
        
        ws.onopen = () => {
            // Send auth (simplified for Phase 2)
            ws.send(JSON.stringify({ type: "auth", token: "dev-token" }));
            document.getElementById('startTalk').disabled = false;
        };
        
        ws.onmessage = async (event) => {
            if (typeof event.data === 'string') {
                const msg = JSON.parse(event.data);
                
                if (msg.type === 'transcript') {
                    document.getElementById('transcript').textContent = `You: ${msg.text}`;
                }
                if (msg.type === 'llm_token') {
                    document.getElementById('ai-response').textContent += msg.token;
                }
                if (msg.type === 'turn_complete') {
                    document.getElementById('latency').textContent = 
                        `Latency: ${msg.latencies.total_ms}ms`;
                    document.getElementById('ai-response').textContent = '';
                }
            
            } else {
                // Binary = audio chunk — add to playback queue
                const arrayBuffer = await event.data.arrayBuffer();
                const sequence = new DataView(arrayBuffer).getUint32(0);
                const audioData = arrayBuffer.slice(4);
                
                audioQueue.push({ sequence, audioData });
                audioQueue.sort((a, b) => a.sequence - b.sequence);
                
                if (!isPlaying) playNextChunk();
            }
        };
    };

    async function playNextChunk() {
        if (audioQueue.length === 0) {
            isPlaying = false;
            return;
        }
        
        isPlaying = true;
        const { audioData } = audioQueue.shift();
        
        if (!audioContext) audioContext = new AudioContext({ sampleRate: 24000 });
        
        // Decode PCM audio (from Kokoro at 24kHz, 32-bit float)
        const float32 = new Float32Array(audioData);
        const buffer = audioContext.createBuffer(1, float32.length, 24000);
        buffer.copyToChannel(float32, 0);
        
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.onended = playNextChunk;
        source.start();
    }

    // Push-to-talk
    const talkBtn = document.getElementById('startTalk');
    
    talkBtn.addEventListener('mousedown', async () => {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: { sampleRate: 16000, channelCount: 1 } 
        });
        
        // Use Web Audio API for raw PCM capture
        audioContext = audioContext || new AudioContext({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(320, 1, 1);
        
        processor.onaudioprocess = (event) => {
            const float32 = event.inputBuffer.getChannelData(0);
            // Convert to Int16
            const int16 = new Int16Array(float32.length);
            for (let i = 0; i < float32.length; i++) {
                int16[i] = Math.max(-32768, Math.min(32767, float32[i] * 32768));
            }
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(int16.buffer);
            }
        };
        
        source.connect(processor);
        processor.connect(audioContext.destination);
        
        talkBtn.dataset.stream = stream;
        talkBtn.dataset.source = source;
        talkBtn.dataset.processor = processor;
    });
    
    talkBtn.addEventListener('mouseup', () => {
        // Signal end of audio
        if (ws) ws.send(JSON.stringify({ type: "audio_end" }));
        // Stop recording
        const stream = talkBtn.dataset.stream;
        if (stream) stream.getTracks().forEach(t => t.stop());
    });
    </script>
</body>
</html>
```

**🐛 Bugs You Will Hit in Phase 2:**

1. **CORS errors on WebSocket.** WebSocket doesn't technically have CORS, but if your JS fetch calls fail, add CORS middleware. WebSocket itself is not blocked by CORS.

2. **AudioContext suspended by browser.** Browsers require a user gesture before AudioContext can play audio. Fix: always create AudioContext inside a user event handler (button click), not at page load.

3. **Audio chunks playing out of order.** Sentence 1 and Sentence 2 TTS generate concurrently. Sentence 2 might arrive before Sentence 1. Fix: sequence numbering + client-side sort queue.

4. **Kokoro not reachable.** If running backend without Docker, Kokoro isn't at `http://kokoro:8880`. Use `http://localhost:8880` in dev, `http://kokoro:8880` in Docker. Use environment variable.

5. **Groq returning empty responses.** Sometimes the streaming API returns a chunk with empty delta.content. Always check `if not token: continue`.

6. **WebSocket staying open after page close.** Browser closes the connection with code 1001 (Going Away). Handle `WebSocketDisconnect` in FastAPI and clean up session state.

**✅ Done When:**
- [ ] WebSocket connection established and maintained throughout 15-minute session
- [ ] Audio streams from browser to server in real-time
- [ ] Transcript appears while AI is generating response
- [ ] AI audio plays back sentence by sentence (not waiting for full response)
- [ ] Barge-in interrupts AI response playback
- [ ] Latency metrics in `turn_complete` message
- [ ] Working in Chrome, Firefox, and Safari (test all three!)

---

## 5. Phase 3: Interview Intelligence

**Duration:** 3–4 weeks  
**Goal:** Add the product layer — resume parsing, question bank, intelligent probing, scoring.

---

### Week 10–11: Resume Parsing + Question Bank

#### 🔨 Build: Resume Parser

```python
# app/services/resume_parser.py

import pymupdf  # pip install pymupdf
from pydantic import BaseModel
from typing import Optional
from groq import AsyncGroq
import json
import os

class WorkExperience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: Optional[str]  # None if current
    description: str
    highlights: list[str]

class ResumeData(BaseModel):
    name: str
    email: Optional[str]
    work_experience: list[WorkExperience]
    education: list[dict]
    skills: list[str]
    projects: list[dict]
    years_of_experience: float

async def parse_resume(pdf_bytes: bytes) -> ResumeData:
    """Extract structured data from a resume PDF."""
    
    # Step 1: Extract text from PDF
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    if len(text.strip()) < 100:
        # PDF might be image-based — try OCR
        raise ValueError("PDF appears to be image-based. OCR not yet supported.")
    
    # Step 2: Parse with LLM (structured output)
    client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    
    prompt = f"""Extract information from this resume and return ONLY valid JSON.
    
Resume text:
{text[:4000]}  # Limit to avoid token overflow

Return this exact JSON structure (no markdown, no explanation):
{{
  "name": "Full Name",
  "email": "email@example.com or null",
  "work_experience": [
    {{
      "company": "Company Name",
      "title": "Job Title", 
      "start_date": "Month YYYY",
      "end_date": "Month YYYY or null if current",
      "description": "Brief role description",
      "highlights": ["Achievement 1", "Achievement 2"]
    }}
  ],
  "education": [
    {{"institution": "University", "degree": "MS Computer Science", "year": "2025"}}
  ],
  "skills": ["Python", "React", "PostgreSQL"],
  "projects": [
    {{"name": "Project Name", "description": "Brief description", "tech": ["stack"]}}
  ],
  "years_of_experience": 2.5
}}"""
    
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,           # Deterministic for parsing
        max_tokens=2000
    )
    
    json_str = response.choices[0].message.content.strip()
    
    # Handle if LLM wraps in markdown
    if json_str.startswith("```"):
        json_str = json_str.split("```")[1]
        if json_str.startswith("json"):
            json_str = json_str[4:]
    
    parsed = json.loads(json_str)
    return ResumeData(**parsed)
```

#### 🔨 Build: Question Selector with ELO

```python
# app/services/question_selector.py

import math
from sqlalchemy import select, func
from app.models import Question, UserQuestionHistory, UserEloRating
from app.database import async_session

class QuestionSelector:
    
    TARGET_SUCCESS_RATE = 0.67  # "Zone of proximal development"
    
    async def select_question(
        self,
        user_id: str,
        category: str,
        user_elo: float,
        recent_question_ids: list[str]
    ) -> Question:
        """Select the best next question for this user."""
        
        async with async_session() as session:
            # Get candidate questions
            query = (
                select(Question)
                .where(Question.category == category)
                .where(Question.is_active == True)
                .where(Question.id.not_in(recent_question_ids))
                # Select questions where user's expected success = 67%
                # ELO formula: expected_score = 1 / (1 + 10^((q_elo - u_elo)/400))
                # We want expected_score = 0.67
                # Solving: q_elo ≈ u_elo - 170 (ideal question difficulty)
                .order_by(
                    func.abs(Question.elo_rating - (user_elo - 170))
                )
                .limit(10)
            )
            
            result = await session.execute(query)
            candidates = result.scalars().all()
            
            if not candidates:
                # Fallback: any active question in category
                result = await session.execute(
                    select(Question)
                    .where(Question.category == category)
                    .where(Question.is_active == True)
                    .order_by(func.random())
                    .limit(1)
                )
                return result.scalar_one()
            
            # Add some randomness — don't always pick #1 match
            import random
            weights = [1.0 / (i + 1) for i in range(len(candidates))]  # Higher weight for better match
            selected = random.choices(candidates, weights=weights, k=1)[0]
            return selected
    
    def update_elo(
        self,
        user_elo: float,
        question_elo: float,
        user_score: float,  # Normalized 0.0–1.0
        k_factor: int = 32
    ) -> tuple[float, float]:
        """
        Update ELO ratings after an interaction.
        Returns (new_user_elo, new_question_elo)
        """
        # Expected score based on ELO difference
        expected = 1 / (1 + 10 ** ((question_elo - user_elo) / 400))
        
        # Update
        new_user_elo = user_elo + k_factor * (user_score - expected)
        new_question_elo = question_elo + k_factor * (expected - user_score)  # Inverse
        
        # Clamp to reasonable range
        new_user_elo = max(600, min(2400, new_user_elo))
        new_question_elo = max(600, min(2400, new_question_elo))
        
        return new_user_elo, new_question_elo
```

#### 🔨 Build: AI Scoring System

```python
# app/services/scorer.py

from groq import AsyncGroq
from pydantic import BaseModel
import os
import json

class TurnScores(BaseModel):
    content_score: float       # 1.0-5.0
    communication_score: float
    star_score: float
    confidence_score: float
    filler_score: float
    overall_score: float       # Weighted average
    
    # Qualitative feedback
    strengths: list[str]
    improvements: list[str]
    example_better_answer: str
    
    # STAR analysis
    has_situation: bool
    has_task: bool
    has_action: bool
    has_result: bool

async def score_turn(
    user_transcript: str,
    question_text: str,
    question_type: str = "behavioral"
) -> TurnScores:
    """Score a user's interview answer using LLM."""
    
    client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])
    
    scoring_prompt = f"""
You are an expert interview coach. Score this candidate's answer.

QUESTION: {question_text}

CANDIDATE'S ANSWER: {user_transcript}

Return ONLY valid JSON with this exact structure:

{{
  "content_score": <1.0-5.0>,
  "communication_score": <1.0-5.0>,
  "star_score": <1.0-5.0>,
  "confidence_score": <1.0-5.0>,
  "filler_score": <1.0-5.0>,
  "overall_score": <1.0-5.0>,
  "has_situation": <true/false>,
  "has_task": <true/false>,
  "has_action": <true/false>,
  "has_result": <true/false>,
  "strengths": ["specific strength 1", "specific strength 2"],
  "improvements": ["specific improvement 1", "specific improvement 2"],
  "example_better_answer": "A better version of this answer would be..."
}}

SCORING RUBRICS:
Content Score (1-5):
  5: Directly answers the question with specific details, quantified results, clear impact
  4: Good answer with mostly specific details, minor gaps
  3: Adequate but lacks specificity or depth
  2: Partially relevant, significant gaps
  1: Off-topic, no clear connection to question

STAR Score (1-5):
  5: All four STAR components present with specifics
  3: 3 components present, missing one
  1: Vague story with no clear structure

Communication (1-5):
  5: Crystal clear, logical flow, concise
  3: Some meandering but comprehensible
  1: Very difficult to follow

Confidence (1-5) - Look for: 
  - Hedging: "I think", "maybe", "sort of", "kind of" → low score
  - Assertive: "I decided", "I led", "I built" → high score

Filler Words (1-5):
  5: 0-1 per minute
  4: 2-3 per minute
  3: 4-6 per minute
  1: 10+ per minute
"""
    
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": scoring_prompt}],
        temperature=0,  # Deterministic scoring
        max_tokens=600
    )
    
    json_str = response.choices[0].message.content.strip()
    # Clean markdown if present
    if "```" in json_str:
        json_str = json_str.split("```")[1].lstrip("json").strip()
    
    scores_dict = json.loads(json_str)
    
    # Calculate weighted overall score
    weights = {
        "content_score": 0.30,
        "communication_score": 0.25,
        "star_score": 0.20,
        "confidence_score": 0.15,
        "filler_score": 0.10
    }
    
    scores_dict["overall_score"] = sum(
        scores_dict[k] * w for k, w in weights.items()
    )
    
    return TurnScores(**scores_dict)
```

**✅ Phase 3 Done When:**
- [ ] Resume parsing extracts experience, skills, projects correctly (test with 10 different resumes)
- [ ] System prompt uses resume data to personalize questions
- [ ] AI asks follow-up questions based on actual answer content (not scripted)
- [ ] Score generated for each turn (runs async, doesn't block conversation)
- [ ] ELO updates after each scored turn
- [ ] Question selector avoids recently-asked questions

---

## 6. Phase 4: Deploy to Production

**Duration:** 2–3 weeks  
**Goal:** Running on Oracle Cloud ARM. Real URL. HTTPS. CI/CD. Monitoring.

### Steps in Order

1. **Provision Oracle Cloud ARM instance**
   ```bash
   # After signing up at oracle.com/cloud/free
   # Create VM.Standard.A1.Flex (ARM Ampere)
   # Shape: 4 OCPU, 24 GB RAM, Ubuntu 22.04
   # Add your SSH public key
   # Set security list: allow TCP 22, 80, 443 inbound
   ```

2. **Initial server setup**
   ```bash
   ssh ubuntu@YOUR_ORACLE_IP
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Docker
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker ubuntu
   # Log out and back in
   
   # Install Docker Compose v2
   sudo apt install docker-compose-plugin
   
   # Install cloudflared
   curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 \
     -o /usr/local/bin/cloudflared
   chmod +x /usr/local/bin/cloudflared
   
   # Create app directory
   mkdir ~/speakprep && cd ~/speakprep
   ```

3. **Set up Cloudflare Tunnel**
   ```bash
   # On server
   cloudflared login
   cloudflared tunnel create speakprep
   cloudflared tunnel route dns speakprep api.speakprep.com
   
   # Create config
   cat > ~/.cloudflared/config.yml << EOF
   tunnel: YOUR_TUNNEL_ID
   credentials-file: /home/ubuntu/.cloudflared/YOUR_TUNNEL_ID.json
   
   ingress:
     - hostname: api.speakprep.com
       service: http://localhost:80
     - service: http_status:404
   EOF
   
   # Install as system service
   sudo cloudflared service install
   sudo systemctl enable cloudflared
   sudo systemctl start cloudflared
   ```

4. **Deploy with Docker Compose**
   ```bash
   # Clone your repo
   git clone https://github.com/yourusername/speakprep.git
   cd speakprep
   
   # Create .env file (NEVER commit this)
   cat > .env << EOF
   DATABASE_URL=postgresql://...
   GROQ_API_KEY=gsk_...
   DEEPGRAM_API_KEY=...
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   SENTRY_DSN=...
   NEW_RELIC_LICENSE_KEY=...
   EOF
   
   # Start everything
   docker compose -f docker-compose.prod.yml up -d
   
   # Check logs
   docker compose logs -f app
   
   # Verify health
   curl http://localhost:8000/api/health
   ```

5. **Run database migrations**
   ```bash
   docker compose exec app alembic upgrade head
   ```

6. **Set up monitoring**
   ```bash
   # New Relic: add NEW_RELIC_LICENSE_KEY to .env
   # New Relic agent auto-instruments FastAPI via the Docker image
   
   # Uptime monitoring (free):
   # Go to uptimerobot.com → add monitor → HTTP → https://api.speakprep.com/api/health
   # Set alert threshold: 1 minute
   # Add email + Slack webhook
   ```

**🐛 Bugs You Will Hit in Phase 4:**

1. **Oracle ARM capacity errors.** "Out of capacity for shape VM.Standard.A1.Flex." Fix: try different regions (us-ashburn-1, eu-frankfurt-1, ap-sydney-1). Retry at off-peak hours. Upgrade to Pay-As-You-Go (free, just needs credit card).

2. **Docker ARM64 images don't exist.** Some images on Docker Hub are x86-only. Check for `:latest-arm64` or `:arm64` tags. Build from source if needed: `docker buildx build --platform linux/arm64`.

3. **Kokoro model download takes 20+ minutes on first start.** It downloads on first container start. Add a volume mount to persist models: `kokoro_models:/app/models`. After first download, subsequent starts are instant.

4. **Cloudflare Tunnel drops WebSocket connections.** Cloudflare free plan has a 100-second timeout on WebSocket. Fix: enable WebSocket keepalive in your Caddy config. Or use Cloudflare's enterprise plan (not needed for Phase 1).

5. **GitHub Actions ARM64 builds take 20+ minutes.** QEMU emulation is slow. Use `docker/setup-qemu-action` with `--platform linux/arm64`. Or build on Oracle directly and push from there.

**✅ Done When:**
- [ ] App accessible at https://api.yourdomain.com/api/health
- [ ] WebSocket voice session works from browser to production server
- [ ] CI/CD auto-deploys on push to main
- [ ] New Relic showing latency metrics
- [ ] UptimeRobot monitoring enabled with alerts
- [ ] Zero-downtime deployment tested (push a change, verify no dropped sessions)

---

## 7. Phase 5: Product Layer

**Duration:** 4–6 weeks  
**Goal:** Full user-facing product. Authentication, dashboard, post-session reports, progress tracking.

### Features to Build in Order

1. **Auth system** (Supabase Auth) — 1 week
2. **Session management + turn persistence** — 1 week
3. **Post-session scoring + report** — 1 week
4. **Progress dashboard** — 1 week
5. **Resume upload flow** — 1 week
6. **Rate limiting + usage tiers** — 3–4 days

### React Frontend Setup

```bash
npm create vite@latest speakprep-web -- --template react-ts
cd speakprep-web
npm install @supabase/supabase-js react-router-dom zustand
npm install recharts  # For progress charts
npm install react-hook-form zod  # For forms
npm install wavesurfer.js  # For audio visualization
npm run dev
```

**Key React components to build:**

```
src/
├── pages/
│   ├── LandingPage.tsx
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx     # Progress charts, recent sessions
│   ├── SessionSetupPage.tsx  # Choose interview type + difficulty
│   ├── VoiceSessionPage.tsx  # Main voice interface
│   └── SessionReportPage.tsx # Post-session scores + feedback
├── components/
│   ├── VoiceButton.tsx       # Push-to-talk with waveform
│   ├── TranscriptPane.tsx    # Live transcript
│   ├── ScoreCard.tsx         # Per-dimension score display
│   └── ProgressChart.tsx     # Score trend over time
├── hooks/
│   ├── useVoiceSession.ts    # WebSocket + audio management
│   └── useAudioRecorder.ts   # Microphone capture
└── store/
    └── sessionStore.ts       # Zustand global state
```

**✅ Done When:**
- [ ] User can register, verify email, log in
- [ ] User can upload resume and see parsed data
- [ ] User can complete a full interview session in browser
- [ ] Post-session report generated with per-question scores
- [ ] Score trend chart shows improvement across sessions
- [ ] Rate limiting enforced (3 sessions/week on free tier)
- [ ] 10 real users (friends, GW classmates) using it with feedback

---

## 8. Phase 6: Hardening + Launch

**Duration:** 3–4 weeks  
**Goal:** Production-grade reliability, security, and real user acquisition.

### Pre-Launch Security Checklist

```bash
# Run OWASP ZAP scan on your API
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://api.speakprep.com

# Check for exposed secrets
pip install gitleaks
gitleaks detect --source=. --verbose

# Verify HTTPS everywhere
curl -I http://api.speakprep.com  # Should redirect to HTTPS
curl -I https://api.speakprep.com/api/health  # Should return 200

# Test rate limiting
for i in $(seq 1 10); do curl https://api.speakprep.com/api/auth/login; done
# Should see 429 after 5 attempts

# Verify no SQL injection vulnerability
# Use parameterized queries everywhere — never string concatenation
```

### Load Testing

```python
# locust_test.py — Load test with realistic user behavior
# pip install locust

from locust import HttpUser, task, between
import json

class InterviewUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        # Register and login
        response = self.client.post("/api/auth/login", json={
            "email": f"test_{self.user_id}@test.com",
            "password": "testpassword"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def view_dashboard(self):
        self.client.get(
            "/api/sessions",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def start_session(self):
        self.client.post(
            "/api/sessions",
            json={"interview_type": "behavioral", "difficulty": "intermediate"},
            headers={"Authorization": f"Bearer {self.token}"}
        )

# Run: locust -f locust_test.py --host=https://api.speakprep.com
# Open http://localhost:8089 to control
```

### Launch Channels (Sequenced)

**Week 1 post-launch (soft launch — friends/network):**
- Share with 20 GW CS alumni in job search (LinkedIn DMs)
- Share in r/cscareerquestions and r/jobs
- Post in Discord servers: CS Career Hub, Blind

**Week 2 (public launch):**
- ProductHunt launch (post Tuesday–Thursday, 12:01 AM PT)
- Hacker News "Show HN" (post at 9 AM EST)
- LinkedIn post: personal story + demo video

**Week 3+ (content marketing):**
- Blog post: "I built an AI mock interviewer — here's what I learned about latency"
- TikTok/YouTube: 60-second demo video showing voice session
- Reach out to career coaches for referral partnerships

**✅ Done When:**
- [ ] Load test handles 50 concurrent sessions without latency spike
- [ ] No security vulnerabilities found in OWASP scan
- [ ] Database query times < 50ms for all dashboard queries
- [ ] Error rate < 0.1% in production (Sentry)
- [ ] ProductHunt and HN posts live
- [ ] First 100 registered users

---

## 9. Daily Development Workflow

```bash
# Morning: sync and plan
git pull origin develop
git checkout -b feature/my-feature-name

# During work: commit often (small, atomic)
git add -p  # Review and stage changes interactively (not git add .)
git commit -m "feat: add sentence boundary detection for TTS pipeline"

# Before ending day: push and verify
git push origin feature/my-feature-name
# Open PR to develop, link to user story

# Weekly: review metrics
# Open New Relic dashboard — check P95 latency trend
# Check Sentry — any new error types?
# Check PostHog — session completion rate?
```

---

## 10. Master Learning Resource List

### Core Books (Read in order)

| Book | When | Why |
|---|---|---|
| "Python Concurrency with asyncio" — Matthew Fowler | Phase 0 | asyncio is the foundation of everything |
| "Designing Data-Intensive Applications" — Martin Kleppmann | Phase 1-2 | System design thinking, data modeling |
| "System Design Interview" — Alex Xu (Vol 1) | Phase 4-5 | Interview story prep |
| "Clean Code" — Robert Martin | Ongoing | Code quality standards |

### Essential Documentation (Bookmark these)

- [FastAPI docs](https://fastapi.tiangolo.com) — WebSocket, dependencies, middleware
- [Deepgram streaming docs](https://developers.deepgram.com/docs/getting-started-with-live-streaming-audio)
- [Groq API docs](https://console.groq.com/docs/api-reference)
- [Kokoro-FastAPI GitHub](https://github.com/remsky/Kokoro-FastAPI)
- [Valkey docs](https://valkey.io/docs/)
- [Supabase docs](https://supabase.com/docs)
- [Alembic migrations](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Docker Compose](https://docs.docker.com/compose/)
- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)

### Open-Source Projects to Study

| Project | Why Study It | Where |
|---|---|---|
| **Pipecat** | Best example of production voice AI pipeline architecture | github.com/pipecat-ai/pipecat |
| **faster-whisper** | How CTranslate2 optimization works | github.com/SYSTRAN/faster-whisper |
| **Kokoro-FastAPI** | TTS serving architecture | github.com/remsky/Kokoro-FastAPI |
| **Interviewer (IliaLarchenko)** | Open-source AI interview tool — closest analog | github.com/IliaLarchenko/Interviewer |
| **LiveKit** | Real-time audio infrastructure at scale | github.com/livekit/livekit |

### Courses (Free)

- [HuggingFace Audio Course](https://huggingface.co/learn/audio-course) — Speech AI fundamentals
- [FastAPI Full Course](https://www.youtube.com/watch?v=0sOvCWFmrtA) — Patrick Loeber
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com) — Comprehensive, free
- [Docker Tutorial for Beginners](https://www.youtube.com/watch?v=fqMOX6JJhGo) — TechWorld with Nana

### Follow These Blogs (Weekly reading, 20 minutes)

- Netflix Technology Blog — real-time systems at scale
- Discord Engineering Blog — WebSocket at scale (millions of connections)
- Deepgram Blog — voice AI best practices
- AssemblyAI Blog — ASR technical deep dives
- High Scalability — architecture case studies

---

*End of Document 3 — Phase-by-Phase Build Guide + Learning Curriculum*
*Next: Document 4 — Interview Story + Portfolio*

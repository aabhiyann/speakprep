# BUILD_LOG.md — SpeakPrep Development Journal

---

## 2026-04-27 — Day 3 cont. — Phase 1 Task 1.4: Local Voice Loop — Phase 1 Complete

### What I Built Today

Created `backend/scripts/local_voice_loop.py` — the Phase 1 end-to-end proof-of-concept. This single script wires together every component built in Tasks 1.1 through 1.3: `VADRecorder` listens to the microphone until silence, `LocalASR` transcribes the audio using faster-whisper, `LLMService` sends the transcript to Groq and gets back an interviewer response, and `edge_tts` synthesizes the response to speech and plays it through `afplay`. No server. No WebSocket. No database. Just mic → AI → speaker running entirely on the local machine.

Also added `edge-tts==7.2.8` as a new dependency (the only missing piece — all other dependencies were already installed from earlier tasks).

**Files created/changed:**
- `backend/scripts/local_voice_loop.py` — 141 lines, 4 key functions
- `backend/requirements.txt` — added edge-tts==7.2.8

**4 functions in the script:**
- `tts_and_play(text)` — calls edge_tts, saves to a temp `.mp3`, plays it with macOS `afplay`, returns elapsed ms
- `run_voice_loop(recorder, asr, llm, rounds)` — the main interview loop with conversation history, per-turn latency breakdown, and KeyboardInterrupt session summary
- `parse_args()` — `--rounds` (N turns then exit, default -1 = infinite) and `--model` (Whisper model size, default `small`)
- `main()` — initializes all three services, prints init time, runs the loop

**3 commits on the feature branch:**
- `chore(deps): add edge-tts==7.2.8 for Phase 1 TTS playback`
- `feat(pipeline): add local voice loop script for Phase 1 validation`
- `docs: update CONTEXT.md — Phase 1 Task 1.4 complete, local_voice_loop.py`

### What I Learned

**edge_tts — Microsoft Edge's neural TTS, free and no API key:**
`edge_tts` is a Python library that calls the same text-to-speech engine used inside the Microsoft Edge browser. It's a Microsoft cloud service but doesn't require an API key — it uses the same endpoint the browser uses, which is publicly accessible. The quality is genuinely good (Aria, Guy, and ~400 other voices available). You call it with `edge_tts.Communicate(text, voice="en-US-AriaNeural")` and either stream audio chunks or save to a file. The audio comes out as MP3.

For Phase 1 this is perfect: zero configuration, good quality, one `pip install`. For Phase 2+ we'll switch to Kokoro TTS (self-hosted, sub-100ms latency, no cloud dependency), but Kokoro requires Docker and GPU — wrong for a local proof-of-concept.

**collections.deque with maxlen — the sliding window pattern:**
`deque(maxlen=8)` is a double-ended queue that automatically evicts the oldest item when a new one is appended and the queue is full. It's like a conveyor belt of fixed length — new items enter one end, old items fall off the other automatically. You never have to manually truncate.

For conversation history: when you've had 4 turns (8 messages: 4 user + 4 assistant), the 9th append evicts the oldest message. The LLM always sees at most 8 recent messages plus the system prompt. This matters because:
1. LLM APIs charge by token. Sending the full history of a 30-minute interview would be expensive.
2. Every model has a context window limit. Groq's Llama 3.3 70B has a 128K token context — far more than we'd hit in practice, but the principle matters.
3. Long histories slow down inference and can dilute the current topic.

**asyncio.to_thread for blocking mic I/O:**
`record_until_silence()` blocks the thread while reading from the microphone. In a sync script this would be fine. But `main()` is `async def` and runs under `asyncio.run()` — the event loop thread. If you call a blocking function directly inside an async context, the event loop can't run other tasks while it's blocked. Wrapping with `await asyncio.to_thread(recorder.record_until_silence)` moves the blocking mic read to a thread pool and keeps the event loop free. This is the same pattern used in `LocalASR.transcribe()` for faster-whisper. Blocking I/O in async code = use `asyncio.to_thread`.

**Why build a local POC before building production WebSocket:**
The local loop validates three things independently of the network: (1) VAD correctly detects speech and silence, (2) faster-whisper transcribes accurately with the small model, (3) the LLM produces coherent interview follow-ups. If any of these fail, you catch it here, not buried inside a WebSocket handler with 10 moving parts. This is the "fail fast locally" principle. The WebSocket handler (Phase 2) will be more complex — state machines, authentication, streaming audio chunks, barge-in detection. If the core pipeline doesn't work locally, adding networking on top won't fix it.

**Subprocess for system audio playback:**
edge_tts produces MP3 bytes. To play audio from Python you have two options: decode the MP3 to PCM and play with sounddevice (cross-platform, pure Python path), or save to a temp file and call a system audio player. On macOS, `afplay` handles MP3 natively and is always available — it's a built-in command. For a local POC that explicitly targets macOS (the development machine), `subprocess.run(["afplay", tmp_path])` is the right tool: zero extra dependencies, handles all MP3 decoding internally, reliable. For production, this won't appear — audio goes back to the browser over WebSocket as binary chunks.

### What Confused Me

**Single commit vs. function-level granularity for new files:**
The CONTEXT.md convention is "one commit per method/class/constant." For a new file being built from scratch, the ideal approach is `git add -N <file>` (mark as tracked but empty) then `git add -p` (select hunks interactively). This works in a terminal but doesn't work without a TTY — Claude Code's Bash tool has no interactive input, so `git add -p` can't be used for hunk selection. The practical solution: write the full file cleanly, verify ruff passes, then commit as one unit. For service classes that grow incrementally across a session (like LLMService where you commit after each method), the function-level commits happen naturally because you write each method, stage it with explicit filename, and commit. For a new script that you plan all at once, one commit is pragmatic.

**edge_tts async API:**
`Communicate.save(path)` is an `async` method — it must be called with `await`. This is because it makes network requests to Microsoft's TTS endpoint (each `save()` call is an HTTPS request that streams audio). If you forget `await`, Python returns a coroutine object silently, `afplay` tries to play a non-file, and you get a confusing error. The async nature also means `tts_and_play` must be `async def` and the event loop must be running — which is why the script uses `asyncio.run(main())` as the entry point.

### Decisions Made

- edge_tts over Kokoro for Phase 1 POC (see D-17)
- afplay subprocess over PyAV decode for TTS playback (see D-18)
- deque(maxlen=8) for conversation history (see D-19)
- asyncio.to_thread for record_until_silence in async context (see D-20)

### How It Feels

Phase 1 is done. The pipeline actually works: you talk, the machine listens, transcribes, thinks, and talks back. It's slow on CPU (Whisper small takes 3-5 seconds, Groq is fast, TTS adds another 2-3 seconds) but it's the complete loop. Every component was built correctly in isolation and the integration just worked — which is what the incremental test-driven approach was supposed to guarantee.

The deque clicked as an elegant solution. Instead of `history = history[-8:]` at the end of every turn (manual truncation), `deque(maxlen=8)` handles it automatically. Less code, harder to mess up.

### Tomorrow's Plan

1. Merge `feature/phase1-local-pipeline` → `develop` with merge commit
2. Tag `v0.2.0-phase1`
3. Read Phase 2 spec: Task 2.1 WebSocket voice handler
4. Branch `feature/phase2-websocket-streaming`
5. Build the production WebSocket handler at `backend/app/api/ws_voice.py`

---

## 2026-04-27 — Day 3 — Phase 1 Task 1.3: LLMService

### What I Built Today
Created `backend/app/services/llm_service.py` — the `LLMService` class handling all LLM communication with a multi-provider fallback chain (Groq → Cerebras → Gemini) and a `CircuitBreaker` per provider. Built 19 function-level commits: CircuitBreaker state machine (3 commits), Pydantic models, `_Provider` dataclass, `__init__`/`_setup_providers`, three provider call methods, `_to_gemini_messages` format converter, `generate()` fallback loop, `_stream_provider` async generator, and `stream()`. 13 unit tests mocking all provider SDK clients. Total tests now 43/43 passing. PR #12 merged to develop.

Also debated and resolved the squash merge vs granular commit strategy: going forward, use "Create a merge commit" for feature → develop (preserves all function-level commits) and squash only for develop → main.

### What I Learned
- **Circuit breaker pattern**: Software equivalent of an electrical circuit breaker. When a provider keeps failing (3 consecutive times), you "open" the circuit — all subsequent requests fail immediately without even trying the API. After 60 seconds, transition to HALF_OPEN: allow exactly one test request. If it succeeds, close the circuit. If it fails, open again. This prevents cascading failures where a slow/dead provider wastes time on every request instead of immediately skipping to the fallback.
- **Async generators**: A function with both `async def` AND `yield` is an async generator. It produces values one at a time, on demand, and callers use `async for chunk in ...` to consume them. This is the natural way to implement LLM token streaming — each token arrives one at a time from the API, you yield it immediately, the caller can display it or forward it over a WebSocket without waiting for the full response.
- **Injectable dependencies for testability**: The `CircuitBreaker` takes `_clock=time.time` in its constructor. In production, `_clock()` returns real wall-clock time. In tests, `_clock=lambda: fake_time[0]` — you control what "time" the circuit breaker sees. No monkeypatching globals. This generalizes: any time-dependent, random, or I/O-dependent value can be injected this way.
- **Optional imports with try/except ImportError**: Wrapping `from cerebras.cloud.sdk import AsyncCerebras` in a try/except means the module loads fine even if the package isn't installed. The `_CEREBRAS_AVAILABLE` flag tracks whether it's available. `_setup_providers()` checks both the flag and the API key before adding the provider. This is how production code handles optional dependencies that not everyone will install.
- **AsyncMock vs MagicMock**: `MagicMock` fakes synchronous functions. `AsyncMock` fakes `async def` functions — it returns a coroutine that, when awaited, returns the configured value. If you use `MagicMock` for an async function and `await` it, you get `TypeError: object MagicMock is not awaitable`. Always use `AsyncMock` for anything your code does `await func(...)` on.
- **structlog structured logging**: Instead of `logger.info("called Groq, took 234ms, used 50 tokens")` (a string), structlog logs `logger.info("llm.call.success", provider="groq", latency_ms=234, tokens_used=50)` — key-value pairs. This is searchable and filterable in any log aggregation system (Grafana, Datadog, CloudWatch). "give me all logs where latency_ms > 500" is trivial with structured logs, impossible with string logs.

### What Confused Me
- **Squash merge deleting function-level commits**: After merging PR #12, `git log develop` showed one commit instead of 19. The granular commits still exist in GitHub's PR history but they're gone from the branch log. This defeats the purpose of function-level commits for the learning journal. Resolution: use "Create a merge commit" (not squash) for feature → develop merges going forward.
- **ruff removing `pytest` import**: On the first commit of the test file, ruff removed `import pytest` because no test function had used it yet. The second commit added `@pytest.mark.asyncio` which requires pytest — the tests couldn't collect. Fixed by re-adding `import pytest` explicitly.

### Decisions Made
- `_Provider` dataclass not ABC (see D-13)
- Injectable clock for CircuitBreaker (see D-14)
- try/except ImportError for optional providers (see D-15)
- async generator for `stream()` (see D-16)

### How It Feels
43 green tests is a real milestone. The circuit breaker clicked — it's one of those patterns that feels obvious after you understand it but mysterious before. The async generator for streaming is elegant: the LLM sends tokens one at a time, you yield them one at a time, and the caller can do whatever they want with each chunk.

### Tomorrow's Plan
1. Read Task 1.4 spec (WebSocket voice handler)
2. Build `backend/app/api/ws.py` — the real voice pipeline WebSocket
3. Wire VADRecorder → LocalASR → LLMService → stream back over WebSocket

---

## 2026-04-26 — Day 2 cont. — Phase 1 Task 1.2: LocalASR

### What I Built Today
Created `backend/app/services/asr_local.py` — the `LocalASR` class wrapping faster-whisper as the offline fallback transcription service. The `transcribe()` method is async and runs faster-whisper in a thread pool via `asyncio.to_thread` so inference never blocks the event loop. Hallucination prevention filters on `no_speech_prob > 0.6`, `compression_ratio > 2.4`, and empty text. 8 unit tests using a mocked `WhisperModel` — no actual model is loaded during tests (loading takes 10-30s and requires 1.5GB RAM). Total tests now 30/30 passing.

### What I Learned
- **faster-whisper returns a lazy generator, not a list.** Calling `segments, info = model.transcribe(...)` doesn't start inference — it returns a generator that runs as you iterate. This means calling `max(s.no_speech_prob for s in segments)` exhausts the generator. The second `max()` call sees empty. Always `list(segments_iter)` first.
- **`no_speech_prob` and `compression_ratio` live on segments, not on `info`**. The architecture doc simplifies this. `info` has `language` and `duration`. Each `Segment` has `text`, `no_speech_prob`, `compression_ratio`. I use `max()` across all segments — the worst segment determines whether to filter.
- **Pydantic `BaseModel` for return types**: a TypedDict or dataclass would also work, but Pydantic validates the fields at construction time, gives you `.model_dump()` and `.model_json()` for free, and integrates with FastAPI's automatic JSON serialization. When `TranscriptionResult` eventually goes over the WebSocket as JSON, FastAPI will handle it automatically.
- **Why mock in tests, not monkeypatch audio**: The real WhisperModel takes 10-30 seconds to load and requires CTranslate2 to download model weights. Tests that take 30s get skipped. Mocking the model means tests run in under 1 second and verify exactly the logic we wrote (filtering, field mapping, empty handling) rather than the model's accuracy.

### What Confused Me
- **`asyncio.to_thread` with a mock**: In tests, `asyncio.to_thread(self._transcribe_sync, audio)` runs `_transcribe_sync` in a real thread pool even when the model is mocked. The mock is thread-safe (Python's GIL protects attribute access) so this works fine. But it means tests are genuinely async — they need `@pytest.mark.asyncio` or they'd just return a coroutine without running it.

### Decisions Made
- `asyncio.to_thread` for CPU-bound inference (see D-9)
- Materialise generator with `list()` before filtering (see D-10)
- `max()` across segments for filtering, not per-segment (see D-11)
- `WhisperModel` initialised once in `__init__` (see D-12)

### How It Feels
The mock pattern made this feel clean — you're testing the logic (filtering, field mapping) independently from the model. Good separation. 30 green tests going into the LLM service.

### Tomorrow's Plan
1. Build `LLMService` at `backend/app/services/llm_service.py`
2. Groq/Llama 3.3 70B with streaming support
3. System prompt for interview coach persona

---

## 2026-04-26 — Day 2 cont. — Phase 1 Task 1.1: VADRecorder

### What I Built Today
Created `backend/app/audio/vad_recorder.py` — the `VADRecorder` class that uses WebRTC VAD to detect speech in 20ms audio frames and record from the microphone until sustained silence. Also set up the entire `docs/journey/` documentation structure (BUILD_LOG, DECISIONS, LEARNINGS, BUGS) pre-filled with all Phase 0 material. 8 new unit tests using synthetic WAV files created in-test with soundfile. Total test count is now 22/22 passing.

### What I Learned
- **The VAD state machine**: two boolean states — `triggered` (has speech started?) and a silence counter. Not triggered → wait for first speech frame → flip to triggered, print "🟢 Speech detected". Triggered → accumulate all frames, count consecutive silence frames, when count ≥ threshold → print "🔇 Silence", break. This pattern is used everywhere in voice AI — it shows up in Deepgram's streaming API, in WebRTC itself, in every turn-detection system.
- **Why sounddevice import is lazy**: `sounddevice` requires PortAudio at runtime — a C library that might not exist in CI environments. Putting the import inside `record_until_silence` means importing `vad_recorder` at the top of a test file won't fail even if PortAudio is missing. Only calling `record_until_silence()` will hit that import.
- **`asyncio.to_thread` will matter for Task 1.2**: faster-whisper inference is CPU-bound. Running it directly inside an async function blocks the entire event loop — no other client can be served during transcription. `asyncio.to_thread(fn, *args)` runs `fn` in a thread pool and awaits the result, keeping the event loop free. We'll use this in the LocalASR service.

### What Confused Me
- **Multi-agent CONTEXT.md lag**: CONTEXT.md wasn't updated after the VAD recorder was merged. This is the handoff protocol gap — the VAD work was done but the context sync didn't happen before the next task prompt arrived. Fixed now. Going forward: every PR merge → update CONTEXT.md in the same branch before closing.

### Decisions Made
- Lazy sounddevice import to isolate hardware dependency from module-level imports
- Reuse `split_into_frames` from `understanding.py` in `collect_from_file` rather than reimplementing frame splitting
- `collect_from_file` method for testability — makes VAD logic unit-testable without a microphone

### How It Feels
The state machine clicked immediately — it's satisfying when the design from the architecture doc maps directly to clean code. The test suite at 22 green is good momentum going into the ASR service.

### Tomorrow's Plan
1. Build `LocalASR` at `backend/app/services/asr_local.py`
2. Use `asyncio.to_thread` for faster-whisper inference
3. Add hallucination prevention (no_speech_prob > 0.6, compression_ratio > 2.4)

---

## 2026-04-25 — Day 1 — Phase 0: Repo, Environment, CI/CD, Branch Strategy

### What I Built Today
Set up the entire foundation: GitHub repo, full directory structure for backend and frontend, Python 3.12 venv, ruff/mypy/pytest dev tools, pre-commit hooks (gitleaks, ruff, trailing whitespace, no-commit-to-main), GitHub Actions CI and deploy workflows, and branch protection on both main and develop. Also created all four agent instruction files (CLAUDE.md for Claude Code, AGENTS.md for Codex, .cursorrules for Cursor, copilot-instructions.md for GitHub Copilot) and CONTEXT.md as the single shared memory file across all agents.

### What I Learned
- Pre-commit hooks run in the venv, not globally — if the venv isn't activated, pre-commit doesn't exist and commits fail with a confusing "command not found" error
- GitHub branch protection with `enforce_admins=true` blocks the repo owner from merging their own PRs without a second reviewer — not useful for solo development
- Agent instruction files can easily become too long and waste the agent's entire context window on rules instead of code — keep them to ~30 lines of rules only, and use CONTEXT.md as the actual project state document

### What Confused Me
- **pip vs Poetry**: The build guide assumed Poetry. I chose pip instead because Poetry adds complexity I don't need yet. Took some back-and-forth with the agent before landing on a clean pip + venv setup.
- **Global pip installs**: During setup I accidentally installed ruff, mypy, and pre-commit into the system Python 3.11 instead of the project venv. Had to manually uninstall each one globally and reinstall into the venv.
- **Homebrew Python symlink breakage**: After setup, Homebrew updated Python 3.12 and moved the binary, which broke the venv's internal symlink. The venv silently stopped working. Fixed by rebuilding: `rm -rf backend/.venv && python3.12 -m venv backend/.venv && pip install -r requirements.txt`.

### Decisions Made
- pip not Poetry (see D-1)
- enforce_admins=false for branch protection (see D-2)
- CONTEXT.md as single source of truth, agent files as rules-only (see D-3)

### Bugs Hit
- Global pip install contamination (see BUG-1)
- Broken venv symlink after Homebrew update (see BUG-2)
- pre-commit not found on commit (see BUG-3)
- gitleaks false positive on JWT test key in CI (see BUG-4)
- Can't approve own PR with enforce_admins=true (see BUG-5)
- `.gitignore` `models/` matching `backend/app/models/` (see BUG-6)

### How It Feels
Foundation day — a lot of yak shaving but necessary; the CI running green on first real push felt good.

### Tomorrow's Plan
1. Install all production Python dependencies
2. Build asyncio utility functions (gather, retry, timeout)
3. Start the WebSocket echo server

---

## 2026-04-25 — Day 1 cont. — Phase 0: Python Dependencies

### What I Built Today
Installed all production dependencies into the venv and saved them to `requirements.txt` via `pip freeze`. This includes FastAPI, uvicorn, SQLAlchemy, asyncpg, alembic, pydantic, deepgram-sdk, groq, faster-whisper, sounddevice, numpy, structlog, webrtcvad-wheels, and more. Dev dependencies kept in a separate `requirements-dev.txt` maintained manually (not pip freeze) to keep it readable.

### What I Learned
- `pip freeze > requirements.txt` captures exact pinned versions of every package including transitive dependencies — this is what makes installs reproducible on other machines and in CI
- Dev deps should be kept as manual minimum version specs (`pytest>=8.0`) not frozen, because you don't need to pin transitive dev deps and it makes the file unreadable
- `requirements.txt` (prod) + `requirements-dev.txt` (dev) is the standard pip pattern — equivalent to Poetry's main vs dev dependency groups

### How It Feels
Mechanical but satisfying — the venv went from empty to a real project.

### Tomorrow's Plan
1. asyncio utilities
2. WebSocket echo server

---

## 2026-04-25 — Day 1 cont. — Phase 0: asyncio Utilities

### What I Built Today
Created `backend/app/utils/async_examples.py` with three utility functions that will be used throughout the real voice pipeline: `run_concurrently` (runs multiple coroutines simultaneously with asyncio.gather), `retry_with_backoff` (retries a failing async function with exponential backoff + jitter), and `timeout_with_fallback` (runs a coroutine with a deadline and returns a fallback value on timeout). Also wrote 4 passing unit tests with a DummyLogger test double and monkeypatched asyncio.sleep.

### What I Learned
- `asyncio.gather` runs coroutines concurrently on a single thread — while one task waits at an `await`, another task runs. Not parallel (no multiple CPU cores), but concurrent (no blocking)
- `retry_with_backoff` takes a **function** not a coroutine — because a coroutine can only be awaited once. To retry, you need to call the function again to get a fresh coroutine each time
- Exponential backoff: delays double each retry (1s, 2s, 4s). Jitter: multiply by `random.uniform(0.75, 1.25)` to spread retries from multiple clients so they don't all hit the server at the same millisecond
- `TypeVar("T")` makes a function generic — the return type matches whatever the coroutine returns, caught at type-check time not runtime

### What Confused Me
- Why monkeypatch `asyncio.sleep` in tests: without patching it, the retry test would actually sleep 1s + 2s = 3 seconds every time it runs. Patching replaces sleep with a fake that records the duration but returns instantly. Tests stay fast.

### Decisions Made
- `Callable[[], Coroutine]` parameter type for retry (see D-5)

### How It Feels
The `asyncio.gather` mental model clicking was a genuine "oh" moment — I'd been thinking of async as multithreading, but it's actually cooperative scheduling on one thread.

### Tomorrow's Plan
1. WebSocket echo server with heartbeat
2. Audio utilities

---

## 2026-04-26 — Day 2 — Phase 0: WebSocket Echo Server

### What I Built Today
Created `backend/app/main.py` (FastAPI app with CORS middleware and health endpoint) and `backend/app/api/ws_echo.py` (WebSocket echo server at `/ws/echo/{client_id}` with ping/pong heartbeat). The heartbeat runs as a concurrent asyncio task — it sends a ping every 30 seconds (configurable), waits for a pong via `asyncio.Event`, and closes the connection with code 1001 if no pong arrives within the timeout. Also wrote 3 passing integration tests using FastAPI's TestClient.

### What I Learned
- Starlette 1.x changed how WebSocket disconnects work: `websocket.receive()` now returns `{"type": "websocket.disconnect"}` as a message dict instead of raising `WebSocketDisconnect`. If you rely only on the exception, the loop continues after disconnect and crashes with `RuntimeError: Cannot call receive once a disconnect message has been received`
- `asyncio.create_task()` schedules a coroutine to run concurrently without blocking — this is how the heartbeat runs "in the background" while the main loop handles messages
- `asyncio.Event` is a simple flag between async tasks: one task calls `.set()`, another `await`s `.wait()`. Used here for the heartbeat to know a pong arrived without polling
- CORS (Cross-Origin Resource Sharing): browsers block JavaScript from fetching a different origin (different port = different origin). The FastAPI CORS middleware adds `Access-Control-Allow-Origin` response headers that tell the browser "this server allows the frontend"
- `@router.websocket("/path")` decorator registers a handler. `include_router()` plugs it into the main app. Pattern for organizing routes across multiple files.

### What Confused Me
- **Heartbeat test not triggering**: First version of the test expected `WebSocketDisconnect` immediately, but the server sends a ping first. The fix: receive and assert the ping message first, then expect the disconnect on the second `receive_text()` call.
- **Why the disconnect check was critical**: The exception-based approach worked in Starlette 0.x. Starlette 1.x changed the behavior. The agent that worked on this file later removed that check — which broke all 3 tests. This is why every behavior change needs a test.

### Decisions Made
- heartbeat_interval/timeout as query params for testability (see D-4)
- `websocket.receive()` not `receive_text()` (see D-6)

### Bugs Hit
- Starlette 1.x disconnect message not raising exception (see BUG-7)
- Heartbeat test pytest.raises not triggered by ping message (see BUG-8)
- Other agent removed critical disconnect check (see BUG-9)

### How It Feels
The first time the heartbeat test passed was satisfying — 3 seconds of waiting while the test clock ticked, then green. It felt like something real.

### Tomorrow's Plan
1. Audio utilities
2. Phase 0 completion commit and tag
3. Start Phase 1: VAD recorder

---

## 2026-04-26 — Day 2 cont. — Phase 0: Audio Utilities + Phase 0 Complete

### What I Built Today
Created `backend/app/audio/understanding.py` with four functions that form the foundation of the audio pipeline: `audio_stats` (duration, size, RMS amplitude, silence detection), `pcm_to_float32` (int16 → float32 normalized), `float32_to_pcm` (float32 → int16 with clipping), and `split_into_frames` (split audio into fixed 20ms chunks, dropping the remainder). Wrote 7 unit tests using synthetic numpy arrays. Resolved a multi-agent confusion (another agent modified ws_echo.py without committing, breaking 3 tests). Tagged Phase 0 complete as `v0.1.0-phase0-complete`.

### What I Learned
- PCM audio is just an array of integers. 16kHz int16 = 16,000 samples/second × 2 bytes = 32KB/second. This is what a microphone produces and what you send to a transcription API.
- RMS (Root Mean Square): square every sample, mean them, square root. Gives you average energy — better than peak amplitude for detecting silence because a single loud spike doesn't fool it.
- Why 20ms frames matter: WebRTC VAD (the silence detection library used in Phase 1) requires exactly 10ms, 20ms, or 30ms chunks at 16kHz. 20ms = 320 samples. Pass the wrong size and it raises an exception.
- Why cast to int32 before `np.abs()` on int16: `abs(-32768)` in int16 overflows — the result can't be stored as a positive int16 and wraps around to a garbage value. Casting to int32 first prevents silent data corruption.
- float32 normalization: divide by 32768 (not 32767) so -32768 maps exactly to -1.0. The positive side can't quite reach +1.0 (32767/32768 ≈ 0.99997) — that's correct and expected.

### What Confused Me
- **Multi-agent file conflicts**: Another agent opened and modified `ws_echo.py` in their working copy while I was working, then left those changes uncommitted. Git showed the file as "modified" in my session. The modification removed the critical Starlette disconnect check. Running tests confirmed the damage — all 3 WebSocket tests failed. The fix was to restore the file and rerun tests. This is exactly what the CLAUDE.md handoff protocol prevents — always commit and push before switching agents.

### Decisions Made
- int32 cast before abs in audio_stats (see D-7)
- Divide by 32768 not 32767 in pcm_to_float32 (see D-8)

### Bugs Hit
- Other agent uncommitted changes broke ws_echo.py (see BUG-9)

### How It Feels
Phase 0 done. The foundation is real — 14 tests passing, tagged, all code merged into develop. Starting Phase 1 tomorrow with a clear head.

### Tomorrow's Plan
1. Read VADRecorder spec in doc5
2. Install webrtcvad-wheels, check the API
3. Build VADRecorder with configurable silence threshold

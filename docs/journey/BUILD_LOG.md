# BUILD_LOG.md — SpeakPrep Development Journal

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

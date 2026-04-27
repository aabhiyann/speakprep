# CONTEXT.md — Agent Shared Memory
# Update this every time you finish a task or switch agents.
# Rules are in CLAUDE.md / AGENTS.md / .cursorrules / copilot-instructions.md

## Project: SpeakPrep — Real-time Voice AI Mock Interview Coach
## Author: Abhiyan Sainju
## Started: April 2026
## Contributors: Abhiyan Sainju only — no AI tools appear as git contributors
## Current Phase: 1 — Local Voice Pipeline
## Current Task: LLM service with Groq (Task 1.3)

## Architecture Summary
- Backend: Python 3.12, FastAPI, asyncio, WebSockets
- ASR: Deepgram Nova-3 (primary), Faster-Whisper (fallback)
- LLM: Groq/Llama 3.3 70B (primary), Cerebras (fallback)
- TTS: Kokoro TTS self-hosted via Docker
- DB: Supabase PostgreSQL (Phase 1-2), self-hosted later
- Cache: Valkey (Redis-compatible)
- Infra: Oracle Cloud ARM, Docker Compose, Cloudflare Tunnel

## Docs Reference
- PRD: /docs/doc1-prd-product.md
- Architecture: /docs/doc2-system-design-architecture.md
- Build Guide: /docs/doc3-build-guide-curriculum.md
- Portfolio: /docs/doc4-interview-portfolio.md
- Dev Playbook: /docs/doc5-dev-playbook.md
- Doc Prompts: /docs/doc6 (LaTeX source — use doc6 prompts for build log, decisions, learnings, blog posts)
- Build Log: /docs/journey/BUILD_LOG.md
- Decisions: /docs/journey/DECISIONS.md
- Learnings: /docs/journey/LEARNINGS.md
- Bugs: /docs/journey/BUGS.md

## What's Working
- [x] Git repo initialized and pushed to GitHub
- [x] Full directory structure (backend + frontend)
- [x] Python 3.12 venv at backend/.venv
- [x] Dev tools: ruff, mypy, pytest, pytest-asyncio, pytest-cov, pre-commit
- [x] Pre-commit hooks (gitleaks, ruff, trailing whitespace, no-commit-to-main)
- [x] GitHub Actions CI + deploy workflows
- [x] Branch protection (main + develop)
- [x] .env.example with all required variables
- [x] Agent instruction files (CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md)
- [x] backend/app/main.py — FastAPI app, CORS, health endpoint
- [x] backend/app/api/ws_echo.py — WebSocket echo server with ping/pong heartbeat
- [x] backend/tests/integration/test_ws_echo.py — 3 passing integration tests
- [x] backend/app/utils/async_examples.py — asyncio utilities (gather, retry, timeout)
- [x] backend/tests/unit/test_async_utils.py — 4 passing unit tests
- [x] backend/app/audio/understanding.py — PCM/float32 conversion, frame splitting, audio stats
- [x] backend/tests/unit/test_audio_understanding.py — 7 passing unit tests
- [x] Phase 0 complete — tagged v0.1.0-phase0
- [x] backend/app/audio/vad_recorder.py — VADRecorder with WebRTC VAD, silence detection, file testing
- [x] backend/tests/unit/test_vad_recorder.py — 8 passing unit tests (synthetic WAV fixtures)
- [x] docs/journey/ — BUILD_LOG, DECISIONS, LEARNINGS, BUGS pre-filled for Phase 0

- [x] backend/app/services/asr_local.py — LocalASR with faster-whisper, hallucination prevention, asyncio.to_thread
- [x] backend/tests/unit/test_asr_local.py — 8 passing unit tests (WhisperModel mocked)

## What's In Progress
- LLM service (backend/app/services/llm_service.py) — not started

## What's Blocked
- Nothing

## Key Files
- Entry point: backend/app/main.py ✅
- Echo server: backend/app/api/ws_echo.py ✅
- Async utils: backend/app/utils/async_examples.py ✅
- Audio utils: backend/app/audio/understanding.py ✅
- VAD recorder: backend/app/audio/vad_recorder.py ✅
- Local ASR: backend/app/services/asr_local.py ✅
- WebSocket voice handler: backend/app/api/ws.py (not created yet)
- DB models: backend/app/models/ (not created yet)

## Commit Convention
- **Function-level granularity**: one commit per method, class, or constant — NOT one commit per file
- Each method gets its own `feat(scope): add MethodName` commit
- Tests grouped by what they cover (e.g., "tests for hallucination filters" separate from "tests for valid output")
- CONTEXT.md and docs always in their own separate commits

## DO NOT TOUCH
- Nothing locked yet

## Last Updated
- Date: 2026-04-26
- By: Abhiyan (Phase 1 Task 1.2 complete, starting Task 1.3; added function-level commit convention)

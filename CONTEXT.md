# CONTEXT.md — Agent Shared Memory
# Update this every time you finish a task or switch agents.
# Rules are in CLAUDE.md / AGENTS.md / .cursorrules / copilot-instructions.md

## Project: SpeakPrep — Real-time Voice AI Mock Interview Coach
## Author: Abhiyan Sainju
## Started: April 2026
## Contributors: Abhiyan Sainju only — no AI tools appear as git contributors
## Current Phase: 2 — Real-Time Streaming
## Current Task: Task 2.1 — WebSocket voice handler (not started)

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

- [x] backend/app/services/llm_service.py — LLMService with Groq/Cerebras/Gemini fallback, CircuitBreaker, streaming
- [x] backend/tests/unit/test_llm_service.py — 13 passing unit tests (all providers mocked)

- [x] backend/scripts/local_voice_loop.py — end-to-end local voice loop (VADRecorder → LocalASR → LLMService → edge_tts/afplay)
- [x] Phase 1 complete — tagged v0.2.0-phase1

## What's In Progress
- Phase 2: WebSocket streaming (Task 2.1) — not started

## What's Blocked
- Nothing

## Key Files
- Entry point: backend/app/main.py ✅
- Echo server: backend/app/api/ws_echo.py ✅
- Async utils: backend/app/utils/async_examples.py ✅
- Audio utils: backend/app/audio/understanding.py ✅
- VAD recorder: backend/app/audio/vad_recorder.py ✅
- Local ASR: backend/app/services/asr_local.py ✅
- LLM service: backend/app/services/llm_service.py ✅
- Local voice loop: backend/scripts/local_voice_loop.py ✅
- WebSocket voice handler: backend/app/api/ws.py (not created yet — Phase 2)
- DB models: backend/app/models/ (not created yet)

## Commit Convention
- **Function-level granularity**: one commit per method, class, or constant — NOT one commit per file
- Each method gets its own `feat(scope): add MethodName` commit
- Tests grouped by what they cover (e.g., "tests for hallucination filters" separate from "tests for valid output")
- CONTEXT.md and docs always in their own separate commits

## PR Merge Strategy
- **feature → develop**: always "Create a merge commit" (preserves all function-level commits in git log develop)
- **develop → main**: "Squash and merge" (one clean release commit per phase milestone)
- NEVER squash feature PRs into develop — it destroys the learning journal
- GitHub repo settings: both merge commit + squash enabled, rebase disabled

## DO NOT TOUCH
- Nothing locked yet

## Last Updated
- Date: 2026-04-27
- By: Abhiyan (Phase 1 fully complete — PR #14 merged to develop, tagged v0.2.0-phase1, all journey docs written. Starting Phase 2.)

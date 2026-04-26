# CONTEXT.md — Agent Shared Memory
# Update this every time you finish a task or switch agents.
# Rules are in CLAUDE.md / AGENTS.md / .cursorrules / copilot-instructions.md

## Project: SpeakPrep — Real-time Voice AI Mock Interview Coach
## Author: Abhiyan Sainju
## Started: April 2026
## Contributors: Abhiyan Sainju only — no AI tools appear as git contributors
## Current Phase: 1 — Local Voice Pipeline
## Current Task: VAD-triggered audio recording (Task 1.1)

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

## What's In Progress
- VADRecorder (backend/app/audio/vad_recorder.py) — not started

## What's Blocked
- Nothing

## Key Files
- Entry point: backend/app/main.py ✅
- Echo server: backend/app/api/ws_echo.py ✅
- Async utils: backend/app/utils/async_examples.py ✅
- Audio utils: backend/app/audio/understanding.py ✅
- DB models: backend/app/models/ (not created yet)
- WebSocket voice handler: backend/app/api/ws.py (not created yet)
- VAD recorder: backend/app/audio/vad_recorder.py (not created yet)

## DO NOT TOUCH
- Nothing locked yet

## Last Updated
- Date: 2026-04-26
- By: Abhiyan (Phase 0 complete, Phase 1 starting)

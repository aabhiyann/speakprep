# CONTEXT.md — Agent Shared Memory
# Update this every time you finish a task or switch agents

## Project: SpeakPrep — Real-time Voice AI Mock Interview Coach
## Author: Abhiyan Sainju
## Started: April 2026
## Current Phase: 0 — Environment Setup (COMPLETE)
## Current Task: Phase 0 tagged — ready for Phase 1

## AGENT SETUP — Run This First Every Session
**Always activate the Python venv before running any backend commands:**
```bash
source backend/.venv/bin/activate
```
- Python 3.12 venv lives at `backend/.venv/` (gitignored)
- Dev tools (ruff, mypy, pytest, pre-commit) are installed inside it
- Without activation: wrong Python version, missing packages, pre-commit may fail

## AGENT HANDOFF PROTOCOL — Do This Before Switching Agents
1. **Commit current state**
   ```bash
   git add -p
   git commit -m "wip: [what you were doing] — switching agents"
   ```
2. **Update CONTEXT.md** — Current Task, What's Working, What's In Progress, What's Blocked
   ```bash
   git add CONTEXT.md
   git commit -m "docs: update CONTEXT.md before agent switch"
   ```
3. **Push**
   ```bash
   git push origin [current-branch]
   ```

## GIT DISCIPLINE — Agents Must Follow This
**Never use `git add .` or `git add -A`. Always stage granularly.**

### Commit message format
```
type(scope): short description (max 72 chars)
```
Types: `feat` `fix` `test` `docs` `refactor` `perf` `chore` `revert` `wip`
Scopes: `audio` `vad` `asr` `llm` `tts` `ws` `api` `auth` `db` `cache` `pipeline` `scoring` `resume` `questions` `dashboard` `ci` `infra`

### Rules
- One logical unit per commit (one function, one test, one config change)
- `wip:` commits only on feature branches — never merge to develop
- Always branch from `develop`, never from `main`
- Branch naming: `feature/vad-recorder`, `fix/auth-token-expiry`, `chore/update-deps`
- Delete feature branches after merge
- Tag each phase completion: `git tag -a v0.X.0-phaseN -m "Phase N complete: ..."`

### Branch protection
- `main` — requires PR + CI pass + 1 review
- `develop` — requires CI pass

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
- Build Guide: /docs/doc3-build-guide.md
- Portfolio: /docs/doc4-interview-portfolio.md

## What's Working
- [x] Git repo initialized and pushed to GitHub
- [x] Full directory structure (backend + frontend)
- [x] Python 3.12 venv at backend/.venv
- [x] Dev tools: ruff, mypy, pytest, pytest-asyncio, pytest-cov, pre-commit

## What's In Progress
- Nothing — Phase 0 complete, Phase 1 not started

## What's Blocked
- Nothing

## Key Files
- Entry point: backend/app/main.py (not created yet)
- DB models: backend/app/models/ (not created yet)
- WebSocket handler: backend/app/api/ws.py (not created yet)

## DO NOT TOUCH
- Nothing locked yet

## Last Updated
- Date: 2026-04-25
- By: Abhiyan (Phase 0 complete)

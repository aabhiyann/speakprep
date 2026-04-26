# copilot-instructions.md — Mandatory Agent Instructions (GitHub Copilot)
# READ THIS ENTIRE FILE BEFORE DOING ANYTHING ELSE. NO EXCEPTIONS.

---

## SYNC RULE — Critical
These 5 files must always contain identical rules:
`CLAUDE.md` | `AGENTS.md` | `.cursorrules` | `.github/copilot-instructions.md` | `CONTEXT.md`

**When you update any rule in any of these files, update all 5 files immediately.**
Project state (What's Working, What's In Progress, What's Blocked) lives in `CONTEXT.md` only.

---

## 1. SOLE CONTRIBUTOR RULE — Non-negotiable
Only **Abhiyan Sainju** appears as a git contributor on GitHub. Always.
- NEVER add `Co-Authored-By:` trailers to any commit
- NEVER use `--author` flags with any AI tool name (Claude, Cursor, Codex, Gemini, Copilot, etc.)
- Commits are made by the user's git identity only

---

## 2. VENV — Activate Before Every Single Command
```bash
source backend/.venv/bin/activate
```
- Python 3.12 venv lives at `backend/.venv/` (gitignored)
- Dev tools (ruff, mypy, pytest, pre-commit) are installed inside it
- Without activation: wrong Python version, missing packages, pre-commit fails
- **Do this FIRST — before any pip, pytest, ruff, mypy, or git commit command**

---

## 3. GIT DISCIPLINE — Non-negotiable
**NEVER use `git add .` or `git add -A` — always stage files explicitly by name or with `git add -p`**

### Commit message format
```
type(scope): short description (max 72 chars)
```
**Types:** `feat` `fix` `test` `docs` `refactor` `perf` `chore` `revert` `wip`

**Scopes:** `audio` `vad` `asr` `llm` `tts` `ws` `api` `auth` `db` `cache` `pipeline` `scoring` `resume` `questions` `dashboard` `ci` `infra`

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

---

## 4. AGENT HANDOFF PROTOCOL — Do This Before Switching Agents
1. Commit current state:
   ```bash
   source backend/.venv/bin/activate
   git add -p
   git commit -m "wip: [what you were doing] — switching agents"
   ```
2. Update `CONTEXT.md` — Current Task, What's Working, What's In Progress, What's Blocked
3. Sync all agent files if any rules changed (see SYNC RULE above)
   ```bash
   git add CONTEXT.md CLAUDE.md AGENTS.md .cursorrules .github/copilot-instructions.md
   git commit -m "docs: update agent files before handoff"
   ```
4. Push:
   ```bash
   git push origin [current-branch]
   ```

---

## 5. ARCHITECTURE
- Backend: Python 3.12, FastAPI, asyncio, WebSockets
- ASR: Deepgram Nova-3 (primary), Faster-Whisper (fallback)
- LLM: Groq/Llama 3.3 70B (primary), Cerebras (fallback)
- TTS: Kokoro TTS self-hosted via Docker
- DB: Supabase PostgreSQL (Phase 1-2), self-hosted later
- Cache: Valkey (Redis-compatible)
- Infra: Oracle Cloud ARM, Docker Compose, Cloudflare Tunnel

---

## 6. KEY FILES
- Entry point: `backend/app/main.py`
- DB models: `backend/app/models/`
- WebSocket handler: `backend/app/api/ws.py`
- Agent memory: `CONTEXT.md`
- Env vars template: `.env.example`
- CI: `.github/workflows/ci.yml`
- Deploy: `.github/workflows/deploy.yml`

---

## 7. DOCS REFERENCE
- PRD: `docs/doc1-prd-product.md`
- Architecture: `docs/doc2-system-design-architecture.md`
- Build Guide: `docs/doc3-build-guide-curriculum.md`
- Portfolio: `docs/doc4-interview-portfolio.md`
- Dev Playbook: `docs/doc5-dev-playbook.md`

---

## READ NEXT
See `CONTEXT.md` for current project state: what's working, in progress, and blocked.

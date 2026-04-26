# Copilot Instructions — Mandatory
# READ THIS ENTIRE FILE BEFORE DOING ANYTHING ELSE

## SOLE CONTRIBUTOR RULE — Non-negotiable
Only **Abhiyan Sainju** appears as a git contributor on GitHub.
- NEVER add `Co-Authored-By:` trailers to any commit
- NEVER use `--author` with any AI tool name
- Make commits with the user's git identity only

## VENV — Activate Before Every Command
```bash
source backend/.venv/bin/activate
```
- Python 3.12 venv lives at `backend/.venv/`
- Without this: wrong Python, missing packages, pre-commit fails
- Do this FIRST, before any pip, pytest, ruff, mypy, or git commit command

## GIT — Non-negotiable Rules
- NEVER use `git add .` or `git add -A` — always stage files explicitly by name
- NEVER commit directly to `main`
- Always branch from `develop`: `git checkout -b feature/your-feature`
- One logical unit per commit (one function, one fix, one config change)
- Always activate venv before committing (pre-commit lives inside it)

## COMMIT MESSAGE FORMAT
```
type(scope): short description (max 72 chars)
```
Types: `feat` `fix` `test` `docs` `refactor` `perf` `chore` `revert` `wip`
Scopes: `audio` `vad` `asr` `llm` `tts` `ws` `api` `auth` `db` `cache` `pipeline` `scoring` `resume` `questions` `dashboard` `ci` `infra`

## AGENT HANDOFF — Do Before Switching Agents
1. `git add -p && git commit -m "wip: [what you were doing] — switching agents"`
2. Update CONTEXT.md (Current Task, What's Working, What's Blocked)
3. `git add CONTEXT.md && git commit -m "docs: update CONTEXT.md before agent switch"`
4. `git push origin [current-branch]`

## READ NEXT
See `CONTEXT.md` for full project state, architecture, and what's in progress.

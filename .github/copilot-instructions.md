# copilot-instructions.md — Mandatory Rules (GitHub Copilot)
# Read this first. Then read CONTEXT.md for full project state.

## 1. CONTRIBUTOR RULE
Only **Abhiyan Sainju** appears as a git contributor. Never add `Co-Authored-By:` or any AI attribution to any commit.

## 2. VENV — Do this before every command
```bash
source backend/.venv/bin/activate
```
Without this: wrong Python, missing packages, pre-commit fails.

## 3. GIT RULES
- Never `git add .` or `git add -A` — stage explicitly by name or `git add -p`
- Never commit directly to `main` — always branch from `develop`
- One logical unit per commit
- Branch naming: `feature/x`, `fix/x`, `chore/x`
- Commit format: `type(scope): description` — types: `feat` `fix` `test` `docs` `refactor` `chore` `wip`

## 4. BEFORE SWITCHING AGENTS
1. `source backend/.venv/bin/activate`
2. `git add -p && git commit -m "wip: [what you were doing] — switching agents"`
3. Update `CONTEXT.md` — Current Task, What's Working, What's In Progress, What's Blocked
4. `git add CONTEXT.md && git commit -m "docs: update CONTEXT.md before agent switch"`
5. `git push origin [current-branch]`

## 5. READ NEXT
**`CONTEXT.md`** — project state, architecture, what's working, what's blocked.

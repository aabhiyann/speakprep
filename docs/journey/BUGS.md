# BUGS.md — Bug Stories and Debugging Log

Format: ### BUG-N | Date | Title

---

### BUG-1 | 2026-04-25 | Accidentally installed dev tools into system Python instead of venv

**Phase:** Phase 0 — Task 0.1 (dependencies)
**Time to fix:** ~20 minutes

**The symptom:**
Running `ruff`, `mypy`, and `pre-commit` worked from the terminal, but they were the wrong version and not associated with the project. Running them inside the venv gave "command not found." Eventually noticed `which ruff` pointed to `/usr/local/bin/ruff` (system Python 3.11) instead of `backend/.venv/bin/ruff`.

**My debugging process:**
Ran `which ruff` and `which mypy` — both pointed to the system Python 3.11 install, not the project venv. Checked `pip list` inside the activated venv — the tools weren't there. Realized I had run `pip install ruff mypy pre-commit` without activating the venv first.

**Root cause:**
Forgot to run `source backend/.venv/bin/activate` before installing. pip defaulted to the system Python 3.11 environment.

**The fix:**
Uninstalled each tool from the system Python: `pip3.11 uninstall ruff mypy pre-commit`. Then activated the venv and reinstalled into it.

**Why it happened:**
New muscle memory needed — every terminal session must start with `source backend/.venv/bin/activate`. The shell gives no warning if you install to the wrong Python.

**The lesson:**
Now I always run `which python` and `which pip` immediately after opening a new terminal to confirm I'm in the right environment. Added "source backend/.venv/bin/activate" as the first line of CLAUDE.md so every agent session forces it.

---
**Interview version (STAR):**
Situation: Setting up the Python development environment for SpeakPrep, a FastAPI backend project.
Task: Install dev tools (ruff, mypy, pre-commit) into the project virtual environment.
Action: Discovered via `which ruff` that tools were installed into system Python 3.11 instead of the project venv. Uninstalled from system Python and reinstalled into the activated venv.
Result: Clean venv isolation. Added a mandatory venv activation step to all agent instruction files and made `which python` a habit after opening any new terminal.

---

### BUG-2 | 2026-04-25 | Homebrew updated Python 3.12, breaking the venv symlink

**Phase:** Phase 0 — Environment setup
**Time to fix:** ~30 minutes

**The symptom:**
After Homebrew auto-updated Python 3.12, the venv stopped working silently. Running `python` inside the activated venv printed confusing errors. `python --version` returned an error instead of 3.12.x. `pip install` failed with "python not found."

**My debugging process:**
Ran `ls -la backend/.venv/bin/python` and saw it was a symlink pointing to `/opt/homebrew/opt/python@3.12/bin/python3.12`. That path no longer existed — Homebrew had moved the Python binary to a new versioned path. The venv's internal symlinks were dead.

**Root cause:**
Python venvs store symlinks to the Python binary, not a copy of it. When Homebrew updates Python 3.12 to a new minor version (e.g., 3.12.3 → 3.12.13), it moves the binary to a new path. The old symlinks become dangling.

**The fix:**
```bash
brew install python@3.12   # ensures latest 3.12 is installed and linked
rm -rf backend/.venv       # delete the broken venv
python3.12 -m venv backend/.venv  # rebuild it
source backend/.venv/bin/activate
pip install -r requirements.txt requirements-dev.txt  # reinstall everything
```

**Why it happened:**
Homebrew's behavior of moving Python binaries on minor version updates is a known issue with venv-based workflows. The venv doesn't survive Python binary moves.

**The lesson:**
When the venv silently breaks, check `ls -la backend/.venv/bin/python` first — if it's a dangling symlink, rebuild the venv. Don't spend time debugging pip or Python itself.

---
**Interview version (STAR):**
Situation: Python 3.12 virtual environment for SpeakPrep stopped working after a Homebrew auto-update.
Task: Diagnose why `python` and `pip` were failing inside the activated venv with no obvious error.
Action: Checked the venv's Python symlink with `ls -la` and found it was pointing to a moved binary. Rebuilt the venv from scratch and reinstalled all dependencies.
Result: Working environment restored in ~10 minutes once the root cause was identified. Added venv rebuild steps to documentation for this known Homebrew gotcha.

---

### BUG-3 | 2026-04-25 | pre-commit not found when making commits

**Phase:** Phase 0 — Pre-commit hooks setup
**Time to fix:** ~10 minutes

**The symptom:**
Running `git commit` from a fresh terminal gave "pre-commit: command not found" or silently skipped hooks. The commit would succeed but with no hook checks.

**My debugging process:**
Ran `which pre-commit` — returned nothing or a path outside the venv. Activated the venv and ran `which pre-commit` again — now it found the right path. Made a test commit with the venv activated — hooks ran correctly.

**Root cause:**
pre-commit is installed inside the venv. The `.git/hooks/pre-commit` hook script calls `pre-commit run`, which requires `pre-commit` to be on the PATH. If the venv isn't activated, the hook can't find the command.

**The fix:**
Always run `source backend/.venv/bin/activate` before any `git commit`. This applies to agents too — added it as the first mandatory step in CLAUDE.md: "Do this before every command."

**Why it happened:**
The connection between "pre-commit is a Python package" and "the git hook calls that Python package" wasn't obvious. I expected git hooks to work independently of the Python environment.

**The lesson:**
pre-commit is a Python tool that lives in the venv. No venv = no pre-commit. Open every terminal session with venv activation and this never happens.

---
**Interview version (STAR):**
Situation: Pre-commit hooks set up for SpeakPrep were silently not running on commits from fresh terminals.
Task: Understand why commits succeeded without triggering ruff, mypy, and other quality checks.
Action: Checked pre-commit's PATH availability inside and outside the activated venv. Found that the git hook relied on a venv-installed binary that wasn't on PATH without venv activation.
Result: Added mandatory venv activation as the first line of every agent instruction file and personal workflow.

---

### BUG-4 | 2026-04-25 | gitleaks false positive on JWT test key in CI workflow

**Phase:** Phase 0 — GitHub Actions CI setup
**Time to fix:** ~15 minutes

**The symptom:**
The gitleaks pre-commit hook (secret scanner) blocked a commit to `.github/workflows/ci.yml` because the file contained a `JWT_SECRET_KEY` env var set to a placeholder test value (a 32-character string). gitleaks detected this as a hardcoded secret.

**My debugging process:**
Read the gitleaks output — it was flagging the JWT_SECRET_KEY environment variable in the CI workflow. The value was intentionally a non-secret test placeholder (not a real credential) used only in CI to run tests. It wasn't a real secret, but the pattern matched gitleaks' rules.

**Root cause:**
gitleaks uses pattern matching, not context. Any assignment to a key named `JWT_SECRET_KEY` triggers it, regardless of whether the value is a real secret or a test placeholder.

**The fix:**
Added `# gitleaks:allow` as an inline comment on the offending line in ci.yml. This tells gitleaks to suppress the rule for that specific line without disabling the scanner globally.
This tells gitleaks to suppress the rule for that specific line.

**Why it happened:**
Secret scanners are conservative by design — they'd rather have false positives than miss real secrets. Test keys that look like the real thing will always trigger them.

**The lesson:**
When gitleaks blocks a non-secret (test value, example key, placeholder), use `# gitleaks:allow` inline. Don't disable the whole hook — the false positive suppression is surgical.

---
**Interview version (STAR):**
Situation: Setting up GitHub Actions CI for SpeakPrep with a gitleaks secret scanning pre-commit hook.
Task: Commit the CI workflow file which contained a test JWT key value.
Action: gitleaks flagged the test key as a potential secret. Identified it as a false positive (intentional test placeholder), added `# gitleaks:allow` inline comment to suppress just that line without disabling the scanner.
Result: Commit succeeded, secret scanner remained active for real secrets. Learned the inline suppression pattern for false positives.

---

### BUG-5 | 2026-04-25 | Can't merge own PRs with enforce_admins=true

**Phase:** Phase 0 — Branch strategy
**Time to fix:** ~20 minutes

**The symptom:**
Created the first PR from `feature/phase0-setup` to `main`. Tried to merge it. GitHub blocked it with "At least 1 approving review is required." As the repo owner, I couldn't approve my own PR.

**My debugging process:**
Read the GitHub branch protection settings — `enforce_admins=true` applied all branch protection rules to administrators as well. The "require 1 approving review" rule required a second person to approve. As the sole contributor, I had no one to ask.

**Root cause:**
`enforce_admins=true` + "require 1 approving review" is designed for teams. For a solo project, it makes merging impossible without a workaround.

**The fix:**
Changed branch protection: set `enforce_admins=false`. This allows the repo owner to bypass the "require human reviewer" rule. CI checks (ruff, mypy, pytest) still run and still block merges on failure — the automated quality gates are preserved, just the human reviewer requirement is removed.

**Why it happened:**
Copied branch protection settings that assumed a team workflow without considering the solo-dev case.

**The lesson:**
enforce_admins=false is the correct setting for solo projects. The important protection (automated CI) still applies. Document this decision explicitly so a future collaborator knows to change it when the team grows. (See D-2.)

---
**Interview version (STAR):**
Situation: Set up strict branch protection on the SpeakPrep GitHub repo to enforce code quality, including enforce_admins=true.
Task: Merge the first feature branch PR after Phase 0 setup.
Action: GitHub blocked the merge requiring a second reviewer. Identified that enforce_admins=true prevents the solo developer from merging. Changed to enforce_admins=false while keeping CI-enforced quality gates active.
Result: Merged successfully. Documented the decision and the condition under which to revert it (when collaborators join).

---

### BUG-6 | 2026-04-25 | .gitignore `models/` matching backend/app/models/ and hiding it from git

**Phase:** Phase 0 — Repo setup
**Time to fix:** ~10 minutes

**The symptom:**
Running `git status` didn't show `backend/app/models/` as a new untracked directory after creating it. The directory existed on disk but git couldn't see it, so it couldn't be committed.

**My debugging process:**
Ran `git check-ignore -v backend/app/models/` — it reported that the `.gitignore` entry `models/` was matching. The `.gitignore` had `models/` to ignore ML model weight files (large binaries that shouldn't be in git). But `models/` matches any directory named `models` anywhere in the repo, including `backend/app/models/`.

**Root cause:**
In `.gitignore`, `models/` without a leading slash matches any directory named `models` at any depth. `backend/app/models/` was being silently ignored.

**The fix:**
Changed `.gitignore` from `models/` to `/models/`. The leading slash anchors the pattern to the repo root — it only ignores a `models/` directory at the top level, not nested ones.

**Why it happened:**
.gitignore pattern matching rules aren't obvious. A leading slash anchors to root. Without it, the pattern matches anywhere in the tree.

**The lesson:**
When a directory isn't showing up in `git status`, run `git check-ignore -v <path>` immediately — it tells you exactly which .gitignore rule is suppressing it and which file that rule is in.

---
**Interview version (STAR):**
Situation: Created `backend/app/models/` for SQLAlchemy models during SpeakPrep setup, but it didn't appear in `git status`.
Task: Figure out why git couldn't see the new directory.
Action: Used `git check-ignore -v backend/app/models/` to trace the suppression to a `.gitignore` entry `models/` intended only for ML model weights at the repo root. Changed `models/` to `/models/` to anchor it to the root only.
Result: `backend/app/models/` became visible to git. Learned the `git check-ignore` diagnostic command.

---

### BUG-7 | 2026-04-26 | Starlette 1.x: websocket.receive() returns disconnect dict instead of raising exception

**Phase:** Phase 0 — Task 0.3 (WebSocket echo server)
**Time to fix:** ~45 minutes

**The symptom:**
All three WebSocket integration tests failed with: `RuntimeError: Cannot call "receive" once a disconnect message has been received.`

The error came from inside `ws_echo.py` at `message = await websocket.receive()` — but only after the first message had already been processed successfully.

**My debugging process:**
Read the Starlette error carefully: "once a disconnect message has been received." This implied that somewhere before the crash, a disconnect message had already been received and the state machine had transitioned to DISCONNECTED. I wasn't handling that message.

Looked at the first implementation — it only had `except WebSocketDisconnect` as the disconnect handler. Searched Starlette 1.x changelog and source. Found that in 1.0.0, `receive()` returns `{"type": "websocket.disconnect"}` as a regular message instead of raising the exception. The state machine marks the connection DISCONNECTED. Any subsequent `receive()` call on a DISCONNECTED connection raises `RuntimeError`.

In my loop, after receiving the disconnect dict, the code fell through to `message.get("text")` (returning None), then `message.get("bytes")` (also None), then looped back to `await websocket.receive()` — which immediately raised `RuntimeError` because the connection was already DISCONNECTED.

**Root cause:**
Starlette 1.x breaking change: `receive()` returns disconnect as a message dict, not as an exception. The common pattern of relying solely on `except WebSocketDisconnect` is insufficient.

**The fix:**
Added an explicit type check at the top of the receive loop:
```python
message = await websocket.receive()
if message["type"] == "websocket.disconnect":
    log.info("client_disconnected", client_id=client_id)
    break
```

**Why it happened:**
The FastAPI documentation and most tutorials were written for pre-1.0 Starlette. The breaking change isn't prominently documented in the FastAPI docs — you have to read Starlette's changelog or hit the error to discover it.

**The lesson:**
When working with newer versions of FastAPI/Starlette, always check the ASGI message type explicitly rather than relying only on exception-based disconnect handling. `except WebSocketDisconnect` can still catch some cases (e.g., abnormal connection resets) but shouldn't be the only disconnect handler.

---
**Interview version (STAR):**
Situation: Implementing a WebSocket echo server for SpeakPrep using FastAPI and Starlette 1.x.
Task: Handle client disconnects gracefully — detect when the client closes the connection and exit the message loop cleanly.
Action: Tests were failing with RuntimeError on the second receive() call. Traced the issue to Starlette 1.x's changed disconnect behavior — it returns a disconnect message dict instead of raising WebSocketDisconnect. Added an explicit check for `message["type"] == "websocket.disconnect"` to break the loop before the state machine reached DISCONNECTED.
Result: All 3 integration tests passing. Documented this Starlette 1.x behavior in BUGS.md and LEARNINGS.md so future agents don't revert the fix (and one did anyway — see BUG-9).

---

### BUG-8 | 2026-04-26 | Heartbeat test: WebSocketDisconnect raised immediately before ping received

**Phase:** Phase 0 — Task 0.3 (WebSocket echo server tests)
**Time to fix:** ~20 minutes

**The symptom:**
The heartbeat test (`test_heartbeat_closes_unresponsive_connection`) was written to expect `WebSocketDisconnect` immediately, but the test was hanging — waiting indefinitely on `receive_text()`.

**My debugging process:**
Added print statements to the test. The server was sending the ping after 1 second (heartbeat_interval=1). The test was calling `receive_text()` expecting to get the WebSocketDisconnect, but it got the ping JSON instead. With the ping received but no pong sent back, the second `receive_text()` call should have gotten the disconnect — but the test was only making one receive call.

**Root cause:**
The test structure was wrong. The sequence is:
1. Connect
2. Wait 1 second → server sends `{"type": "ping"}`
3. Test does nothing (no pong sent)
4. Wait 1 more second → server closes connection → server sends disconnect

The test was trying to receive the disconnect on the first `receive_text()`, but that first call gets the ping. It blocks forever because the test never sends a pong and the server is still in the "waiting for pong" state when the first receive is made.

**The fix:**
Restructured the test to explicitly receive and assert the ping first, then wait for the disconnect:
```python
ping = ws.receive_text()             # first receive: gets the ping (~1s wait)
assert json.loads(ping)["type"] == "ping"
with pytest.raises(WebSocketDisconnect):
    ws.receive_text()                # second receive: gets disconnect (~1s later)
```

**Why it happened:**
Didn't think through the full message sequence. The heartbeat sends a ping before closing — the disconnect is the second message, not the first.

**The lesson:**
When testing protocols with multiple messages, map out the full expected message sequence before writing the test. The server's behavior was correct — the test's expectation was wrong.

---
**Interview version (STAR):**
Situation: Writing integration tests for the WebSocket heartbeat feature in SpeakPrep's echo server.
Task: Test that the server closes an unresponsive connection after ping timeout.
Action: Initial test hung waiting for WebSocketDisconnect on the first receive, but the first message was actually the ping. Mapped out the actual message sequence: (1) receive ping after 1s, (2) receive disconnect after another 1s. Restructured the test to receive and assert the ping first, then expect the disconnect.
Result: Test completes in ~2 seconds and passes reliably. Added comment explaining the timing to prevent future confusion.

---

### BUG-9 | 2026-04-26 | Other agent removed Starlette disconnect check, breaking all 3 WebSocket tests

**Phase:** Phase 0 — Phase completion
**Time to fix:** ~15 minutes

**The symptom:**
All 3 WebSocket integration tests that had been passing since BUG-7 was fixed suddenly failed again with the same `RuntimeError: Cannot call "receive" once a disconnect message has been received.`

**My debugging process:**
Ran `git diff backend/app/api/ws_echo.py`. The diff showed 6 lines deleted — specifically the entire `if message["type"] == "websocket.disconnect": break` block that was the fix from BUG-7.

Checked git log — the deletion wasn't in any commit. It was an uncommitted local modification in the working tree, not a committed change. Checked branch history — the committed version of the file was correct.

Another agent had opened `ws_echo.py` in their session, removed the disconnect check (perhaps thinking it was unnecessary since `except WebSocketDisconnect` existed), and left the file modified without committing or reverting.

**Root cause:**
Multi-agent file conflict. Two agents working on the same branch in overlapping sessions. One agent modified a file without understanding why a specific piece of code existed, then left without committing.

**The fix:**
The Edit tool restored the disconnect check. Since the committed version of the file was correct, the edit brought the working tree back into sync with HEAD. `git status` then showed nothing to commit.

**Why it happened:**
The CLAUDE.md handoff protocol exists exactly for this: "before switching agents, `git add -p && git commit`." The agent that removed the check didn't follow the handoff protocol — they left uncommitted changes that contaminated the next session.

Also: no comment explaining WHY the disconnect check existed. The check looks like dead code if you don't know about the Starlette 1.x behavior. This is one of the rare cases where a code comment is justified — the behavior is non-obvious and there's a real risk of "obviously wrong" removal.

**The lesson:**
1. Always follow the handoff protocol: commit before switching agents
2. Non-obvious workarounds deserve a comment: `# Starlette 1.x returns disconnect as dict, not exception`
3. `git diff <file>` is the first diagnostic when previously-passing tests suddenly fail

---
**Interview version (STAR):**
Situation: Managing multiple AI agents (Claude Code, Cursor) working on the same codebase for SpeakPrep.
Task: Maintain code correctness across agent handoffs.
Action: All 3 WebSocket tests failed after a second agent session. `git diff` revealed the other agent had deleted the critical Starlette 1.x disconnect check. The committed version was correct — restored the working tree and ran tests.
Result: Tests passing again in ~15 minutes. Tightened the agent handoff protocol: mandatory commit-and-push before switching, and added a comment to the disconnect check explaining the Starlette 1.x behavior.

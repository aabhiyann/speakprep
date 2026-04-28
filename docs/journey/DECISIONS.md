# DECISIONS.md — Technical Decisions Log

Format: ### D-N | Date | Title

---

### D-20 | 2026-04-27 | asyncio.to_thread for record_until_silence in async script

**The question I was facing:**
`VADRecorder.record_until_silence()` is a blocking synchronous method — it reads from the microphone using sounddevice's `RawInputStream`, blocking the calling thread until silence is detected. The `main()` and `run_voice_loop()` functions are `async def` and run under the asyncio event loop. If I call a blocking function directly inside `async` code, what actually happens?

**Options I considered:**
Option A — Call it directly: `audio = recorder.record_until_silence()`. The code is simple. But: this blocks the event loop thread for the entire duration of the recording (could be 2-60 seconds). During that time, no other coroutines can run — no asyncio tasks, no timeouts, nothing. For a single-user local script this is acceptable in theory, but it's incorrect practice and will cause bugs if the script ever gets more async logic (like a timeout for long silences, or cancellation on Ctrl+C during recording).

Option B — `await asyncio.to_thread(recorder.record_until_silence)`: runs the blocking function in a thread pool and suspends the coroutine at the `await` — the event loop stays free. The microphone blocking happens in a real OS thread, not in the event loop thread. The coroutine resumes when `record_until_silence` returns.

**What I chose:** Option B — asyncio.to_thread

**Why:**
The script's main loop is already fully async (LLMService.generate is async, tts_and_play is async). Mixing blocking calls into an async loop without `to_thread` is a pattern that "works" until it doesn't — and silently degrades behavior (KeyboardInterrupt during blocking mic read behaves differently than during awaited calls, asyncio timeouts won't fire). Using `to_thread` consistently for all blocking I/O makes the code correct by default and extends naturally to the production WebSocket handler where blocking the event loop is catastrophic. This is the same decision made for faster-whisper inference in D-9.

**What I'm giving up:**
Marginal complexity. The call is one extra word: `await asyncio.to_thread(...)` vs `recorder.record_until_silence()`. Trivial.

**How I'll know if I was wrong:**
If sounddevice or PortAudio behaves incorrectly when called from a non-main thread. In practice, sounddevice is thread-safe and this pattern is well-established in the Python audio community.

**Interview answer version:**
"Even in a local script, I used asyncio.to_thread for the blocking mic read because the main loop is async and mixing blocking calls into an async context is an antipattern — it defeats the event loop's cooperative scheduling. The same call structure I used for faster-whisper inference in LocalASR."

---

### D-19 | 2026-04-27 | collections.deque(maxlen=8) for conversation history

**The question I was facing:**
The interview loop accumulates messages (user transcripts and AI responses) in a conversation history list that gets sent to the LLM on every turn. Without a cap, this list grows indefinitely. A 30-minute interview at 1 turn per 30 seconds = 60 turns = 120 messages. How do I keep the history bounded?

**Options I considered:**
Option A — Manual slice: `history = history[-8:]` at the end of each turn (or before sending to LLM). Simple but easy to forget one call site, and it creates a new list on every turn. If history is long, this copies a lot of memory unnecessarily.

Option B — `deque(maxlen=8)`: Python's standard library double-ended queue with a fixed maximum length. When a new item is appended and the deque is full, the oldest item is automatically evicted. Zero manual truncation code. The `maxlen` invariant is enforced by the data structure itself, not by the programmer.

Option C — Keep full history, truncate only when calling LLM: `messages = [system_prompt] + list(history)[-8:]`. Sends only the last 8 but stores all of them. Useful if you want a full transcript for analytics but only send a window to the LLM.

**What I chose:** Option B — deque(maxlen=8)

**Why:**
For a proof-of-concept, the full transcript isn't needed. Memory is also finite — storing a multi-hour interview history in RAM is wasteful for a local POC. The deque is the right abstraction: it makes the "sliding window of recent context" semantics explicit in the type itself. A reader who sees `deque(maxlen=8)` immediately understands the intention. A reader who sees `history = history[-8:]` has to understand that this is the truncation mechanism.

The 8-message limit (4 turns of user+assistant) is a practical choice: enough context for the interviewer to track what the candidate said, not so much that it dominates the prompt. Groq's Llama 3.3 70B can handle far more, but the system prompt for a behavioral interviewer is short and 8 messages is plenty for coherent follow-up.

**What I'm giving up:**
Full transcript history. If we want to show the user a complete session summary at the end, we'd need a separate `full_history` list. Acceptable for a POC — Phase 3+ will have database logging.

**How I'll know if I was wrong:**
If the LLM produces incoherent follow-ups that require more context to make sense. In practice, interview follow-up questions are self-contained — each question responds to the immediately preceding answer.

**Interview answer version:**
"I used collections.deque with maxlen=8 for conversation history because it enforces the sliding window invariant automatically — no manual truncation code, no risk of forgetting to truncate at one call site. The maxlen makes the constraint explicit in the data structure itself."

---

### D-18 | 2026-04-27 | afplay subprocess over PyAV decode for TTS audio playback

**The question I was facing:**
edge_tts produces audio as MP3 bytes. To play it locally I need to either: (a) decode the MP3 to PCM and play with sounddevice, or (b) save to a temp file and use a system audio player. Both approaches work. Which is right for this script?

**Options I considered:**
Option A — PyAV decode + sounddevice: `av` (PyAV) is already installed in the project venv. It can decode MP3 bytes to a PCM numpy array using `av.open(io.BytesIO(mp3_bytes))`, then `sd.play(pcm_array, samplerate=24000)`. Cross-platform, no system dependencies, no temp file. Cons: more code (15-20 lines of PyAV audio container/stream/frame iteration), needs to query sample rate from container headers, and the resulting code is significantly more complex than a two-line subprocess call.

Option B — Save to temp file + afplay: `await communicate.save(tmp_path)` writes the MP3 to a temporary file. `subprocess.run(["afplay", tmp_path])` plays it. `afplay` is a macOS built-in — available on every Mac without any installation. It handles MP3 decoding internally (CoreAudio), is always the right sample rate, and the entire TTS play logic is 5 lines. Cons: requires writing to disk (temp file), macOS-only.

**What I chose:** Option B — afplay via subprocess

**Why:**
This script is explicitly a local macOS proof-of-concept. The dev machine is macOS (darwin). `afplay` is always available. The deployment target for production is an Oracle Cloud ARM server running Linux where audio playback is irrelevant — TTS audio in production goes directly to the browser over WebSocket as binary chunks. The macOS-only constraint is not a constraint for this file. Adding 15 lines of PyAV buffer manipulation for "cross-platform" support in a file that will never run cross-platform is engineering the wrong thing.

The temp file approach adds one disk write (~50-200KB MP3 file) but the file is deleted immediately after playback in the `finally` block. On an SSD this is milliseconds.

**What I'm giving up:**
Cross-platform audio playback and playing from memory without a temp file. Both are irrelevant for a local macOS script.

**How I'll know if I was wrong:**
If anyone needs to run `local_voice_loop.py` on Linux. If that happens: replace `afplay` with `mpg123 -q` (Linux) or use the PyAV approach.

**Interview answer version:**
"For a local macOS proof-of-concept, I used subprocess to call macOS's built-in afplay rather than decoding MP3 with PyAV. The production TTS path sends audio bytes over WebSocket — no local playback needed there. Using the right tool for the scope: system player for local dev, binary WebSocket frames for production."

---

### D-17 | 2026-04-27 | edge_tts over Kokoro for Phase 1 local POC

**The question I was facing:**
The architecture document specifies Kokoro TTS as the production TTS engine (self-hosted, sub-100ms, high quality). But Kokoro requires Docker, at least 4GB RAM for the model, and GPU for low latency. For the Phase 1 local proof-of-concept, should I use Kokoro or a simpler alternative?

**Options I considered:**
Option A — Kokoro TTS: matches the production stack. Self-hosted, no cloud dependency, potentially very fast with GPU. Cons: requires Docker running locally, downloading the Kokoro model (~2GB+), a GPU for acceptable latency (CPU inference on Kokoro is very slow), and significant setup time. The POC's purpose is to validate the ASR → LLM → TTS pipeline end-to-end quickly — Kokoro setup would take hours and be a distraction.

Option B — edge_tts (Microsoft Edge TTS): single `pip install`, no API key, no Docker, no GPU. Makes a network request to Microsoft's TTS service (the same one used in the Edge browser) and returns MP3 audio. Good voice quality (Aria neural voice sounds natural). Cons: requires internet, uses Microsoft's cloud service (not self-hosted), adds ~2-3 seconds of network latency for TTS. Acceptable for a POC where latency is not the primary goal.

Option C — pyttsx3 (offline TTS): completely local, no network. Cons: robotic voice quality, system-dependent (different voices on Windows/macOS/Linux), actively distracting because the output sounds so bad it's hard to evaluate whether the LLM responses are good.

**What I chose:** Option B — edge_tts

**Why:**
The Phase 1 POC has one purpose: validate that the full pipeline works. The question is "does it work?" not "is it fast?" edge_tts answers that question well — the audio quality is good enough that you can actually evaluate the interview conversation, the setup is one pip install, and the library has a clean async API that matches the rest of the async codebase. Kokoro is the right choice for Phase 2+ when latency matters and the production environment is established.

This is an explicit "don't build the production solution in the proof-of-concept phase" decision. Premature optimization of the TTS component would delay the POC by a day and provide no additional learning.

**What I'm giving up:**
Matching the production TTS stack. If Kokoro has integration issues (HTTP streaming, audio format), those would be caught later in Phase 2. Acceptable tradeoff — the POC validates ASR→LLM more than TTS.

**How I'll know if I was wrong:**
If the edge_tts API or audio format causes issues that mask real pipeline problems. Unlikely — it's a simple `save()` call.

**Interview answer version:**
"For the Phase 1 local POC I chose edge_tts (Microsoft's Edge TTS, one pip install) over the production Kokoro TTS (self-hosted Docker, requires GPU). The POC's goal was pipeline validation, not latency optimization. Production TTS (Kokoro) gets integrated in Phase 2 when the server infrastructure exists."

---

### D-13 | 2026-04-27 | _Provider as dataclass not abstract base class

**The question I was facing:**
Three providers (Groq, Cerebras, Gemini) each have different SDK clients and models. How do I abstract over them so `generate()` can iterate them uniformly without giant if/elif chains everywhere?

**Options I considered:**
Option A — Abstract base class (ABC): define `BaseProvider` with `@abstractmethod complete(...)` and `@abstractmethod stream(...)`. Subclass: `GroqProvider`, `CerebrasProvider`, `GeminiProvider`. Cons: 3 extra classes, verbose, overkill for 3 providers that mostly just call their SDK. The abstraction leaks anyway (Gemini needs message format conversion that the others don't).
Option B — `_Provider` dataclass bundling `name`, `client`, `model`, `circuit_breaker`. The dispatch logic (`_call_groq`, `_call_cerebras`, `_call_gemini`) lives in `LLMService` as private methods. `generate()` iterates `self._providers` and dispatches via `_call_provider(provider, ...)` which has a small if/elif.

**What I chose:** Option B — dataclass

**Why:**
Three providers is not enough to justify a class hierarchy. The dataclass captures the data (name, client, model, circuit breaker) and the `LLMService` methods capture the behavior. Behavior is per-provider type, not per-provider instance — so it belongs in dispatch methods, not in subclasses. If a fourth provider appeared that needed fundamentally different behavior (e.g. a local model with no SDK), that's when an ABC makes sense.

**What I'm giving up:**
Open/closed principle — adding a provider means touching `_setup_providers`, adding a `_call_<name>` method, and adding a case to `_call_provider`. With ABC, you'd only add a new subclass. Acceptable tradeoff for 3 providers.

**How I'll know if I was wrong:**
If provider count grows past 5-6 and `_call_provider` becomes a long if/elif chain. At that point, extract a protocol/ABC.

**Interview answer version:**
"I used a dataclass over an ABC because three providers don't justify a class hierarchy — the dispatch logic is simple enough to live in private methods. If the provider list grew significantly I'd extract a protocol."

---

### D-14 | 2026-04-27 | Injectable clock for CircuitBreaker tests

**The question I was facing:**
`CircuitBreaker` checks `time.time()` to decide if 60 seconds have passed and it's time to go HALF_OPEN. How do I test the 60-second timeout without actually sleeping 60 seconds in tests?

**Options I considered:**
Option A — `monkeypatch.setattr(time, 'time', ...)`: pytest's monkeypatch globally replaces `time.time` for the duration of the test. Works, but the patch affects every piece of code running in that test — risky if something else also calls `time.time()`. Also less explicit about intent.
Option B — Injectable clock: `def __init__(self, ..., _clock=time.time)`. Default is real time. Tests pass `_clock=lambda: fake_time[0]` and control the fake time by mutating `fake_time[0]`. No global state, no side effects on other code.

**What I chose:** Option B — injectable clock

**Why:**
The injectable pattern is explicit about which object is time-dependent. It requires no test framework magic — it's just a function argument. It generalizes to any time-sensitive class: use `_clock=time.time` as the default and inject in tests. This is the dependency injection pattern applied to time.

**What I'm giving up:**
The `_clock` parameter is slightly unexpected to a reader who hasn't seen this pattern. Convention is to name it `_clock` (underscore prefix) to signal "internal/testing use only, don't pass this in production."

**How I'll know if I was wrong:**
If I find myself needing to patch `time.time` globally anyway for some reason. Hasn't happened.

**Interview answer version:**
"The circuit breaker needed time.time() to check the 60-second recovery timeout. Rather than monkeypatching the global, I injected the clock function as a constructor parameter with a default of time.time. Tests pass a lambda over a mutable list to control the clock. This is dependency injection applied to time."

---

### D-15 | 2026-04-27 | try/except ImportError for optional providers

**The question I was facing:**
Cerebras and Gemini SDKs aren't installed in the project venv. How do I write code that uses them when they're present without crashing when they're absent?

**Options I considered:**
Option A — Require all packages: add cerebras-cloud-sdk and google-generativeai to requirements.txt. Everyone must install them. Cons: adds hundreds of MB of dependencies for packages that may never be used. Also requires API keys for packages you can't use without accounts.
Option B — Conditional import at usage site: check `os.getenv("CEREBRAS_API_KEY")` and only then `from cerebras.cloud.sdk import ...`. Cons: the import inside an `if` block confuses type checkers and is hard to reason about.
Option C — `try/except ImportError` at module level: attempt the import at module load time, set `_CEREBRAS_AVAILABLE = True/False`. Usage code checks the flag. Type: `AsyncCerebras = None` as fallback satisfies references without crashing.

**What I chose:** Option C — try/except at module level

**Why:**
Module-level imports are visible, predictable, and happen once. The `_CEREBRAS_AVAILABLE` flag is a clear signal. `_setup_providers()` reads both the flag and the API key — both must be present to add the provider. Type checkers are satisfied with `# type: ignore[assignment]` on the `None` fallback.

**What I'm giving up:**
The `type: ignore` comments are slightly ugly. A full solution would use `TYPE_CHECKING` guards and conditional type stubs.

**How I'll know if I was wrong:**
If the optional packages start failing silently in production in a way that's hard to debug. Mitigation: the structlog warning when a provider isn't available would make this visible.

**Interview answer version:**
"For optional provider SDKs, I use try/except ImportError at module level and set an availability flag. The service constructor checks both the flag and the API key before adding a provider. This follows the pattern used in popular libraries like SQLAlchemy for optional drivers."

---

### D-16 | 2026-04-27 | async generator for stream()

**The question I was facing:**
`stream()` needs to yield tokens as they arrive from the LLM API. What's the right return type and structure?

**Options I considered:**
Option A — Collect all tokens, return a list: `chunks = []; async for c in api_stream: chunks.append(c); return chunks`. Simple. Cons: destroys streaming — the caller doesn't see the first token until the last token arrives. For a voice app where responsiveness matters, this is wrong.
Option B — Return a callback: `stream(messages, on_token: Callable[[str], None])`. Caller passes a function that gets called for each token. Works but awkward — you can't use it in `async for`, can't chain it, hard to test.
Option C — `async def` + `yield` = async generator. The function returns an `AsyncGenerator[str, None]` (satisfies `AsyncIterator[str]`). Caller does `async for chunk in service.stream(messages)`. Natural, composable, testable. Falls back to `generate()` if streaming fails — yields the full response as one chunk.

**What I chose:** Option C — async generator

**Why:**
Async generators are the standard Python pattern for asynchronous sequences. They compose naturally with `async for`, work with FastAPI's streaming responses, and can be collected into a list in tests with `chunks = [c async for c in service.stream(...)]`. The fallback path (`yield response.content`) is a single yield — the caller doesn't know or care whether it came from streaming or not.

**What I'm giving up:**
Slightly harder to type-annotate correctly. The return annotation is `AsyncIterator[str]` but the runtime type is `AsyncGenerator[str, None]`. Both are correct (AsyncGenerator is a subtype of AsyncIterator).

**Interview answer version:**
"LLM streaming returns tokens one at a time. I used an async generator — async def with yield — so callers can consume tokens as they arrive with async for. This is the natural Python pattern for async sequences and composes directly with FastAPI's StreamingResponse."

---

### D-9 | 2026-04-26 | asyncio.to_thread for faster-whisper inference

**The question I was facing:**
`LocalASR.transcribe()` is an async method, but faster-whisper inference is CPU-bound and synchronous. How do I call it from async code without freezing the server?

**Options I considered:**
Option A — Call it directly: `segments, info = self._model.transcribe(audio_f32)`. Simplest. Cons: faster-whisper inference takes 2-5 seconds on CPU. During that time the entire event loop is blocked — no pings, no other WebSocket messages, no health checks can run. One transcription request freezes every connected client.
Option B — `asyncio.to_thread(self._transcribe_sync, audio)`: runs the sync function in Python's default thread pool executor. Event loop awaits the result but is free to run other coroutines while the thread works. CTranslate2 (the C library underlying faster-whisper) releases the GIL during matrix operations, so actual CPU work runs in parallel with the event loop.

**What I chose:** Option B — asyncio.to_thread

**Why:**
SpeakPrep is a multi-client voice server. If one user's transcription freezes everyone else, the product is unusable. `asyncio.to_thread` is exactly the right tool for CPU-bound work you can't rewrite as async — it moves the blocking work to a thread pool without requiring any changes to the sync logic.

**What I'm giving up:**
Slightly more complex call structure. The sync business logic lives in `_transcribe_sync`, the async wrapper in `transcribe`. This split is intentional and actually improves testability — you can unit-test `_transcribe_sync` directly in a sync context.

**How I'll know if I was wrong:**
If profiling shows the thread pool is saturating (all workers busy) during peak load. At that point, switch to a GPU or move transcription to a separate process with `ProcessPoolExecutor`.

**Interview answer version:**
"faster-whisper is CPU-bound so I wrapped it with asyncio.to_thread — this runs inference in a thread pool and keeps the event loop free. CTranslate2 releases the GIL during computation, so it runs genuinely in parallel with the event loop thread rather than just context-switching."

---

### D-10 | 2026-04-26 | Materialise faster-whisper generator with list() before filtering

**The question I was facing:**
`model.transcribe()` returns `(segments_generator, info)`. Should I iterate the generator directly or convert it to a list first?

**Options I considered:**
Option A — Iterate directly: `max(s.no_speech_prob for s in segments_iter)`. Fewer allocations. Cons: a generator is a one-time iterable — after the first `max()` exhausts it, the second `max(s.compression_ratio ...)` sees nothing and raises `ValueError: max() arg is an empty sequence`.
Option B — Materialise with `list()`: `segments = list(segments_iter)`. Iterate twice safely. Minor memory overhead.

**What I chose:** Option B — materialise with list()

**Why:**
Correctness over micro-optimisation. We need to apply two independent filters (`no_speech_prob` and `compression_ratio`) and then join segment texts — that's three passes over the data. Short utterances from VADRecorder are typically 2-10 seconds and produce at most 3-5 segments. The list is tiny.

**What I'm giving up:**
Nothing meaningful. Materialising 5 small objects is not a performance concern.

**Interview answer version:**
"faster-whisper returns a lazy generator that can only be iterated once. I materialise it with list() immediately because I need to apply two independent filters and then join the text — that requires multiple passes over the segments."

---

### D-11 | 2026-04-26 | Use max() across all segments for hallucination filtering

**The question I was facing:**
When checking `no_speech_prob` and `compression_ratio`, should I filter per-segment (drop individual bad segments) or use the worst-case value to filter the entire utterance?

**Options I considered:**
Option A — Per-segment filtering: drop segments where `no_speech_prob > 0.6`, keep the rest. Could salvage partial utterances. Cons: produces incomplete text mid-utterance (e.g., drops the middle of a sentence), which creates worse output than returning nothing.
Option B — Worst-case across all segments: if ANY segment has `no_speech_prob > 0.6`, return `None` for the whole utterance. More conservative. Guarantees either clean complete output or nothing.

**What I chose:** Option B — max() across all segments

**Why:**
For interview coaching, a partial or garbled transcript is worse than no transcript. If the LLM receives "Tell me about... [garbled middle]... that's why I think" it produces a nonsensical response. Returning `None` triggers a "sorry, could you repeat that?" response instead, which is a better user experience.

**What I'm giving up:**
Occasionally filtering genuinely valid short utterances that happen to contain a noisy segment. In Phase 2, Deepgram (the primary ASR) handles this better with streaming — this filter only applies to the offline fallback.

**Interview answer version:**
"I use max() across all segments rather than per-segment filtering because a partial transcript mid-utterance produces worse LLM responses than returning nothing. The offline Whisper fallback should fail clean — the primary Deepgram path handles noisy audio better."

---

### D-12 | 2026-04-26 | WhisperModel initialised once in __init__, not per transcription

**The question I was facing:**
Should `WhisperModel` be created once when `LocalASR` is instantiated, or on each call to `transcribe()`?

**Options I considered:**
Option A — Per-call initialisation: `model = WhisperModel("small", ...)` inside `transcribe()`. Avoids holding a large object in memory between calls. Cons: loading WhisperModel takes 10-30 seconds and requires downloading/reading ~500MB of model weights. Per-call initialisation means the first transcription of every request takes 30 seconds.
Option B — Once in `__init__`: model loaded when the service starts, reused for every transcription. Loading happens once at server startup, each call costs only inference time (~4s on CPU).

**What I chose:** Option B — once in __init__

**Why:**
A 30-second transcription latency is not a product — it's a broken product. Model loading is a one-time startup cost. The memory (~500MB for small INT8) is acceptable on the target hardware (Oracle Cloud ARM with 6GB RAM). This is standard practice for all ML inference services: load model at startup, keep it warm.

**What I'm giving up:**
Memory: the model occupies RAM even during idle periods. On low-memory machines, this matters. Mitigation: use `tiny` model (150MB) for very constrained environments.

**Interview answer version:**
"WhisperModel is loaded once at startup, not per-request — loading takes 10-30 seconds. This is standard ML inference practice: pay the startup cost once, then each inference is just computation. The model stays in memory warm for all requests."

---

### D-1 | 2026-04-25 | pip + venv instead of Poetry

**The question I was facing:**
The dev playbook assumed Poetry for dependency management. Poetry is the modern standard for Python projects and handles virtual environments automatically. Do I use it or switch to plain pip?

**Options I considered:**
Option A — Poetry: automatic venv management, lock files, dependency groups (prod/dev), good tooling. Cons: another tool to install and learn, adds a `pyproject.toml` abstraction layer, CI setup is slightly different, and I've never used it before.
Option B — pip + venv manually: standard Python, no extra tools, requirements.txt is universally understood, every tutorial and CI example uses it. Cons: no lock file by default, venv must be activated manually, no dependency groups (manual split into requirements.txt + requirements-dev.txt).

**What I chose:** Option B — pip + venv

**Why:**
I'm already learning FastAPI, asyncio, WebSockets, voice AI, and cloud deployment simultaneously. Adding Poetry on top means debugging Poetry issues instead of debugging my code. pip is the baseline — it works everywhere, it's what CI expects by default, and every Stack Overflow answer is in pip. When I'm more comfortable with the stack I can migrate.

**What I'm giving up:**
No automatic lock file for transitive dependencies. `pip freeze > requirements.txt` gives me pinned versions, but it's not as robust as Poetry's `poetry.lock`. Also no automatic venv management — must always run `source backend/.venv/bin/activate` first.

**How I'll know if I was wrong:**
If dependency conflicts start causing CI failures that are hard to debug, or if I need complex dependency groups that requirements.txt can't express cleanly.

**Interview answer version:**
"I chose pip over Poetry to reduce cognitive load — I was learning multiple new technologies simultaneously and adding another tool would have meant debugging Poetry instead of my application. The tradeoff is less robust dependency resolution, which I accepted because the project has a stable, well-known dependency set."

---

### D-2 | 2026-04-25 | enforce_admins=false for branch protection

**The question I was facing:**
GitHub branch protection with `enforce_admins=true` means even the repo owner needs a PR review before merging. For team repos this is essential. But I'm the only contributor. Do I enforce it?

**Options I considered:**
Option A — enforce_admins=true: maximum protection, no accidental direct pushes even from myself, mirrors what real teams use. Cons: I can't merge my own PRs without a second reviewer, which is impossible when I'm solo.
Option B — enforce_admins=false: I can merge my own PRs. CI still runs on every PR, ruff/mypy/pytest still gate merges. Only the "second human reviewer" requirement is removed. Cons: slightly less protection against my own mistakes.

**What I chose:** Option B — enforce_admins=false

**Why:**
CI still runs on every PR. The ruff, mypy, and pytest checks still gate merges — I can't merge broken code. The only thing removed is human review, which I can't provide for myself anyway. The protection that matters (automated quality checks) is still in place.

**What I'm giving up:**
A second set of eyes on every PR. Any mistake I make in code review I won't catch. If/when collaborators join, I should switch enforce_admins back to true.

**How I'll know if I was wrong:**
If I accidentally merge something that breaks main because I rubber-stamped my own review.

**Interview answer version:**
"For a solo project, I kept CI-enforced quality gates (lint, type check, tests) but removed the human review requirement since I can't review my own code. I documented this decision explicitly so the setting can be changed when collaborators join."

---

### D-3 | 2026-04-25 | CONTEXT.md as single source of truth, agent files as rules-only

**The question I was facing:**
Each AI agent (Claude Code, Cursor, Codex, Copilot) needs instruction files. Should those files contain the full project context (architecture, what's working, what's blocked), or just rules?

**Options I considered:**
Option A — Full context in each agent file: each file has architecture, stack, what's done, what's next. Agents always have full context without reading another file. Cons: each file is 100+ lines, duplicated everywhere, gets out of sync, eats the agent's context window with information that's already in the file the agent just read.
Option B — Rules-only in agent files, CONTEXT.md as the single state document: agent files are ~30 lines of mandatory rules (contributor, venv, git, commit format, handoff protocol). CONTEXT.md has all project state and is updated after every task. Cons: agents must be explicitly told to read CONTEXT.md; if they don't, they lack project context.

**What I chose:** Option B — rules-only agent files

**Why:**
An agent's context window is finite and expensive. A 100-line agent file that repeats the architecture on every session is a waste. The rules (never add Co-Authored-By, always activate venv, never git add -A) are stable and belong in the instruction file. Project state (current task, what's working, what's blocked) changes constantly and belongs in one place that's explicitly updated.

**What I'm giving up:**
Agents that don't read CONTEXT.md first will lack project context. The instruction files must explicitly say "read CONTEXT.md first" as the first rule.

**Interview answer version:**
"I separated concerns between instruction files (stable rules: contributor policy, venv activation, git discipline) and CONTEXT.md (dynamic state: current task, what's working, what's blocked). This kept instruction files minimal and put project state in one authoritative place that gets updated with every commit."

---

### D-4 | 2026-04-26 | heartbeat_interval and heartbeat_timeout as query parameters

**The question I was facing:**
The WebSocket echo server has a 30s heartbeat interval and 5s pong timeout. Testing this would take 35 seconds per test. Should these values be hardcoded or configurable?

**Options I considered:**
Option A — Hardcoded: simpler code, no parameters to document. Cons: the heartbeat test takes 35 seconds. A test suite that takes 35 seconds to run is a suite you stop running frequently.
Option B — Query parameters with defaults: `/ws/echo/{id}?heartbeat_interval=1&heartbeat_timeout=1` for tests, `/ws/echo/{id}` uses 30s/5s defaults in production. Cons: slightly more complex signature, query params on WebSocket URLs are unusual.

**What I chose:** Option B — configurable via query params

**Why:**
Fast tests are tests you actually run. The test completes in ~2 seconds instead of ~35 seconds. The query param approach is clean in FastAPI — it reads exactly like an HTTP query param and defaults to the production values. The production behavior is unchanged.

**What I'm giving up:**
Slightly unusual API surface — WebSocket URLs with query params aren't commonly seen. Someone reading the URL might be confused. Documented in the test comment.

**Interview answer version:**
"I made the heartbeat interval a query parameter with a production default so tests could run in 2 seconds instead of 35. Fast feedback loops matter more than a clean URL surface in a development-stage API."

---

### D-5 | 2026-04-25 | retry_with_backoff takes a Callable, not a Coroutine

**The question I was facing:**
`retry_with_backoff` needs to re-run the operation on each retry. Should it accept a coroutine (the result of calling an async function) or a callable (the function itself)?

**Options I considered:**
Option A — Accept a Coroutine: caller passes `retry_with_backoff(fetch_data())`. Simpler call site. Cons: a coroutine is a one-time use object. Once it's been awaited (or failed), it's done. You can't re-run it. Retrying a coroutine would either silently return a stale result or raise an error.
Option B — Accept a Callable: caller passes `retry_with_backoff(fetch_data)`. Slightly more awkward (no parentheses at call site). But on each retry, the function calls `coro_func()` to get a fresh coroutine, which starts the operation from scratch.

**What I chose:** Option B — Callable

**Why:**
The whole point of retry is re-running the operation. A coroutine can't be re-run. This is a correctness requirement, not a preference. Using a coroutine would produce silently wrong behavior.

**What I'm giving up:**
Slightly less convenient call site. Caller must remember not to add `()` when passing the function. Easy to confuse once, but the type signature catches it: `Callable[[], Coroutine]` not `Coroutine`.

**Interview answer version:**
"retry_with_backoff takes a callable, not a coroutine, because a coroutine is a one-time-use object — you can't re-run it. To retry the operation you need to call the function again to get a fresh coroutine each time. This is a correctness requirement."

---

### D-6 | 2026-04-26 | websocket.receive() instead of receive_text() or receive_bytes()

**The question I was facing:**
FastAPI/Starlette offers typed receive methods: `receive_text()`, `receive_bytes()`, and the raw `receive()`. Which to use in the main loop of the echo server?

**Options I considered:**
Option A — `receive_text()` / `receive_bytes()`: cleaner, self-documenting. Cons: each method only handles one type. To handle both text and binary you'd need two separate code paths, and more critically, neither handles the disconnect message — they raise an exception on disconnect rather than returning the message dict.
Option B — Raw `receive()`: returns a dict with `type`, `text`, or `bytes` fields. Handles all message types in one place. With Starlette 1.x, the disconnect message (`{"type": "websocket.disconnect"}`) is returned as a normal message, not raised as an exception.

**What I chose:** Option B — raw `receive()`

**Why:**
Starlette 1.x changed disconnect behavior: `receive()` returns the disconnect message as a dict instead of raising `WebSocketDisconnect`. Using the typed helpers would make the disconnect case raise `RuntimeError: Cannot call receive once a disconnect message has been received` — because the typed helper calls `receive()` internally, gets the disconnect dict, and then the state machine is in DISCONNECTED state, so any subsequent call raises. The raw `receive()` lets you handle the disconnect explicitly with a type check.

**What I'm giving up:**
Less obvious code. A reader who doesn't know about the Starlette 1.x change will find the raw dict handling confusing. This is exactly why the BUGS.md entry exists — so future me (and other agents) know why this decision was made.

**Interview answer version:**
"I used raw `receive()` instead of `receive_text()` because Starlette 1.x changed how disconnects work — they return a message dict instead of raising an exception. The raw method lets you explicitly check the message type and handle all cases without the state machine error."

---

### D-7 | 2026-04-26 | Cast to int32 before abs() in audio_stats

**The question I was facing:**
Computing max amplitude requires `np.abs()` on an int16 audio array. Should I cast to a larger type first?

**Options I considered:**
Option A — `np.abs(audio_int16)` directly: simpler, one line. Cons: silent integer overflow. `abs(-32768)` in int16 is undefined because +32768 doesn't fit in int16 (max is 32767). NumPy wraps around and returns -32768, so the max amplitude of the loudest possible sample reports as a negative number.
Option B — `audio_int16.astype(np.int32)` first, then `np.abs()`: one extra line but correct. int32 can hold +32768 without overflow.

**What I chose:** Option B — cast to int32 first

**Why:**
Correctness. Silent data corruption that happens to look plausible (wrong but reasonable-looking numbers) is the worst kind of bug. The amplitude of the loudest possible int16 sample reporting as -32768 instead of 32768 would make silence detection wrong in edge cases.

**What I'm giving up:**
One extra line of code. Trivial.

**Interview answer version:**
"I cast int16 audio to int32 before taking absolute values because `abs(-32768)` overflows int16 — the result wraps to -32768 instead of 32768. This is silent data corruption that would make the max amplitude of the loudest sample report as a large negative number."

---

### D-8 | 2026-04-26 | Divide by 32768 (not 32767) in pcm_to_float32

**The question I was facing:**
When normalizing int16 PCM to float32 [-1.0, 1.0], what number do you divide by? The min int16 value is -32768, the max is 32767. They're not symmetric.

**Options I considered:**
Option A — Divide by 32767: the max positive value maps exactly to +1.0. But -32768 / 32767 = -1.0000305..., which is slightly outside [-1.0, 1.0]. Some audio processing code breaks on values outside that range.
Option B — Divide by 32768: the most negative value maps exactly to -1.0 (32768/32768). The most positive value maps to 32767/32768 ≈ 0.99997, never quite reaching +1.0. The range is guaranteed to be within [-1.0, 1.0].

**What I chose:** Option B — divide by 32768

**Why:**
The float32 output is guaranteed to stay within [-1.0, 1.0]. Downstream audio processing libraries (Faster-Whisper, numpy FFT, etc.) expect normalized float audio in that range and may produce incorrect results or errors on values outside it. Losing 0.003% of precision on the positive side is not a meaningful tradeoff.

**What I'm giving up:**
The positive side can never exactly reach +1.0 (32767/32768 ≈ 0.99997). In practice this is inaudible and computationally irrelevant.

**Interview answer version:**
"I divide by 32768 not 32767 when normalizing PCM to float32 because it guarantees output stays within [-1.0, 1.0]. Dividing by 32767 would map the most negative sample to -1.0000305, which is outside the range that audio processing libraries expect."

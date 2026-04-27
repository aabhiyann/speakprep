# LEARNINGS.md — Concepts in My Own Words

Format: ### Concept — Date / Explanation

---

### Circuit breaker pattern — what it is and why it exists — 2026-04-27

**The confusion before:**
I heard "circuit breaker" and thought it was something complex. It's actually a simple state machine that solves one specific problem: when a dependency (an API, a database) is failing, stop wasting time and resources trying to call it over and over.

**The mental model that works:**
Think of an electrical circuit breaker in your house. When too much current flows, the breaker trips — it opens the circuit and stops all electricity. You reset it after the problem is fixed. Software circuit breakers work identically:

```
CLOSED (normal) → 3rd consecutive failure → OPEN (blocking all requests)
OPEN → 60 seconds pass → HALF_OPEN (allow one test request)
HALF_OPEN → success → CLOSED
HALF_OPEN → failure → OPEN (reset timer)
```

In CLOSED state, track consecutive failures. When failures hit the threshold, OPEN the circuit — every subsequent request is rejected immediately (microseconds, not after a 5-second API timeout). After the recovery timeout, go HALF_OPEN: let one request through as a test. The injectable clock `_clock=time.time` means tests can fast-forward time without sleeping.

**Why it matters:**
Without a circuit breaker, if Groq is down: every request waits 5-30 seconds for the Groq timeout before trying Cerebras. With 100 concurrent users, that's thousands of seconds wasted per minute. With a circuit breaker: after 3 failures, Groq is skipped instantly.

**One deep read:** Search "martinfowler.com circuit breaker" — Martin Fowler's original article.

---

### Async generators — yield inside async def — 2026-04-27

**The confusion before:**
I knew `yield` makes a generator. I knew `async def` makes a coroutine. What happens when you combine them?

**The mental model that works:**
A regular generator produces values one at a time. An async generator does the same, but can `await` between yields:

```python
async def stream_tokens(api_response):
    async for chunk in api_response:
        yield chunk.text  # caller gets this token immediately

async for token in stream_tokens(response):  # async for — note the async
    send_to_client(token)
```

The type is `AsyncGenerator[str, None]`. It satisfies `AsyncIterator[str]`. Each `yield` delivers a token to the caller the moment it arrives from the API — the user sees text appearing word by word rather than waiting for the full response.

In tests, you can collect all yielded values: `chunks = [c async for c in service.stream(messages)]`.

The fallback path in `stream()` calls `await self.generate()` and then `yield response.content` — yields the full response as one chunk. The caller doesn't know or care whether it came from streaming or not.

**One deep read:** PEP 525 — Asynchronous Generators (python.org/dev/peps/pep-0525)

---

### AsyncMock vs MagicMock — testing async functions — 2026-04-27

**The confusion before:**
Used `MagicMock` for everything. Tests crashed with "object MagicMock is not awaitable."

**The mental model that works:**
`MagicMock()` fakes a synchronous callable — calling it returns a value immediately.
`AsyncMock()` fakes an `async def` function — calling it returns a coroutine, which when awaited returns the configured value.

```python
# Wrong — MagicMock is not awaitable
mock.create = MagicMock(return_value=response)
result = await mock.create(...)  # TypeError: object MagicMock is not awaitable

# Correct — AsyncMock returns a coroutine
mock.create = AsyncMock(return_value=response)
result = await mock.create(...)  # works
```

Rule: **any method your code calls with `await` must be faked with `AsyncMock`.** Everything else uses `MagicMock`.

For raising exceptions from async mocks: `AsyncMock(side_effect=RateLimitError(...))` — when awaited, raises the exception instead of returning a value.

**One deep read:** Python docs — `unittest.mock.AsyncMock`

---

### Structured logging with structlog — 2026-04-27

**The confusion before:**
`print()` or `logging.info("Groq took 234ms")` — what's wrong with that?

**The mental model that works:**
String logs are for humans at a terminal. Structured logs are for machines querying a log system.

```python
# String log — un-queryable
logger.info("Groq call succeeded in 234ms using 50 tokens")

# Structured log — key-value pairs
logger.info("llm.call.success", provider="groq", latency_ms=234, tokens_used=50)
```

In a log aggregation system (Grafana, Datadog), you can filter: `latency_ms > 500`. With string logs, that requires regex. With structured logs, it's a simple field query. You can build dashboards: "average latency by provider over time" — trivial with structured, painful with strings.

Usage pattern in this project:
```python
import structlog
logger = structlog.get_logger(__name__)
logger.info("llm.call.success", provider=provider.name, latency_ms=latency_ms)
logger.warning("llm.provider.failure", provider=provider.name, error=str(exc))
```

**One deep read:** structlog.readthedocs.io — Getting Started guide

---

### Squash merge vs create a merge commit — git strategy — 2026-04-27

**The confusion before:**
I'd been using "Squash and merge" on GitHub for every PR. Then I noticed `git log develop` showed one commit per PR, not 19. My function-level commits were gone.

**The mental model that works:**

**Squash merge:** collapses all N commits in a feature branch into one new commit on the base branch. Clean history, but you lose granularity.

**Create a merge commit:** all N commits appear on the base branch, connected by a merge commit. You can see the full granular history with `git log`.

```
Squash:  develop: A → B → "feat(llm): LLM service"  (19 commits hidden inside)
Merge:   develop: A → B → M
                          |\
                          | feat(llm): add stream()
                          | feat(llm): add generate()
                          | ... 17 more commits
```

**Decision for this project:**
- feature → develop: "Create a merge commit" — all function-level commits visible in `git log develop`
- develop → main: "Squash and merge" — one clean release commit per phase

The function-level commits ARE the learning journal. Squashing them into develop defeats their purpose.

---

### Whisper's architecture — encoder-decoder, mel spectrogram, why 30s limit — 2026-04-26

**The confusion before:**
I knew Whisper converted audio to text but I had no idea what was happening inside. I thought it was just "audio in, text out" like a black box.

**The mental model that works:**
Whisper has three stages:

1. **Preprocessing**: raw 16kHz audio → mel spectrogram. A mel spectrogram is a 2D image: time on the x-axis, frequency on the y-axis, brightness = loudness. The "mel" scale compresses high frequencies (humans can't distinguish 8000 Hz from 8100 Hz well) and expands low frequencies (100 Hz vs 200 Hz is clearly different). Log scale compresses amplitude. Whisper always pads or truncates to exactly 30 seconds.

2. **Encoder**: the mel spectrogram (effectively a 2D image) goes through two Conv1D layers for local feature extraction, then through transformer blocks. Each block has self-attention (every position attends to every other position) and a feed-forward layer. Output: a rich numerical representation of "what acoustic patterns are present."

3. **Decoder**: generates text tokens one at a time. At each step: look at previously generated tokens + cross-attend to the encoder output + pick the most likely next token. Repeat until `<|endoftext|>`. This is why Whisper can't start outputting until it "understands" the full audio context.

The 30-second limit: the model was trained on 30-second windows. The positional encodings only go up to 30s. Longer audio must be chunked and merged, introducing errors at boundaries.

**Why it matters for SpeakPrep specifically:**
Interview answers are typically 30-90 seconds. For the offline fallback, we need to be aware that long answers require chunking. Deepgram (Phase 2, primary ASR) doesn't have this limitation — it uses CTC which processes frames as they arrive, not fixed windows.

**The code that made it real:**
```python
# faster-whisper handles the mel spectrogram internally
# We just need to pass float32 audio normalised to [-1.0, 1.0]
audio_f32 = pcm_to_float32(audio)  # int16 → float32
segments_iter, info = self._model.transcribe(audio_f32, language="en")
```

**What to read if you want to go deeper:**
[Whisper paper — arxiv.org/abs/2212.04356](https://arxiv.org/abs/2212.04356) — "Robust Speech Recognition via Large-Scale Weak Supervision"

**Interview answer version:**
"Whisper converts audio to a log-mel spectrogram then runs an encoder-decoder transformer. The encoder reads the full 30-second audio context, the decoder generates text tokens autoregressively using cross-attention to the encoder. It's fundamentally different from streaming ASR — it needs the complete audio before outputting anything."

---

### Hallucination detection — no_speech_prob and compression_ratio — 2026-04-26

**The confusion before:**
I didn't know Whisper could hallucinate. I assumed if you gave it audio it would give you an accurate transcript.

**The mental model that works:**
Whisper hallucinates on silence and noise — it generates plausible-sounding text even when there's nothing to transcribe. This affects ~40% of non-speech segments. It's not a bug, it's a consequence of how it was trained: the model learned to always produce text given a 30-second window, because the training data was audio that always had speech.

Two detection signals Whisper exposes:

**`no_speech_prob`**: probability the model assigns to the audio being non-speech. Ranges 0.0–1.0. Above 0.6 = likely silence or noise, return None.

**`compression_ratio`**: hallucinations tend to be repetitive ("Thank you for watching. Please like and subscribe."). Repetitive text compresses well. The ratio is length(original) / length(compressed). High ratio = very repetitive = suspect. Above 2.4 = likely hallucination, return None.

These are the same two filters used in OpenAI's original Whisper code. faster-whisper computes `compression_ratio` using a token-based approach (comparing output tokens to what's statistically expected for the audio length).

**Why it matters for SpeakPrep specifically:**
Without these filters, a user who pauses or has background noise would generate a hallucinated transcript that the LLM would respond to. The LLM can't tell the difference — it would give interview coaching feedback on nonsense text.

**The code that made it real:**
```python
max_no_speech_prob = max(s.no_speech_prob for s in segments)
max_compression_ratio = max(s.compression_ratio for s in segments)

if max_no_speech_prob > 0.6:
    return None  # silence or noise
if max_compression_ratio > 2.4:
    return None  # likely hallucination
```

**What to read if you want to go deeper:**
[faster-whisper source — transcribe.py](https://github.com/SYSTRAN/faster-whisper/blob/master/faster_whisper/transcribe.py) — `no_speech_prob` and `compression_ratio` calculation in context

**Interview answer version:**
"Whisper hallucinates on silence — it generates text even when there's no speech. I filter results using two built-in signals: `no_speech_prob > 0.6` (the model itself says this is probably not speech) and `compression_ratio > 2.4` (the output is highly repetitive, a hallucination signature). Both are computed per-segment; I use the worst case across all segments."

---

### Python generators — one-time iterables, why you must materialise them — 2026-04-26

**The confusion before:**
I knew generators existed but I thought of them as just "lazy lists." I didn't fully understand that they're stateful and can only be traversed once.

**The mental model that works:**
A generator is a function that yields values one at a time instead of computing them all upfront. When you call a generator function, you get a generator object — a cursor sitting at the start of the sequence. Each `next()` call advances the cursor and returns the next value. When the cursor reaches the end, it's done. There is no "go back to the start."

```python
def count_to_three():
    yield 1
    yield 2
    yield 3

gen = count_to_three()
list(gen)   # [1, 2, 3]
list(gen)   # [] — already exhausted
```

faster-whisper uses this because Whisper generates transcript segments as it processes the audio. Materialising all segments would require keeping them all in memory; the generator lets you process each segment as it's decoded.

But we need multiple passes: one for `max(no_speech_prob)`, one for `max(compression_ratio)`, one for joining text. So we call `list(segments_iter)` once, store in a list, iterate as many times as needed.

**Why it matters for SpeakPrep specifically:**
This same pattern will appear with Groq's streaming API (Task 1.3) and Deepgram's streaming API (Phase 2). Streaming responses are generators/async generators. Understanding that they're single-pass is essential for correct code.

**The code that made it real:**
```python
segments_iter, info = self._model.transcribe(audio_f32, ...)
segments = list(segments_iter)  # materialise — exhaust once, store, iterate freely
max_no_speech_prob = max(s.no_speech_prob for s in segments)   # pass 1
max_compression_ratio = max(s.compression_ratio for s in segments)  # pass 2
text = " ".join(s.text.strip() for s in segments)  # pass 3
```

**What to read if you want to go deeper:**
[Python docs — generators](https://docs.python.org/3/howto/functional.html#generators) — Python Functional Programming HOWTO, generators section

**Interview answer version:**
"Python generators are stateful one-time iterables — once exhausted they return nothing. faster-whisper returns a generator of transcript segments. I materialise it with list() immediately because I need three passes: two for hallucination filtering and one for joining the text."

---

### Pydantic BaseModel — type-safe data classes with validation — 2026-04-26

**The confusion before:**
I knew Python had `dataclass` and `TypedDict`. I didn't understand why you'd use Pydantic instead.

**The mental model that works:**
A `dataclass` is just a class with auto-generated `__init__`. No validation — if you pass a string where a float is expected, it silently stores the string. `TypedDict` is only checked by the type checker (mypy), not at runtime.

Pydantic `BaseModel` validates types at construction time:
```python
result = TranscriptionResult(text="hello", no_speech_prob="not-a-float", ...)
# Raises ValidationError: no_speech_prob must be float
```

It also gives you `.model_dump()` (Python dict), `.model_json()` (JSON string), and direct integration with FastAPI — when a Pydantic model is returned from a FastAPI route, it's automatically serialized to JSON.

**Why it matters for SpeakPrep specifically:**
`TranscriptionResult` will eventually go over the WebSocket as JSON. In the real handler, we'll return it from an endpoint or serialize it directly. Pydantic handles that automatically. Also: if faster-whisper returns an unexpected type for `no_speech_prob` (a bug in a new version), Pydantic catches it at the boundary rather than letting it silently propagate to the LLM.

**The code that made it real:**
```python
class TranscriptionResult(BaseModel):
    text: str
    no_speech_prob: float   # validated at construction
    language: str
    duration_seconds: float
    latency_ms: int

result = TranscriptionResult(text=text, no_speech_prob=0.04, ...)
result.model_dump()  # {'text': ..., 'no_speech_prob': 0.04, ...}
```

**What to read if you want to go deeper:**
[Pydantic v2 docs — models](https://docs.pydantic.dev/latest/concepts/models/)

**Interview answer version:**
"I use Pydantic BaseModel for structured return types because it validates field types at construction (not just statically), gives free JSON serialization, and integrates directly with FastAPI's response handling. A TypedDict would only be checked by mypy — Pydantic catches type mismatches at runtime at the data boundary."

---

### VAD state machine — triggered flag + silence counter — 2026-04-26

**The confusion before:**
I thought VAD was a function you call and it tells you "there was speech from 1.2s to 3.4s." I didn't understand how you detect speech in real time, frame by frame, without knowing the future.

**The mental model that works:**
You maintain two pieces of state: a `triggered` flag and a `silence_count` counter. Initially untriggered. Each 20ms frame you ask the VAD classifier one question: speech or silence?

- Not triggered + speech → flip to triggered, start recording
- Triggered + speech → keep recording, reset silence counter
- Triggered + silence → increment silence counter; if counter ≥ threshold → utterance over, stop

That's it. No lookahead. You never know if the next frame will be speech or silence — you just react to what arrives. The silence threshold (400ms = 20 consecutive silence frames) is the only tunable parameter that affects responsiveness vs. clipping risk.

**Why it matters for SpeakPrep specifically:**
This exact state machine is in `VADRecorder.record_until_silence()` and `collect_from_file()`. When Phase 2 adds streaming Deepgram, the same pattern applies — we'll watch Deepgram's `is_final` field instead of a silence counter, but the triggered/not-triggered logic is identical.

**The code that made it real:**
```python
if not triggered:
    if is_speech:
        triggered = True          # speech has started
else:
    silence_count += 1 if not is_speech else 0
    if not is_speech and silence_count >= self._silence_frames_needed:
        break                     # utterance over
```

**What to read if you want to go deeper:**
[WebRTC VAD README — webrtcvad Python bindings](https://github.com/wiseman/py-webrtcvad)

**Interview answer version:**
"VAD for real-time speech detection is a two-state machine: wait for speech to start, then wait for sustained silence to end the utterance. The silence threshold — typically 400ms — is the tradeoff between cutting off trailing words and adding latency to every turn."

---

### asyncio.to_thread — running blocking code without freezing the server — 2026-04-26

**The confusion before:**
I knew that `time.sleep()` inside async code was bad. But I didn't know what to do when I have a legitimate CPU-intensive operation (like ML inference) that genuinely takes 2-3 seconds and can't be made async.

**The mental model that works:**
`asyncio.to_thread(fn, *args)` runs `fn` in Python's default thread pool executor and suspends your coroutine until it finishes. From the event loop's perspective: your coroutine yields control (just like any `await`), other tasks run, and when the thread is done the coroutine resumes with the result.

The thread pool has real OS threads, so CPU-bound work actually runs in parallel with the event loop. The GIL is released during the thread's computation — Python releases the GIL during C extension calls, and faster-whisper is a C extension.

Without `to_thread`: faster-whisper holds the GIL for 2-3 seconds. Every other coroutine is frozen. One transcription request freezes the entire server — no other client can receive a ping, send audio, or do anything.

With `to_thread`: inference runs in a thread, event loop keeps serving other requests, result arrives when ready.

**Why it matters for SpeakPrep specifically:**
`LocalASR.transcribe()` will use `await asyncio.to_thread(self._transcribe_sync, audio)`. This is Task 1.2. Without it, a 2-second Whisper inference would freeze every active WebSocket connection during that time — unacceptable for a real-time voice app.

**The code that made it real:**
```python
# CPU-bound work runs in thread, event loop stays free
result = await asyncio.to_thread(self._transcribe_sync, audio)
```

**What to read if you want to go deeper:**
[Python docs — asyncio.to_thread](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread)

**Interview answer version:**
"asyncio.to_thread offloads CPU-bound work to a thread pool and awaits the result, keeping the event loop free to serve other requests. For ML inference like Whisper, this is essential — without it, a single transcription request would block every active WebSocket connection for the duration of inference."

---

### HTTP vs WebSockets — 2026-04-26

**The confusion before:**
I knew WebSockets were "for real-time" but I didn't understand the actual mechanism. I thought maybe they were just very fast HTTP requests.

**The mental model that works:**
HTTP is like sending a letter. You send a request, the server sends a response, the connection closes. Every piece of data requires a new letter. WebSockets are like a phone call — you dial once, and both sides can talk at any time until one of you hangs up. The connection stays open permanently.

The technical version: HTTP is request-response and stateless. WebSockets start as an HTTP request with an `Upgrade: websocket` header. The server responds with `101 Switching Protocols`, and from that point on the same TCP connection becomes a full-duplex channel — both sides can send at any time.

**Why it matters for SpeakPrep specifically:**
Voice audio is continuous — you can't send an HTTP request for each 20ms audio frame (that's 50 requests/second). WebSockets let the browser stream audio in real time and receive the AI's spoken response back, all on one persistent connection.

**The code that made it real:**
```python
await websocket.accept()   # completes the HTTP→WebSocket upgrade handshake
message = await websocket.receive()  # blocks until a message arrives
await websocket.send_text("Echo: hello")  # push to client anytime
```

**What to read if you want to go deeper:**
[MDN WebSocket API — Writing WebSocket Servers](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers)

**Interview answer version:**
"WebSockets upgrade an HTTP connection to a persistent full-duplex channel where both client and server can send messages at any time. Unlike HTTP's request-response model, no new connection is required for each message — essential for streaming audio where you have 50 frames per second."

---

### Python asyncio — event loop, coroutines, tasks — 2026-04-26

**The confusion before:**
I thought `async/await` meant my code ran in parallel across multiple threads. I was confused about why you couldn't just use `time.sleep()` inside an async function.

**The mental model that works:**
asyncio is a single-threaded task scheduler. There is one thread, one event loop, and many tasks. Each task runs until it hits an `await` — at that point it voluntarily pauses and says "I'm waiting for something, let someone else run." The event loop picks the next ready task and runs it until its next `await`. This is cooperative multitasking, not parallelism.

`time.sleep(3)` blocks the entire thread for 3 seconds — no other task can run during that time. `await asyncio.sleep(3)` pauses only the current task for 3 seconds — all other tasks keep running normally. That's the critical difference.

`async def` defines a coroutine function. Calling it returns a coroutine object — the computation hasn't started yet. `await` starts it and pauses your code until it finishes. `asyncio.create_task()` schedules it to run concurrently without your code waiting for it.

**Why it matters for SpeakPrep specifically:**
The voice handler needs to do several things at once: receive audio from the browser, send it to Deepgram, wait for the transcript, send it to Groq, wait for the LLM response, convert it to speech, send it back. asyncio lets all of this happen on one thread without blocking — while waiting for Deepgram, we can be processing the next audio chunk.

**The code that made it real:**
```python
heartbeat_task = asyncio.create_task(_heartbeat())  # starts concurrently, doesn't block
message = await websocket.receive()  # pauses here, heartbeat keeps running
```

**What to read if you want to go deeper:**
[Python asyncio docs — Coroutines and Tasks](https://docs.python.org/3/library/asyncio-task.html)

**Interview answer version:**
"asyncio is a single-threaded cooperative scheduler. Coroutines yield control at every `await` point, letting the event loop run other tasks. Unlike threading, there's no parallelism — but for I/O-bound work like network requests, you spend most time waiting anyway, so concurrency without parallelism is enough."

---

### asyncio.gather — concurrent execution — 2026-04-25

**The confusion before:**
I knew `gather` ran things "at the same time" but I didn't understand how to use it or what order results came back in.

**The mental model that works:**
`asyncio.gather(task1, task2, task3)` starts all three coroutines and runs them concurrently. It waits until ALL of them finish, then returns a list of results in the same order as the input — regardless of which one finished first.

Without gather, if each task takes 1 second, running them sequentially takes 3 seconds. With gather, all three run concurrently and the total time is ~1 second (the slowest one).

**Why it matters for SpeakPrep specifically:**
When the voice handler needs both the LLM response and a database lookup at the same time, `gather` lets both happen concurrently instead of sequentially. In a latency-sensitive voice app, this difference is noticeable to the user.

**The code that made it real:**
```python
results = await asyncio.gather(fetch_transcript(), fetch_user_history(), check_session())
# all three run at the same time, results[0] is transcript, results[1] is history, etc.
```

**What to read if you want to go deeper:**
[asyncio.gather documentation](https://docs.python.org/3/library/asyncio-task.html#asyncio.gather)

**Interview answer version:**
"asyncio.gather starts multiple coroutines and runs them concurrently, returning results in input order when all complete. For I/O-bound operations like API calls, this turns N sequential waits into one concurrent wait — reducing latency from sum(times) to max(times)."

---

### Exponential backoff with jitter — 2026-04-25

**The confusion before:**
I knew "retry with backoff" existed but I didn't know why both exponential AND jitter were necessary, or what problem each solved.

**The mental model that works:**
When an API fails, retrying immediately often fails again — the server is overloaded. Exponential backoff gives it time to recover by doubling the wait time each retry: 1s, 2s, 4s, 8s.

But if 1000 clients all fail at the same moment and all wait exactly 1 second, they all retry at the exact same moment — causing another spike. Jitter adds randomness (multiply by a random number between 0.75 and 1.25) so retries are spread across a time window instead of synchronized. A synchronized retry storm is called a "thundering herd."

**Why it matters for SpeakPrep specifically:**
Deepgram and Groq are external APIs that will occasionally return 429 (rate limit) or 500 (server error). Without retry logic, one bad API response crashes the interview session. With retry + backoff + jitter, transient failures are handled transparently.

**The code that made it real:**
```python
base_delay_secs = float(2**attempt)          # 1, 2, 4, 8...
delay_secs = base_delay_secs * random.uniform(0.75, 1.25)  # jitter
await asyncio.sleep(delay_secs)
```

**What to read if you want to go deeper:**
[AWS Architecture Blog — Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

**Interview answer version:**
"Exponential backoff gives a failing service time to recover between retries. Jitter adds randomness to the delay so multiple clients retrying simultaneously don't all hit the server at the same instant — preventing the 'thundering herd' problem where retries cause the next failure."

---

### FastAPI — what it is and how routes work — 2026-04-26

**The confusion before:**
I'd heard FastAPI was "fast" but I didn't understand what a web framework actually was at the level of "what problem does it solve."

**The mental model that works:**
A web framework solves the problem of "how do I turn incoming HTTP/WebSocket requests into function calls?" Without a framework, you'd manually parse HTTP bytes, extract headers, decode query strings, validate types, and format responses. FastAPI does all of that. You write a Python function, decorate it with `@app.get("/path")`, and FastAPI connects the dots — incoming requests on that path call your function, the return value becomes the response.

Starlette is the low-level engine FastAPI is built on — it handles the actual protocol (reading bytes, managing connections). FastAPI adds automatic type validation, automatic API docs generation, and convenience decorators on top.

**Why it matters for SpeakPrep specifically:**
The entire backend is FastAPI. Understanding the router pattern (each file has its own `APIRouter`, main.py imports and includes them) means I can add new endpoints in new files without touching main.py.

**The code that made it real:**
```python
router = APIRouter()

@router.websocket("/ws/echo/{client_id}")  # decorator registers the handler
async def ws_echo(websocket: WebSocket, client_id: str): ...

# in main.py:
app.include_router(ws_echo_router)  # plugs the router into the app
```

**What to read if you want to go deeper:**
[FastAPI official tutorial — intro](https://fastapi.tiangolo.com/tutorial/)

**Interview answer version:**
"FastAPI maps HTTP/WebSocket requests to Python functions via decorators. It's built on Starlette for the protocol layer and adds automatic request validation from type hints and auto-generated OpenAPI docs. I used its APIRouter pattern to organize routes by feature domain rather than putting everything in main.py."

---

### CORS (Cross-Origin Resource Sharing) — 2026-04-26

**The confusion before:**
I'd seen CORS errors in browser consoles before but I thought it was a server setting I needed to "turn off." I didn't understand what it was protecting against.

**The mental model that works:**
A browser security rule: JavaScript on page A cannot make requests to server B without B's explicit permission. "Origin" = protocol + domain + port. `http://localhost:5173` and `http://localhost:8000` are different origins even on the same machine.

Without this rule, a malicious website could silently make requests to your bank (`https://bank.com/transfer`) using your already-logged-in session cookies. The bank's server would see authenticated requests and process them. CORS prevents this by requiring the server to explicitly say which origins are allowed.

The server includes `Access-Control-Allow-Origin: http://localhost:5173` in responses. The browser sees this and allows the JavaScript request to proceed. The browser enforces this — the server doesn't block requests, it just sets the header. Non-browser clients (curl, Postman, server-to-server) ignore CORS entirely.

**Why it matters for SpeakPrep specifically:**
The frontend (Vite dev server at port 5173) makes WebSocket connections to the backend (port 8000). Without the CORS middleware, the browser blocks every single connection attempt.

**The code that made it real:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # only this origin is allowed
    allow_credentials=True,
)
```

**What to read if you want to go deeper:**
[MDN CORS guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)

**Interview answer version:**
"CORS is a browser security policy that prevents cross-origin JavaScript requests unless the server explicitly allows them via `Access-Control-Allow-Origin` headers. It defends against cross-site request forgery — malicious pages making authenticated requests to other sites. FastAPI's CORSMiddleware adds these headers automatically for configured origins."

---

### PCM audio format — int16, sample rate, frames — 2026-04-26

**The confusion before:**
I knew audio was "bytes" but I had no idea what structure those bytes had or why 16kHz mattered.

**The mental model that works:**
Sound is pressure waves in air. A microphone converts pressure into voltage. An ADC (analog-to-digital converter) samples that voltage at regular intervals and stores each sample as a number.

Sample rate (16000 Hz) = 16,000 measurements per second. Human speech is fully captured at 8kHz, so 16kHz is more than adequate.

Bit depth (int16 = 16-bit signed integer) = each measurement is stored as a number from -32768 to +32767. 0 = silence. Large positive or negative = loud.

Storage: 1 second at 16kHz int16 = 16,000 samples × 2 bytes = 32,000 bytes ≈ 31 KB/sec.

20ms frame = 16,000 × 0.02 = 320 samples = 640 bytes. This is the unit WebRTC VAD requires.

**Why it matters for SpeakPrep specifically:**
The microphone produces int16 PCM. WebRTC VAD requires int16 PCM in 20ms frames. Deepgram accepts int16 PCM. Faster-Whisper expects float32 normalized to [-1.0, 1.0]. Knowing the format at each step tells you which conversion functions to call.

**The code that made it real:**
```python
frame_size_samples = int(sample_rate * 0.02)  # 16000 * 0.02 = 320 samples per 20ms
size_bytes = int(audio_int16.nbytes)            # 1600 samples * 2 bytes = 3200 bytes
```

**What to read if you want to go deeper:**
[Wikipedia — Pulse-code modulation](https://en.wikipedia.org/wiki/Pulse-code_modulation)

**Interview answer version:**
"PCM audio is a sequence of integer samples representing sound pressure at regular time intervals. At 16kHz int16, you have 16,000 two-byte samples per second. Voice AI systems require specific formats — VAD needs int16 in 20ms frames, local transcription models need float32 normalized to [-1.0, 1.0]."

---

### RMS amplitude for silence detection — 2026-04-26

**The confusion before:**
I assumed you detect silence by checking if samples are close to zero. I didn't know why that was insufficient.

**The mental model that works:**
Peak amplitude (checking the max sample) can be fooled by a single loud click — one spike of 32767 in a mostly-silent recording would report as loud. You need the average energy.

RMS (Root Mean Square): square every sample, compute the mean of the squares, take the square root. This gives the "typical" amplitude across the whole window. Squaring makes all values positive (so negative samples don't cancel out positive ones) and emphasizes loud samples more than quiet ones.

Silence ≈ RMS < 500. Quiet speech ≈ 500-2000. Normal speech ≈ 2000-8000.

**Why it matters for SpeakPrep specifically:**
The VAD recorder needs to decide when the user has stopped talking. Checking RMS < 500 for N consecutive frames = silence detected = end of utterance. This is more reliable than checking peak amplitude.

**The code that made it real:**
```python
rms_amplitude = float(np.sqrt(np.mean(np.square(int32_audio), dtype=np.float64)))
is_likely_silence = bool(rms_amplitude < 500.0)
```

**What to read if you want to go deeper:**
[Wikipedia — Root mean square (signal processing)](https://en.wikipedia.org/wiki/Root_mean_square#In_electronics)

**Interview answer version:**
"RMS amplitude squares every sample, averages them, and takes the square root — giving average signal energy rather than peak value. For silence detection in voice apps, RMS is more reliable than peak amplitude because a single loud click won't falsely register as speech."

---

### Starlette 1.x WebSocket disconnect behavior — 2026-04-26

**The confusion before:**
I expected `websocket.receive()` to raise `WebSocketDisconnect` when the client disconnected, same as pre-1.0 Starlette and most FastAPI tutorials show.

**The mental model that works:**
In Starlette 0.x (and most tutorials), `receive()` raises `WebSocketDisconnect` when the client disconnects. You catch it and clean up.

In Starlette 1.x, `receive()` instead returns the disconnect message as a normal dict: `{"type": "websocket.disconnect", "code": 1000}`. The exception is NOT raised. The state machine transitions to DISCONNECTED. If you then call `receive()` again (because you missed the disconnect check), it raises `RuntimeError: Cannot call "receive" once a disconnect message has been received.`

This is a breaking change that isn't prominently documented. It means every FastAPI tutorial showing `except WebSocketDisconnect` as the main disconnect handler will subtly break on Starlette 1.x under certain conditions.

**Why it matters for SpeakPrep specifically:**
Every WebSocket handler needs to detect when clients disconnect. Getting this wrong means the handler loop continues after the client is gone, hits RuntimeError, and crashes. The fix is one explicit check, but you have to know it's needed.

**The code that made it real:**
```python
message = await websocket.receive()
if message["type"] == "websocket.disconnect":  # critical check for Starlette 1.x
    break
# without this check: RuntimeError on the next receive() call
```

**What to read if you want to go deeper:**
[ASGI WebSocket spec](https://asgi.readthedocs.io/en/latest/specs/www.html#websocket) — the underlying contract Starlette implements

**Interview answer version:**
"Starlette 1.x changed WebSocket disconnect handling — `receive()` now returns a disconnect message dict instead of raising WebSocketDisconnect. Without explicitly checking `message['type'] == 'websocket.disconnect'`, the handler continues looping and crashes with RuntimeError on the next receive call."

---

### TypeVar and generics in Python — 2026-04-25

**The confusion before:**
I'd seen `TypeVar` in code but I didn't know why you'd use it instead of just using `Any`.

**The mental model that works:**
`Any` tells the type checker "I don't care what type this is." That means it stops checking — you lose all the safety.

`TypeVar("T")` says "I don't know what type this will be, but whatever it is, these things must be the same type." It's a placeholder that the type checker fills in at each call site.

```python
T = TypeVar("T")
async def timeout_with_fallback(coro: Coroutine[..., T], fallback: T) -> T:
```

This tells the type checker: "The return type matches the type of `coro`'s result, and `fallback` must be the same type." If `coro` returns a `str`, then `fallback` must be a `str` and the return is a `str`. If you pass a `str` fallback to an `int`-returning coroutine, the type checker catches it.

**Why it matters for SpeakPrep specifically:**
The async utility functions work with any type — `timeout_with_fallback` might wrap a `str`-returning TTS call or a `dict`-returning database call. TypeVar lets the type checker verify that the fallback type matches in each specific use case.

**The code that made it real:**
```python
T = TypeVar("T")
async def timeout_with_fallback(coro: Coroutine[Any, Any, T], timeout_secs: float, fallback: T) -> T:
```

**What to read if you want to go deeper:**
[Python docs — TypeVar](https://docs.python.org/3/library/typing.html#typing.TypeVar)

**Interview answer version:**
"TypeVar creates a generic type placeholder that the type checker fills in at each call site. Unlike Any, which turns off type checking, TypeVar enforces consistency — if a function returns T, the caller knows the return type matches whatever the input type was."

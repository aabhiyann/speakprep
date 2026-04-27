# LEARNINGS.md — Concepts in My Own Words

Format: ### Concept — Date / Explanation

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

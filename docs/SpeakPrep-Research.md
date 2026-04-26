# SpeakPrep: Complete Technical Research Blueprint

**SpeakPrep enters a $1.7B AI interview coaching market that is growing at 30.6% CAGR, yet no existing product combines real-time voice AI with adaptive coaching across the full interview preparation lifecycle.** This research covers every technical and product dimension needed to build a best-in-class real-time voice AI mock interview coach — from byte-level audio streaming to LLM provider selection to adaptive difficulty algorithms. The findings inform four detailed technical documents: a PRD, system design doc, architecture spec, and learning curriculum.

---

## SECTION 1: Product and market landscape

### The $1.7B market has clear gaps no competitor fills

The AI recruitment market reached **$596–706M in 2025** with a 6.8–7.5% CAGR toward $920M–$1.1B by 2030. The candidate-facing AI interview assistant segment hit **$1.7B in 2025**, growing at **30.6% CAGR**. 58% of job applicants now use AI tools during their search, and 93% report interview anxiety.

**Competitive landscape in detail:**

| Competitor | Pricing | Core Differentiator | Key Weakness |
|---|---|---|---|
| **Final Round AI** | $96–$148/mo | Real-time CoPilot during live interviews, AI mock with video analysis | Buggy, expensive, generic responses, poor support |
| **Google Interview Warmup** | Free | Privacy-first, 5 questions per session, no scoring | No follow-ups, no conversation, no personalization |
| **Yoodli** | $10–$20/mo | Speech coaching (pacing, fillers, eye contact) | Better for delivery than content; not interview-specific |
| **Hume AI** | API pricing | Empathic Voice Interface detecting emotional cues, <300ms latency | Infrastructure API, not a consumer product |
| **Interviewing.io** | $225+/session | Live mock with FAANG engineers | Expensive ($1K+ for 5 sessions), not beginner-friendly |
| **Pramp/Exponent** | Free–$79/mo | Peer-to-peer mock interviews | Inconsistent peer quality, 30% bad experiences |
| **Big Interview** | $39–$299 | 170+ video lessons, 1000+ questions, university partnerships | AI feedback can be generic vs. human coaching |
| **Huru** | $8.25/mo | Mobile-first, HireVue simulation | Limited depth |

**Critical unsolved pain points** identified from Reddit, G2, Trustpilot, and app reviews:

No current tool provides **realistic conversational pressure** — users can "game" the AI. Follow-up question logic is poor; most tools ask predefined questions without intelligent probing. There is **no end-to-end journey coverage** — users cobble together 4–5 tools (LeetCode for coding, ChatGPT for stories, Big Interview for practice, Interviewing.io for calibration). No tool addresses **interview anxiety and confidence building** progressively, despite 93% of seekers reporting anxiety. Tools deliver **generic, one-size-fits-all feedback** that ignores company culture, role level, and interviewer style. The **price-to-value mismatch** is severe — $148/month for only 4 sessions feels exploitative to unemployed job seekers.

### The job seeker's interview preparation workflow spans 4–12 weeks

**Stage 1 — Resume and application (1–2 weeks, 5–15 hours):** Resume optimization, ATS keyword matching, cover letter writing. Tools: Teal, Jobscan, ChatGPT.

**Stage 2 — Recruiter/phone screen (15–30 min per call, 1–2 hours prep):** Behavioral questions, salary expectations, "tell me about yourself." Tools: Google Warmup, Glassdoor.

**Stage 3 — Technical phone screen (45–60 min, 40–200+ hours prep):** Coding problems, data structures, algorithms. Tools: LeetCode ($35/mo), HackerRank, NeetCode.

**Stage 4 — Behavioral interview (45–60 min, 10–20 hours prep):** STAR stories, leadership principles. Tools: Big Interview, ChatGPT.

**Stage 5 — System design (45–60 min, 20–60 hours prep):** Distributed systems, API design. Tools: HelloInterview, Alex Xu's books.

**Stage 6 — On-site loop (3–6 hours, all accumulated prep):** Combined rounds. Final calibration: Interviewing.io at $225+/session.

**Total preparation: 50–300+ hours over 4–12 weeks.** SpeakPrep's opportunity is covering stages 2–5 in a single product with voice-first practice.

### Realistic KPIs for a career-focused SaaS product

| Metric | Conservative | Good | Best-in-Class |
|---|---|---|---|
| DAU/MAU | 8% | 12% | 18%+ |
| D1 Retention | 12% | 18% | 25% |
| D7 Retention | 5% | 10% | 15% |
| D30 Retention | 2% | 4% | 7% |
| Session Length | 10 min | 18 min | 25+ min |
| Freemium→Paid | 2% | 4% | 7%+ |
| Monthly Churn (monthly plans) | 12% | 8% | 5% |

EdTech freemium-to-paid conversion averages only **2.6%** — the lowest across SaaS. Career tools may slightly outperform due to higher urgency. EdTech monthly churn hit **9.6%** in 2025 — highest in B2B SaaS. Career tools have unique "positive churn" where users cancel after landing jobs.

---

## SECTION 2: Deep technical architecture

### Real-time audio streaming at the byte level

**Sample rate selection:** 16 kHz is the universal ASR standard because human speech intelligibility lies in 100 Hz–8 kHz, and 16 kHz captures frequencies up to 8 kHz per Nyquist. Higher rates add zero recognition accuracy — experiments confirm 48 kHz and 16 kHz yield identical ASR results. At **16 kHz, 16-bit, mono**, the data rate is exactly **32 KB/s** (256 kbps).

**PCM format:** Each sample is a signed 16-bit integer (range −32,768 to +32,767) in little-endian byte order. A 20ms audio frame at 16 kHz contains 320 samples = **640 bytes**. This is the optimal chunk size — it balances latency (20ms buffering delay) against per-frame overhead (50 frames/sec is manageable). Smaller 10ms frames double overhead; larger 30ms frames add perceptible latency.

**Byte calculations for the full pipeline:**
- Per 20ms frame: **640 bytes**
- Per second: **32,000 bytes**
- Per minute: **1.92 MB**
- One-hour interview session: **115.2 MB** (raw PCM)
- With Opus at 16 kbps: **7.2 MB** per hour (**16:1 compression**)

### Voice Activity Detection separates speech from silence

**WebRTC VAD** uses a Gaussian Mixture Model classifier analyzing spectral features via FFT. It processes 10/20/30ms frames of 16-bit mono PCM and outputs binary speech/non-speech per frame. Four aggressiveness modes (0–3) adjust the confidence threshold — mode 0 captures all speech with more false positives, mode 3 applies strict filtering that may clip speech edges. It runs in **<1ms per frame** at only **158 KB**. However, it struggles to distinguish speech from non-speech noise like music or TV.

**Silero VAD** uses a deep neural network with multi-head attention on STFT features. It outputs a continuous probability [0.0–1.0] per chunk and runs in **~1ms on CPU**. It significantly outperforms WebRTC VAD in noisy environments because it uses learned features from massive multilingual training data rather than hand-crafted GMM rules. The tradeoff is a larger footprint requiring PyTorch or ONNX Runtime.

**End-of-utterance detection** is the largest single contributor to voice agent latency. A **500ms silence threshold** (industry default used by Deepgram and most STT providers) adds 500ms to every turn. Modern semantic endpointing — using transformer models that predict turn completion from partial transcripts — can reduce this to **~200ms** by detecting linguistic completion before silence occurs. LiveKit's 135M-parameter EOU model reads partial transcripts and fires before the speaker finishes pausing.

### Audio encoding: Opus dominates for WebSocket transmission

For browser-to-server voice streaming, **Opus at 16–20 kbps** delivers excellent wideband speech quality with **16:1 compression** over raw PCM. It has 26.5ms algorithmic delay (reducible to 5ms), built-in forward error correction for packet loss resilience, and is mandatory for WebRTC (RFC 7874). All modern browsers support it. The WebM container wraps Opus for MediaRecorder API output in browsers.

For server-to-browser TTS playback, **Opus in OGG/WebM** provides compressed streaming with native browser decoding. For internal pipeline processing (TTS output → processing), **raw PCM** avoids all encoding overhead.

### Python asyncio powers the concurrent voice pipeline

The asyncio event loop is a **single-threaded scheduler** using OS-level I/O multiplexing (epoll on Linux, kqueue on macOS). A coroutine defined with `async def` creates a coroutine object that maintains its own stack frame. When `await` is encountered, the coroutine suspends — preserving state — and yields control back to the event loop, which can then advance other ready coroutines. This cooperative multitasking uses **~8 KB per Task** versus **~64 KB per thread**, enabling 10,000+ concurrent connections per process.

**FastAPI + Uvicorn implement ASGI** (Asynchronous Server Gateway Interface), which extends WSGI with WebSocket and HTTP/2 support. Uvicorn uses **uvloop** — a Cython-based event loop on libuv (same as Node.js) — achieving **2–4x speedup** over the default asyncio loop. A single Uvicorn process with uvloop handles ~20,000 concurrent WebSocket connections.

**WebSocket protocol details:** The connection begins with an HTTP upgrade handshake where the client sends `Upgrade: websocket` and `Sec-WebSocket-Key`. The server responds with HTTP 101 and `Sec-WebSocket-Accept` (SHA1 hash proving WebSocket awareness). Frames use opcodes: 0x1 (text), 0x2 (binary), 0x8 (close), 0x9 (ping), 0xA (pong). Client-to-server frames must be masked with a random 32-bit key to prevent cache-poisoning attacks on intermediary proxies. Ping/pong heartbeats (default 20-second interval in Uvicorn) detect dead connections.

**Backpressure** is critical in the voice pipeline. When ASR can't keep up with incoming audio at 32 KB/s, unbounded queuing grows at ~1 MB per 30 seconds per connection. The solution is bounded `asyncio.Queue` with explicit overflow policies — drop oldest frames for real-time priority, or block producers at high-water marks. When the user interrupts (barge-in), all queued TTS audio must be flushed immediately.

### Whisper architecture and faster-whisper optimization

Whisper is an **encoder-decoder transformer** trained on **680,000 hours** of weakly supervised web audio. The encoder processes a **log-mel spectrogram** (80 filter banks, 25ms windows, 10ms hop) through two Conv1D layers and transformer blocks. The decoder autoregressively predicts tokens using causal self-attention and cross-attention to encoder representations. Model sizes range from tiny (39M) to large-v3 (1.55B parameters). The **turbo** variant (809M params, 4 decoder layers instead of 32) offers large-v2 accuracy at ~8x speed.

**faster-whisper** reimplements Whisper using **CTranslate2**, a C++ inference engine with weight quantization (INT8/FP16), layer fusion, and optimized kernels. It achieves **4x speedup** with identical accuracy: transcribing 13 minutes of audio in ~54 seconds (vs ~4.5 minutes for original Whisper on RTX 3070 Ti). With batched inference + INT8, it reaches ~16 seconds — **nearly 8x faster**.

**Streaming ASR vs batch:** Whisper cannot natively stream due to its 30-second chunk constraint and autoregressive decoder. **Deepgram Nova-3** uses a native streaming architecture achieving **<300ms latency** with sub-7% WER. For SpeakPrep, the recommended approach is Deepgram for real-time transcription with faster-whisper as an offline fallback for detailed analysis.

**ASR hallucination** affects **40.3%** of non-speech audio segments. Common patterns include repeated phrases, YouTube boilerplate ("Thanks for watching"), and random text during silence. Prevention requires layered defense: Silero VAD preprocessing (most effective single mitigation), compression ratio filtering (threshold 2.4), log probability thresholds, and no-speech probability filtering.

**Word Error Rate** = (Substitutions + Deletions + Insertions) / Total Words. Current benchmarks: Deepgram Nova-3 achieves **<5% WER** on clean speech; Whisper large-v3 hits **5–8%** clean and **10–13%** noisy. Production WER degrades **2.8–5.7x** from benchmark conditions. For interview coaching, target **<10% WER** for clean conversational speech.

### LLM integration: Groq wins on latency, Gemini on cost

**Token streaming** uses Server-Sent Events where each chunk contains a `delta` object with incremental tokens. For voice AI, tokens must be buffered into complete sentences before sending to TTS — split on `.?!;` boundaries using regex, handling edge cases like "Dr." and "3.14". The triple-buffer pipeline pattern is: while generating sentence N+1 with LLM, synthesize sentence N with TTS, play sentence N-1.

**LLM provider comparison for real-time voice:**

| Provider | Input $/1M | Output $/1M | Tokens/sec | TTFT |
|---|---|---|---|---|
| **Groq Llama 3.1 8B** | $0.05 | $0.08 | 840 | <100ms |
| **Groq Llama 3.3 70B** | $0.59 | $0.79 | 394 | <100ms |
| **Cerebras Llama 3.3 70B** | ~$0.60 | ~$0.80 | 2,100–2,500 | 80–150ms |
| **Gemini 2.5 Flash-Lite** | $0.10 | $0.40 | ~200 | ~420ms |
| **OpenAI GPT-4o-mini** | $0.15 | $0.60 | ~100–150 | 300–600ms |
| **OpenAI GPT-4o** | $2.50 | $10.00 | ~80–100 | 300–800ms |

**Winner for real-time voice: Groq** with sub-100ms TTFT — unmatched for conversational cadence. Use Llama 3.1 8B ($0.05/$0.08) for routine interview turns, escalate to 70B for scoring and complex evaluation. Implement a **multi-provider fallback chain** with circuit breakers: Groq (primary) → Cerebras → GPT-4o-mini, using exponential backoff with jitter and the circuit breaker pattern (closed → open after 5 failures → half-open after 60s cooldown → probe → closed).

**System prompt design** for voice AI interview coaching must enforce conciseness (under 3 sentences per response), ban markdown/bullets, require one question at a time, enable follow-up probing ("Can you be more specific?"), and use conversational fillers ("That's interesting...") for natural flow. Temperature 0.7–0.9 for engaging variety. Use separate prompts for behavioral (STAR probing), technical (algorithm walkthroughs), and system design (requirements → high-level → deep dive → tradeoffs).

**Context window management:** Use a hybrid approach — system prompt (~500 tokens) + condensed resume summary (~300 tokens) + interview state summary (~200 tokens) + scoring criteria (~200 tokens) + last 4–6 messages verbatim (~800 tokens) = **~2,000–3,000 tokens per request**. This keeps latency and cost low while preserving conversational continuity.

### Neural TTS and Kokoro deliver production-quality voice

The neural TTS pipeline flows: text → text normalization → grapheme-to-phoneme → acoustic model → mel spectrogram → vocoder → waveform. Modern systems like **VITS** combine acoustic model and vocoder end-to-end. Vocoders have evolved from WaveNet (sample-by-sample, impractically slow) to **HiFi-GAN** (167x real-time on GPU) to **BigVGAN** (universal vocoding, 44–75x real-time).

**Kokoro TTS** is built on **StyleTTS 2 architecture** with an ISTFTNet vocoder, using only the decoder path at inference — no diffusion model, no separate encoder. At just **82M parameters**, it achieved **#1 on the HuggingFace TTS Arena**, outperforming models 6–15x larger. Key metrics: **RTF ~0.03 on A100** (33x faster than real-time), **3–11x real-time on CPU**, 54 voices across 8 languages, **Apache 2.0 license**. It produces 24 kHz audio at ~40–70ms latency per sentence on GPU.

**Streaming TTS implementation** requires the triple-buffer pipeline: LLM generates → sentence buffer splits at boundaries → TTS synthesizes per sentence → audio buffer plays with crossfade. Barge-in detection (user speaks during TTS playback) requires always-on VAD monitoring with echo cancellation, sustained speech requirement (100–300ms) to avoid false triggers, and immediate TTS cancellation + audio buffer flush on confirmed interruption.

**Audio format for output:** Use **Opus in OGG/WebM at 32–48 kbps** for browser streaming — optimal latency (5–26.5ms encoding), excellent quality, minimal bandwidth (~4–6 KB/s). Bandwidth comparison for 1 minute of 24 kHz mono voice: PCM = 2.88 MB, Opus 32 kbps = 240 KB (**83x smaller**).

### WebSocket protocol design for the voice pipeline

**Seven message types** on a single WebSocket: `session_control` (JSON), `audio_data` (binary), `transcription` (JSON), `llm_response` (JSON), `tts_audio` (binary), `error` (JSON), `heartbeat` (JSON). The conversation state machine cycles: **IDLE → LISTENING → PROCESSING → SPEAKING → IDLE**, with interruption support for direct SPEAKING → LISTENING transition.

**Reconnection strategy:** Use exponential backoff with jitter (500ms → 1s → 2s → 4s → 8s → cap at 30s, max 10–15 attempts). Preserve session state in Redis with a session token; on reconnect, the client sends `{type: "session_resume", session_token: "abc123", last_seq: 42}` and any server can restore state from Redis and replay missed messages.

**Horizontal scaling** WebSocket servers is harder than REST because connections are persistent and stateful. Use sticky sessions (IP hash or cookie-based) at the load balancer plus **Redis pub/sub** as a message bus for cross-server communication. A single tuned server handles **10K–100K** connections depending on resources. For SpeakPrep Phase 1, a single Uvicorn process with uvloop handles the expected load.

### PostgreSQL schema and Redis for the data layer

The core schema requires tables for `users`, `resumes` (with JSONB `parsed_content` for flexible structured data), `sessions` (with `session_type`, `difficulty_level`, `overall_score`), `questions` (tagged question bank with GIN indexes on `tags`), `responses` (transcript, audio URL, LLM feedback as JSONB), and `scores` (per-dimension scoring). Key indexes: `(user_id, created_at DESC)` on sessions for dashboard queries, GIN indexes on JSONB columns for flexible querying.

**Redis/Valkey** serves as the real-time backbone: WebSocket session state (Hashes with TTL), audio processing queues (Lists), rate limiting counters (Strings with INCR+EXPIRE), LLM response caching, pub/sub for cross-server events, and sorted sets for leaderboards. **Valkey** (BSD 3-Clause fork of Redis by Linux Foundation) is recommended for new projects — fully open source with no vendor lock-in, compatible wire protocol, and competitive performance at **~1M ops/sec on 8 vCPU**.

**Connection pooling** is essential: each PostgreSQL connection forks a backend process consuming 5–10 MB RAM, with a default limit of 100 connections. Use **asyncpg** (5x faster than psycopg3 in raw throughput, native binary protocol, built-in pooling) with pool_size = `num_cores × 2 + 1`. For SQLAlchemy async, wrap via `postgresql+asyncpg://` dialect with `pool_pre_ping=True` to detect dead connections.

### Infrastructure: Docker, Caddy, Cloudflare Tunnel, GitHub Actions

**Docker networking:** Always use custom bridge networks (never the default bridge). Services on the same custom network resolve each other by name via Docker's embedded DNS at 127.0.0.11. Segment networks: `frontend` for Caddy + API, `backend` (with `internal: true`) for database + Redis — isolating sensitive services from external access.

**Cloudflare Tunnel** creates outbound-only encrypted connections from your server to Cloudflare's edge. No public IP needed, no open inbound ports, no firewall rules. Automatic SSL/TLS, built-in DDoS protection, native WebSocket support. Free tier with unlimited tunnels. Superior to ngrok (which is for development) and Tailscale (which is for private networking).

**Caddy** handles automatic HTTPS via ACME protocol — it obtains, installs, and renews Let's Encrypt certificates with zero configuration. Critical for voice AI: use `flush_interval -1` in the reverse_proxy directive to prevent response buffering that breaks WebSocket and streaming connections. Caddy is ~15–25% the configuration complexity of nginx with equivalent or better performance for small teams.

**Zero-downtime deployment** on a single server uses blue-green strategy: deploy new version to inactive environment, wait for health check, switch reverse proxy, stop old environment. For solo developers, `docker compose up -d --force-recreate` with fast-starting containers and health checks provides <2-second downtime — acceptable for Phase 1.

**GitHub Actions CI/CD pipeline:** lint (ruff + mypy) → test (with PostgreSQL/Redis service containers) → build Docker image → push to GHCR → SSH deploy to server → run Alembic migrations → recreate containers → health check verification. Use `type=gha` Docker layer caching with `mode=max` for all layers.

### Security: JWT, rate limiting, and voice-specific threats

**JWT authentication:** Store access tokens (15-minute expiry) in memory (JavaScript variable) and refresh tokens (7-day expiry) in httpOnly/Secure/SameSite=Strict cookies. For WebSocket authentication, use **first-message auth** — the client sends `{type: "auth", token: jwt}` immediately after connection, and the server validates before accepting other messages. This keeps tokens out of URLs and server logs.

**Rate limiting** uses Redis with sliding window counters (best accuracy/performance balance). Recommended limits: 3 concurrent WebSocket connections per user, 60 req/min for general API, 5 req/min for auth/login, 100 LLM/TTS calls per day per user (cost management).

**Voice AI-specific security concerns:** LLM prompt injection via voice (users speaking "ignore all instructions") requires strict prompt segregation — treat all user input as DATA, never as COMMANDS. Audio data privacy requires encryption at rest (AES-256), WSS for transmission, automated PII redaction in transcripts, and GDPR/CCPA-compliant retention policies (30-day auto-delete). WebSocket endpoints need origin checking against an allowlist and authentication timeout (5 seconds to send auth message or disconnect).

**Secrets management for a solo developer:** Use `.env` files (in `.gitignore`) for development, GitHub repository secrets for CI/CD, and Docker environment variables from GitHub secrets during deployment. Install gitleaks pre-commit hooks to prevent accidental commits. Rotate secrets by generating new → deploying → verifying → removing old → revoking at provider.

---

## SECTION 3: Interview coaching product features

### Resume parsing uses a hybrid PDF-to-LLM pipeline

The recommended pipeline is **PyMuPDF → text → LLM structured extraction → Pydantic validation**. PyMuPDF extracts text in **0.1 seconds** (50–70x faster than pdfminer). Send extracted text to GPT-4o/Llama with a structured output schema requiring: personal info, work experience (company, title, dates, description, highlights), education, skills (technical, soft, languages), certifications, and projects. Validate with Pydantic and handle edge cases: image-based PDFs trigger OCR with Tesseract/Surya, poorly formatted PDFs fall back through PyMuPDF → pdfplumber → OCR.

Resume data personalizes interviews: experience-based behavioral questions targeting specific roles/companies, skill-gap analysis comparing resume against target job requirements, seniority calibration (years of experience → difficulty adjustment), and project deep-dives for technical follow-ups.

### Question bank design with STAR scoring rubrics

**Behavioral questions** use the STAR method (Situation, Task, Action, Result) with **10–20 questions per category** across leadership, teamwork, conflict resolution, failure/growth, and decision-making. Scoring rubric (1–5): Score 5 requires all STAR components with specific details, quantified results, and self-reflection. Score 1 indicates no structure, hypothetical answers, or irrelevance.

**Technical questions** span algorithms, data structures, system concepts, and language-specific topics across easy/medium/hard difficulty tiers. Voice-only evaluation focuses on problem decomposition, algorithm selection rationale, complexity analysis, edge cases, and tradeoff discussion.

**System design questions** follow a guided flow: requirements gathering (2 min) → high-level design (5 min) → component deep dive (5 min) → tradeoffs and scaling (3 min). Score on requirements completeness, architectural cleanliness, tradeoff awareness, and failure handling.

### AI-powered scoring across five dimensions

| Dimension | Weight | What to Measure |
|---|---|---|
| Content Quality | 30% | Relevance, completeness, depth, technical accuracy |
| Communication | 25% | Clarity, logical structure, conciseness |
| STAR Compliance | 20% | All 4 components, specificity, quantified results |
| Confidence Markers | 15% | Hedging language, assertiveness, vocal steadiness |
| Filler Words | 10% | Frequency of um/uh/like/you know per minute |

**Implementation:** Send transcript + scoring rubric + context to LLM with temperature=0 for deterministic output and a fixed model version to prevent drift. Force structured JSON response with per-dimension scores (1–5), specific feedback, strengths, and improvements. Calibrate with few-shot examples at each score level. Optional ensemble voting (3 LLM calls, take median) increases consistency at 3x cost.

### Prosody analysis extracts confidence signals from audio

**Speaking rate benchmarks:** <110 WPM indicates uncertainty; **140–160 WPM is optimal for interviews** (perceived as most credible); >180 WPM signals rushing. Filler words below 2 per minute rate "excellent"; 2–5 is "good"; above 10 is "poor."

**Tools:** Use **openSMILE** for comprehensive speech feature extraction (F0, loudness, jitter, shimmer, MFCCs in a few lines of code). Use **Parselmouth** (Praat wrapper) for detailed phonetic analysis when needed. Track pitch variation (moderate = confident, monotone = disengaged), volume consistency, pause patterns (strategic pauses vs. hesitation), and jitter/shimmer (vocal tremor indicators).

### Adaptive difficulty uses an ELO-based progression system

**Readiness signals for advancement:** Consistent scores ≥4.0/5.0 for 3+ consecutive sessions, fast response time with high quality, follow-up handling scores ≥3.5, full STAR compliance in >80% of behavioral answers, and filler words <3/minute consistently.

**Four dimensions of difficulty progression:**
1. **Question complexity:** Simple recall → situational → multi-part → curveball/adversarial
2. **Interviewer behavior:** Friendly/encouraging → neutral → challenging/pushback → adversarial/interrupting
3. **Follow-up depth:** None → 1 gentle → 2–3 probing → continuous drilling to knowledge boundary
4. **Time pressure:** Unlimited → 5 min → 3 min → 2 min per question

**Algorithm:** Start with threshold-based (MVP), graduate to **ELO-based system** targeting **60–75% expected success rate** (the "zone of proximal development"). ELO updates both student ability and question difficulty after each interaction. Start with K=40 for fast convergence on new users, decrease to K=16 for stable users. Select questions where expected success probability is closest to 0.65–0.75. Never jump more than 1 difficulty level at a time; drop immediately after 2 consecutive poor scores.

**Preventing frustration** (from Duolingo's Birdbrain system): Mix 70% appropriately-difficult questions with 20% confidence boosters and 10% stretch questions. Monitor session completion rates — if users abandon sessions, auto-reduce difficulty.

---

## SECTION 4: Learning resources and open-source references

### Essential resources by technology

**Python asyncio:** "Python Concurrency with asyncio" by Matthew Fowler (Manning, 2022) is the most comprehensive practical book. Real Python's "Async IO in Python: A Complete Walkthrough" is the best free tutorial. Official docs at docs.python.org/3/library/asyncio.html.

**System design:** "Designing Data-Intensive Applications" by Martin Kleppmann (2nd edition, Jan 2026) is the single most important book — now covering cloud-native architectures and AI/ML data systems. "System Design Interview" Volumes 1 & 2 by Alex Xu for practical interview-focused patterns.

**Speech AI:** faster-whisper GitHub (SYSTRAN/faster-whisper) for production ASR. Kokoro TTS (hexgrad/kokoro) for local TTS. HuggingFace Audio Course (free) for transformers-based speech processing. Stanford CS224S for academic foundations.

**Infrastructure:** Docker official docs for containerization. Caddy docs for automatic HTTPS. Hetzner for production hosting (**3–6x cheaper** than alternatives at €3.79/mo for 2 vCPU/4GB), DigitalOcean for learning (excellent tutorials).

### Critical open-source projects to study

**Pipecat** (~11,155 stars, by Daily.co) is the **most directly relevant project** — it demonstrates production voice AI pipeline architecture with frame-based processing, proper async patterns, VAD integration, interruption handling, and real-time audio streaming. Supports 100+ AI services with client SDKs for JS, React, React Native, Swift, Kotlin.

**LiveKit** (~25,000+ stars) shows scalable real-time audio/video infrastructure with WebRTC SFU architecture and horizontal scaling via Redis + Kubernetes.

**faster-whisper** (~15,000+ stars) demonstrates CTranslate2 optimization, INT8 quantization, and batched inference achieving 12.5x speedup over original Whisper.

**AI Mock Interviewer** (IliaLarchenko/Interviewer) is a speech-first interview interface supporting multiple LLM providers — the closest open-source analog to SpeakPrep.

### Twenty mistakes junior developers make that seniors avoid

The most critical for voice AI systems:

**Blocking the event loop** — calling synchronous functions (file I/O, `requests.get()`, Whisper inference) inside async handlers freezes all concurrent connections. Use `asyncio.to_thread()` or dedicated worker processes.

**Ignoring backpressure** — pushing audio data faster than consumers can process causes unbounded queue growth and eventual OOM. Use bounded queues with explicit drop policies.

**Not measuring latency per pipeline stage** — only tracking end-to-end latency makes bottleneck identification impossible. Instrument every stage: audio capture, network, STT processing, LLM TTFT, TTS synthesis, network delivery. Set explicit latency budgets per stage (target <300ms total).

**Sequential instead of streaming pipelines** — running STT→LLM→TTS sequentially adds all latencies together. Senior engineers implement streaming where TTS starts synthesizing as the first LLM sentence completes, achieving sub-second response times.

**Deploying pipeline components across distant regions** — a voice system with STT in Virginia, LLM in London, and TTS in Tokyo adds 300–500ms of network latency. Co-locate all pipeline components.

**Not pre-warming models** — cold starts in STT/TTS add hundreds of milliseconds to the first turn. Run dummy inference at startup to eliminate JIT compilation delays.

**Testing with only one concurrent user** — most voice AI demos work flawlessly in single-user testing. Production systems fail at 10–30 concurrent calls due to GPU memory fragmentation, connection pool starvation, and provider rate limiting.

---

## Conclusion: architectural decisions that matter most

SpeakPrep's competitive advantage will come from three architectural choices. First, **Groq's sub-100ms TTFT** enables conversational cadence that no competitor using GPT-4o (300–800ms TTFT) can match. Second, **Kokoro TTS at 82M parameters** runs 33x real-time on GPU and achieves real-time on CPU — enabling either cloud efficiency or future edge deployment. Third, the **triple-buffer streaming pipeline** (LLM generates sentence N+1 while TTS synthesizes sentence N while audio plays sentence N-1) compresses perceived latency to under 500ms for natural conversation.

The biggest technical risk is not any single component but the **integration complexity** of the full pipeline: audio capture → Opus encoding → WebSocket → Silero VAD → Deepgram streaming ASR → sentence buffering → Groq LLM streaming → sentence splitting → Kokoro TTS → Opus encoding → WebSocket → browser playback. Each handoff point is a potential latency source and failure mode. The recommended mitigation is to build on **Pipecat's frame-based architecture** rather than implementing the pipeline from scratch, customize the interview logic layer, and invest instrumentation time in per-stage latency monitoring from day one.

The market timing is favorable: the AI interview coaching segment is growing at 30.6% CAGR, existing tools have clear gaps (no realistic voice conversation, no end-to-end coverage, no adaptive difficulty), and the required infrastructure — fast LLM inference, high-quality open-source TTS, streaming ASR APIs — has only recently become viable and affordable.
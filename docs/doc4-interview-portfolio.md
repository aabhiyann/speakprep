# SpeakPrep — Document 4: Interview Story + Portfolio Guide
### Version 1.0 | Author: Abhiyan Sainju | April 2026

---

> **How to use this doc:** This is your interview prep artifact for the project itself. It tells you exactly how to talk about SpeakPrep in recruiter screens, technical interviews, and hiring manager conversations. Update it as you build — the best answers come from real experiences, not hypothetical ones.

---

## TABLE OF CONTENTS

1. [The Core Narrative](#1-the-core-narrative)
2. [Recruiter Screen Answers](#2-recruiter-screen-answers)
3. [Hiring Manager Conversation](#3-hiring-manager-conversation)
4. [Technical Interview Answers](#4-technical-interview-answers)
5. [System Design Walkthrough](#5-system-design-walkthrough)
6. [The Five Key Decisions (Memorize These)](#6-the-five-key-decisions)
7. [The Three Bug Stories](#7-the-three-bug-stories)
8. [Questions to Expect + How to Answer](#8-questions-to-expect--how-to-answer)
9. [Portfolio Presentation Guide](#9-portfolio-presentation-guide)
10. [What to Update As You Build](#10-what-to-update-as-you-build)

---

## 1. The Core Narrative

Every interview answer about SpeakPrep should connect back to one core story. Internalize this, then adapt it to each context.

### The One-Paragraph Story

> "After graduating from GW with my MS in CS, I was going through the job search myself and frustrated by the gap between available interview prep tools and what an actual interview feels like. So I built SpeakPrep — a real-time voice AI mock interview coach. You speak naturally, the AI transcribes your answer, generates an intelligent response through an LLM, converts it to speech, and plays it back — all in under 2 seconds end-to-end. I made every technical decision myself: the WebSocket architecture, choosing Groq over OpenAI for sub-100ms inference, self-hosting Kokoro TTS instead of paying per character, running the entire stack on Oracle Cloud's free ARM tier. It's deployed, real users have used it, and I can talk through any layer of the system."

### Why This Narrative Works

- **Personal motivation** — not a textbook project, you needed this yourself
- **Technical depth signal** — you mention specific tradeoffs, not just the tech list
- **Deployed product** — not a classroom exercise or a GitHub repo nobody uses
- **Ownership** — "I made every decision" — this is what hiring managers want to hear
- **Concise** — 6 sentences, leaves room for follow-up questions

---

## 2. Recruiter Screen Answers

Recruiters evaluate: communication clarity, relevance to the role, enthusiasm.

### "Tell me about your most impressive project"

Keep to 60–90 seconds. Hit these points in order:
1. What problem it solves (1 sentence)
2. What the system does (2–3 sentences)
3. One technical challenge you overcame (1–2 sentences)
4. What makes you proud of it (1 sentence)

**Script:**

> "My standout project is SpeakPrep, an AI mock interview coach I built to solve a problem I was experiencing personally — existing tools like Google Interview Warmup just ask scripted questions with no follow-ups, while real interviewers probe and push back. I built a full voice pipeline: your speech streams to a Python backend over WebSockets, gets transcribed by Deepgram in real time, an LLM generates a contextual follow-up question, and Kokoro TTS converts it to audio — all in under two seconds end-to-end. The hardest technical challenge was implementing the streaming pipeline so TTS starts generating before the LLM finishes — if I waited for the full response, it would feel like a chatbot, not a conversation. I'm proud that it's genuinely deployed and has helped people practice before real interviews."

### "What tech stack did you use?"

Don't just list. Explain one choice.

> "Python FastAPI for the backend, WebSockets for real-time bidirectional audio, Groq for LLM inference — specifically because their LPU hardware gives me sub-100-millisecond time-to-first-token, which is essential for voice. Deepgram for streaming speech recognition, Kokoro TTS for synthesis — that's Apache 2.0 and runs on CPU so I don't pay per character. PostgreSQL for persistence, Valkey for session caching, Docker for deployment on Oracle Cloud ARM."

### "Why did you build this instead of working on other projects?"

> "Honestly? I was in the interview gauntlet myself. I used ChatGPT for practice but it doesn't push back — it accepts whatever you say. Real interviewers probe weak answers. I wanted something that simulates that pressure, and I knew the technology to build it existed — streaming ASR, fast LLM inference, neural TTS — they just hadn't been combined into a focused product. So I built it, and the process taught me things about real-time systems, asyncio, audio pipelines, and production deployment that I couldn't get from coursework."

---

## 3. Hiring Manager Conversation

Hiring managers evaluate: product thinking, ownership, learning velocity, how you'd work on a team.

### "Walk me through a product decision you made"

> "The most important product decision was narrowing from 'general voice AI' to 'interview coach specifically.' I was tempted to build something broad, but broader means less compelling to any one user. By focusing on interview coaching, I had a clear user with a clear pain point — job seekers who need realistic conversational practice — and a measurable outcome: did their scores improve? Did they land the job? That focus changed everything downstream: what the system prompt says, what data to collect, what the progress dashboard shows. Every feature exists to serve that specific workflow."

### "What would you have done differently?"

> "I'd have instrumented latency earlier. I spent two weeks building before I added per-stage timing. When I finally did, I discovered Kokoro TTS was my biggest bottleneck — not Groq or Deepgram as I assumed. With earlier data, I would have optimized differently. Also, I'd set up VAD from day one instead of using fixed-duration recording. Proper end-of-utterance detection changed the conversational feel dramatically. Both mistakes cost me time that early measurement would have saved."

### "How did you prioritize what to build?"

> "I had a simple rule: if it doesn't make the voice session feel more like a real interview, it waits. Progress dashboards, resume parsing, user accounts — all deferred until the core voice loop was solid. That meant Phase 1 was just getting voice in, voice out, end to end. No auth. No database. No product UI. Just the pipeline. I find you can always add product features on top of a working core, but you can't easily rebuild the core under a product that's already launched."

---

## 4. Technical Interview Answers

Engineers evaluate: problem-solving approach, depth of understanding, ability to reason about tradeoffs.

### "Explain a complex technical concept from your project to a non-technical person"

Use audio pipeline as the example.

> "When you speak into SpeakPrep, three things happen in parallel, like an assembly line that doesn't wait for the previous station to finish. First, your voice is converted into numbers — 16,000 measurements per second — and streamed to my server over the internet. Second, those numbers get converted to text by a speech recognition model. Third, that text goes to an AI that generates a response, which gets converted back to speech. What makes it feel conversational is that I start synthesizing the audio before the AI finishes its full response. As soon as the first complete sentence comes out of the AI, I immediately start generating the audio for it — while the AI is still writing the second sentence. By the time you've heard sentence one, sentence two is already synthesized and ready. That's why it sounds like a real conversation rather than waiting for a computer."

---

## 5. System Design Walkthrough

When asked "Design a real-time voice AI assistant" — this is your answer.

### The 5-Minute Whiteboard Answer

**Step 1: Clarify requirements (30 seconds)**
> "Before designing, let me clarify: are we targeting web, mobile, or both? How many concurrent users? What's the latency requirement — under 2 seconds for the voice round-trip? And are we building from scratch or using external APIs for ASR/LLM/TTS?"

**Step 2: High-level design (1 minute)**
```
Client (Browser/Mobile)
    ↕ WebSocket (audio up, audio down)
Backend (Python FastAPI)
    ├── VAD → ASR → LLM → TTS (pipeline)
    ├── PostgreSQL (sessions, history, scores)
    └── Redis/Valkey (session state, rate limiting)
```

> "I'd choose WebSockets over REST because voice requires bidirectional streaming. REST is request-response — you can't stream audio continuously in both directions. WebSockets give me a persistent connection where binary audio data flows up and synthesized audio flows down simultaneously."

**Step 3: The pipeline in detail (2 minutes)**

> "The pipeline has four stages. First, Voice Activity Detection — I need to know when the user stops speaking before I start transcribing. I use Silero VAD, a neural network that outputs speech probability continuously. When probability drops below 0.35 for 400ms, I trigger transcription.

> Second, ASR — I stream the accumulated audio to Deepgram, which is purpose-built for streaming with sub-300ms latency. Deepgram returns partial transcripts as you speak, which I show in the UI immediately.

> Third, LLM — the final transcript goes to Groq running Llama 3.3 70B. The critical metric here is time-to-first-token, not throughput. Groq achieves under 100ms TTFT on their LPU hardware. I stream the response token by token.

> Fourth, TTS — I don't wait for the full LLM response. As each sentence completes in the token stream, I immediately synthesize it with Kokoro TTS and stream the audio to the client. This is the triple-buffer pipeline: LLM generates sentence N+1 while TTS synthesizes sentence N while the client plays sentence N-1."

**Step 4: Data layer (30 seconds)**

> "PostgreSQL for durable storage: users, sessions, turn transcripts, scores. Valkey — Redis-compatible — for ephemeral session state: active connections, LLM context cache with 1-hour TTL, rate limiting counters. The split is important: session state must survive backend restarts for reconnection, hence Valkey."

**Step 5: Scaling (30 seconds)**

> "At small scale, a single process handles everything. To scale horizontally, the key challenge is WebSocket servers — persistent connections, not stateless. Solution: sticky sessions at the load balancer plus Redis pub/sub as a message bus. If user A connects to server 1 and sends a message that server 2 needs to process, server 1 publishes to Redis, server 2 subscribes and responds. Database read replicas for analytics queries, connection pooling via asyncpg."

---

## 6. The Five Key Decisions

Memorize these. Know the context, the alternatives, and the reasoning cold.

---

### Decision 1: WebSockets over REST

**Context:** Needed a protocol for real-time bidirectional audio streaming.

**What you rejected:** REST polling (adds 100ms minimum artificial latency, wastes bandwidth, no binary streaming), Server-Sent Events (one-directional only), gRPC (excellent for server-to-server but browser support requires proxy), WebRTC (designed for P2P video, massive overkill and complexity).

**Why WebSockets:** Bidirectional, binary-capable, universally supported in all browsers and React Native, 2-byte frame overhead vs 700+ bytes for HTTP headers, native async support in FastAPI.

**The consequence you learned:** Load balancers need sticky sessions. Debugging WebSocket issues is harder — no `curl` equivalent, need `wscat` or browser devtools WebSocket inspector.

---

### Decision 2: Groq over OpenAI for LLM

**Context:** LLM must respond fast enough for natural voice conversation.

**What you rejected:** OpenAI GPT-4o (300–800ms time-to-first-token — too slow), self-hosted Llama (5–15 tokens/sec on CPU — catastrophically slow for real-time), Gemini Flash (420ms TTFT — borderline).

**Why Groq:** LPU (Language Processing Unit) hardware designed for inference. Sub-100ms TTFT consistently. 315 tokens/sec on Llama 70B. Free tier covers development. OpenAI-compatible API so switching providers is a config change.

**The consequence you learned:** Rate limiting at 30 RPM on free tier requires a multi-provider fallback chain. LLM quality is Llama 70B, not GPT-4o — calibrated for conversational use where quality difference is minimal.

---

### Decision 3: Self-Hosted Kokoro TTS over ElevenLabs

**Context:** Need high-quality TTS with no per-character cost at launch.

**What you rejected:** ElevenLabs (10,000 chars/month free ≈ 10 minutes — depleted in hours with real users), Cartesia (20,000 chars/month — still limited), Google Cloud TTS (4M chars free but 6/10 quality — users notice).

**Why Kokoro:** Apache 2.0 license (commercial use free), ranked #1 on HuggingFace TTS Arena at 8.5/10 quality, runs on CPU at 3–11x real-time, 82M parameters (tiny — fits easily in Oracle ARM's 24 GB), unlimited usage. The architectural insight: if you can self-host a model of equivalent quality, you should.

**The consequence you learned:** Must maintain the Docker deployment yourself. ARM64 Docker image required — found `ghcr.io/remsky/kokoro-fastapi-cpu:latest` which supports arm64.

---

### Decision 4: Oracle Cloud ARM over AWS for Compute

**Context:** Need always-on compute with enough RAM to run the full stack.

**What you rejected:** AWS EC2 t3.micro (1 GB RAM — can't fit FastAPI + Whisper + Kokoro + Valkey simultaneously), Render free tier (512 MB RAM + sleeps after 15 minutes — breaks WebSocket sessions), Railway (killed free tier in 2023).

**Why Oracle ARM:** 4 OCPUs, 24 GB RAM, genuinely always-free with no expiration. Fits entire stack with ~20 GB headroom. Oracle has maintained this tier since 2019.

**The consequence you learned:** ARM architecture requires `--platform linux/arm64` in Docker builds. Some images don't have ARM64 variants — must build from source. Oracle may reclaim instances with CPU < 20% — keep-alive script prevents this.

---

### Decision 5: Streaming Pipeline over Sequential

**Context:** How to minimize perceived latency from voice in to voice out.

**Sequential approach (rejected):** Record audio → transcribe → wait for full LLM response → synthesize full audio → play. Total latency: 4–8 seconds.

**Why streaming pipeline:** Start TTS synthesis on sentence 1 while LLM is still generating sentence 2 while client plays sentence 0. Perceived latency = time to first word of response ≈ 800–1,200ms instead of 4–8 seconds. The architectural pattern: decompose the pipeline into stages that can overlap rather than waiting for each stage to fully complete.

**The consequence you learned:** Sentence splitting is harder than expected. "Dr. Smith spent $3.5M" splits incorrectly on "Dr." Fix: custom sentence splitter with abbreviation awareness. Also: must handle LLM generating partial sentences without terminal punctuation — flush remaining buffer at stream end.

---

## 7. The Three Bug Stories

Real bugs make you credible. These are the best ones to tell.

---

### Bug 1: Whisper Hallucinating on Silence

**The situation:** In Phase 1, after implementing the basic pipeline, Whisper would output random text whenever the user paused or there was background noise. Phrases like "Thanks for watching. Please like and subscribe." appeared out of nowhere during silence.

**Why it happened:** Whisper is trained on internet audio — YouTube videos, podcasts, lectures. When it encounters silence or noise, it doesn't output nothing. It outputs what would typically follow that pattern in training data. 40.3% of non-speech audio segments produce hallucinations.

**How I found it:** I was testing and noticed the AI responding to things I never said. Logged the transcript and saw gibberish output.

**The fix:** Multi-layer defense. First: add Silero VAD before sending to Whisper — only send confirmed speech segments. Second: check `info.no_speech_prob > 0.6` from Whisper's own output — it knows when it's uncertain. Third: compression ratio check — hallucinations are often repetitive text, which compresses unusually well.

**What I learned:** Never trust model output without validation. Production audio is nothing like benchmark audio. Models have failure modes that only appear in real conditions.

---

### Bug 2: Audio Chunks Playing Out of Order

**The situation:** In Phase 2, users would occasionally hear the second sentence of an AI response before the first. "Hello! Great question." played as "Great question! Hello!" — jarring and confusing.

**Why it happened:** The streaming pipeline processes sentences concurrently. Sentence 1 goes to Kokoro TTS simultaneously with Sentence 2. Short sentences ("I see.") synthesize faster than long ones. If Sentence 2 is synthesized before Sentence 1, the client receives them out of order.

**How I found it:** A test user mentioned the AI sounded "like it was stuttering" — responses weren't making sense. Logged the sequence numbers on arriving audio chunks and saw out-of-order arrivals.

**The fix:** Add a 4-byte sequence number header to every audio chunk binary frame. Client maintains a sorted queue — play in sequence order, buffer any out-of-order chunks until the expected sequence arrives. Also added a 50ms crossfade between chunks to eliminate audible gaps.

**What I learned:** Concurrent processing requires explicit ordering mechanisms. In distributed systems (even within one process), arrival order doesn't equal submission order.

---

### Bug 3: WebSocket Memory Leak — 200 Zombie Connections

**The situation:** After running for a week, the server started showing degraded performance. CPU was low, but memory kept climbing. New connections started taking longer to establish.

**Why it happened:** When users navigated away from the browser tab without explicitly disconnecting, the browser sent a close frame — but network conditions sometimes caused it to not reach the server. The server's connection tracking dict (`active_connections`) accumulated these stale entries. After 200 zombie connections, the dict was large enough to cause noticeable overhead.

**How I found it:** New Relic showed memory growing linearly, ~5 MB per hour. Added logging to the connection dict — saw 200+ entries with no recent heartbeat activity.

**The fix:** Heartbeat monitoring coroutine. Every 20 seconds, send a ping to each connection. If no pong received within 5 seconds, close the connection and remove from the dict. Also added connection.last_seen timestamp — close any connection not active in 10 minutes.

**What I learned:** Server resources are finite and non-obvious. WebSocket connections are persistent — unlike HTTP requests they don't clean themselves up. Any persistent resource needs an explicit cleanup mechanism.

---

## 8. Questions to Expect + How to Answer

### "Why not just use OpenAI's built-in voice features?"

> "OpenAI's Advanced Voice Mode is closed-source, costs per minute, and locks you into OpenAI's ecosystem. Building from components taught me how each layer works and lets me optimize them independently. I can swap the ASR layer without changing TTS, or switch LLM providers in a config change. The architectural flexibility is valuable — but the real reason was learning. You can't learn how voice AI systems work by using a black-box API."

### "How does this scale to 10,000 concurrent users?"

> "Today it's a monolith on a single Oracle ARM VM — that's fine for hundreds of concurrent sessions. To scale to 10,000, I'd decompose into services: dedicated ASR workers on GPU instances, an LLM gateway with provider routing and response caching, a TTS cluster. WebSocket servers need to be stateless — all session state moves to a Redis cluster. Load balancers use sticky sessions to route reconnects to the same server. PostgreSQL gets read replicas for dashboard queries and PgBouncer for connection pooling. The current architecture is already designed for this — WebSocket handlers don't store state locally, everything's in Valkey."

### "What's your biggest technical debt?"

> "The sentence splitter for the TTS pipeline. I built a regex-based heuristic that handles most cases but still breaks on edge cases — mathematical notation, quoted speech, nested parentheses. A proper solution would use a small classification model that reads context rather than pattern-matching. It would take 2–3 days to fix properly and I've deferred it because the current solution handles 95% of interview responses correctly. I'd fix it before scaling to 1,000+ users."

### "How did you test this?"

> "Three levels. Unit tests for pure functions — the sentence splitter, the STAR scorer, the ELO update logic — with pytest. Integration tests for the pipeline stages with real API calls using VCR cassettes to replay recorded API responses. And end-to-end tests where I run the full voice loop in a headless browser using Playwright, feeding pre-recorded audio files and verifying the response arrives within the latency budget. I also have manual regression testing — before every deployment, I run 5 test turns across behavioral, technical, and system design modes."

### "Tell me about a time you had to make a decision with incomplete information"

> "When choosing between Deepgram and self-hosted Faster-Whisper for ASR, I didn't know if $200 in Deepgram credits would cover my development and early user period. I estimated: 20 test users × 20 minutes/day × 30 days × $0.0077/min = $92. That gave me enough confidence to start with Deepgram. I made the decision with a clear understanding of the uncertainty and a fallback plan: if credits ran out unexpectedly, I had Faster-Whisper working as a fallback from Phase 1. The key was quantifying the uncertainty and having a fallback."

---

## 9. Portfolio Presentation Guide

### GitHub Repository Structure

```
speakprep/
├── README.md              ← CRITICAL — first thing reviewers see
├── docs/
│   ├── doc1-prd.md        ← Link from README
│   ├── doc2-architecture.md
│   ├── doc3-build-guide.md
│   └── adr/               ← Individual ADRs
│       ├── ADR-001-websocket.md
│       ├── ADR-002-web-first.md
│       └── ...
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── services/
│   │   ├── models/
│   │   └── api/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
└── docker-compose.prod.yml
```

### README.md Template

```markdown
# SpeakPrep — AI Mock Interview Coach

Real-time voice AI that simulates a realistic interview experience. 
Speak naturally, hear intelligent follow-up questions in <2 seconds.

**Live:** [app.speakprep.com](https://app.speakprep.com)
**Demo Video:** [2-minute walkthrough](youtube-link)

## Architecture

[Insert system diagram from Doc 2]

Voice pipeline: Browser WebAudio → WebSocket → VAD (Silero) → ASR (Deepgram) → LLM (Groq/Llama 70B) → TTS (Kokoro) → WebSocket → Browser AudioContext

End-to-end latency: ~800–1,400ms (measured, not estimated)

## Key Technical Decisions

| Decision | Choice | Why |
|---|---|---|
| Protocol | WebSockets | Bidirectional audio streaming |
| LLM | Groq/Llama 70B | Sub-100ms time-to-first-token |
| TTS | Kokoro (self-hosted) | Apache 2.0, CPU-capable, unlimited |
| Compute | Oracle Cloud ARM | 24 GB RAM, always free |

Full reasoning: [Architecture Decision Records](docs/adr/)

## Running Locally

\`\`\`bash
git clone https://github.com/abhiyansainju/speakprep
cd speakprep
cp .env.example .env  # Add your API keys
docker compose up -d
open http://localhost:5173
\`\`\`

## Tech Stack

Backend: Python 3.12, FastAPI, asyncio, SQLAlchemy, Alembic
AI: Deepgram (ASR), Groq + Llama 3.3 70B (LLM), Kokoro TTS
Data: PostgreSQL (Supabase), Valkey (Redis-compatible)
Infrastructure: Oracle Cloud ARM, Docker, Cloudflare Tunnel, GitHub Actions
Monitoring: New Relic, Sentry, PostHog
```

### Demo Video Script (60 seconds)

```
0–5s:  "SpeakPrep is a real-time AI mock interview coach I built from scratch."
5–10s: Show the session setup screen — pick behavioral, intermediate, neutral
10–15s: "I'll start a behavioral session about leadership." Press start.
15–30s: AI asks opening question. Show waveform while asking.
30–45s: Speak a 10-second STAR answer into mic. Show transcript appearing in real-time.
45–55s: AI response plays. Show that it's a follow-up ("You mentioned... can you elaborate?")
55–60s: Cut to latency metrics display. "800 milliseconds end-to-end."
```

### LinkedIn Post Template (for launch)

```
I spent 3 months building a real-time AI mock interview coach — here's what I learned:

The hard part wasn't the AI. It was the plumbing.

Getting voice in → text → LLM response → voice out in under 2 seconds requires:
• VAD to detect when you stop speaking
• Streaming ASR (not batch) for real-time transcript
• LLM with sub-100ms first-token latency (Groq, not OpenAI)
• TTS that starts generating before LLM finishes
• WebSockets, not REST, because REST can't stream audio both ways

The most surprising thing I built: a sentence splitter that knows "Dr." isn't a sentence ending but "." followed by a capital letter probably is. Edge cases everywhere.

The project: SpeakPrep — AI mock interview coach
[link]

Built with: Python FastAPI, Groq, Deepgram, Kokoro TTS, PostgreSQL, Oracle Cloud
Deployed: yes, actually, with real users
Cost per month: $0 (by design)

Full architecture writeup in the README if you're curious how it works.
```

---

## 10. What to Update As You Build

This doc starts as a template. As you actually build SpeakPrep, replace every placeholder below with real numbers and real stories.

### Update After Phase 1
- [ ] Replace "~800–1,400ms" with your actual measured P50 latency
- [ ] Fill in Bug Story 1 with details from your actual Whisper hallucination experience

### Update After Phase 2
- [ ] Fill in Bug Story 2 with your actual audio ordering issue (or replace with what you actually hit)
- [ ] Add specific WebSocket edge cases you discovered

### Update After Phase 3
- [ ] Add specific system prompt iteration stories — what worked, what didn't
- [ ] Document a specific scoring calibration decision

### Update After Phase 4
- [ ] Add real Oracle Cloud provisioning experience
- [ ] Document any infrastructure surprises
- [ ] Fill in actual uptime numbers from UptimeRobot

### Update After Phase 5
- [ ] Add user feedback quotes (with permission)
- [ ] Document a product decision you made based on user behavior data
- [ ] Add conversion metrics (free → paid if applicable)

### Update After Phase 6
- [ ] Add load test results (how many concurrent users before degradation?)
- [ ] Document security review findings
- [ ] Add ProductHunt/HN launch story

---

*End of Document 4 — Interview Story + Portfolio*
*All four documents together form the complete SpeakPrep Blueprint.*
*Documents cross-reference each other: PRD (Doc 1) → System Design (Doc 2) → Build Guide (Doc 3) → Portfolio Story (Doc 4)*

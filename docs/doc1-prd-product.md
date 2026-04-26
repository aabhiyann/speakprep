# SpeakPrep — Document 1: Product Requirements Document
### Version 1.0 | Author: Abhiyan Sainju | April 2026
### Status: LIVING DOCUMENT — update as product evolves

---

> **How to use this doc:** This is your single source of truth on WHAT you're building and WHY. Every engineering decision in Docs 2 and 3 traces back here. When you're mid-build and tempted to add a feature, come back to this doc first. If it doesn't serve a user story here, it doesn't get built yet.

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Market Context](#3-market-context)
4. [Target Users](#4-target-users)
5. [Product Vision](#5-product-vision)
6. [Feature Set — Phase 1 (Interview Coach)](#6-feature-set--phase-1)
7. [Feature Set — Phase 2 (General Platform)](#7-feature-set--phase-2-deferred)
8. [User Stories](#8-user-stories)
9. [Non-Goals](#9-non-goals)
10. [Success Metrics & KPIs](#10-success-metrics--kpis)
11. [Assumptions vs Decisions](#11-assumptions-vs-decisions)
12. [Risks](#12-risks)
13. [Monetization Strategy](#13-monetization-strategy)
14. [Competitive Differentiation](#14-competitive-differentiation)

---

## 1. Executive Summary

**SpeakPrep** is a real-time, voice-first AI mock interview coach. Users speak naturally; SpeakPrep responds conversationally — probing, pushing back, and scoring — in under 2 seconds. It covers the full interview lifecycle: resume intake, behavioral practice, technical walkthroughs, and system design sessions, with AI feedback that improves with every session.

SpeakPrep is **Phase 1** of a larger voice AI platform. The interview coach is the wedge — a high-urgency, high-retention use case that proves the core voice pipeline. The platform expands to general voice AI in Phase 2.

**Why interview coaching as the wedge:**
- High personal urgency (users are actively job-hunting — pain is immediate)
- Repeated usage need (multiple interview rounds, multiple companies)
- Measurable outcomes (did they get the job? did their scores improve?)
- Defensible against ChatGPT/Claude (those are chat products; we're a voice *coach*)
- Personal relevance: this is your own lived experience as a recent MS grad job hunting

---

## 2. Problem Statement

### The Primary Problem

Job seekers need realistic, conversational interview practice. But:

**Human mocks are inaccessible.** Professional coaching costs $150–$500/session. Peer mocks on Pramp/Exponent yield inconsistent quality — 30% of users report bad experiences. Family/friends can't replicate interviewer pressure.

**Current AI tools don't feel like real interviews.** Google Interview Warmup asks questions and waits. Final Round AI reads back bullet points. ChatGPT doesn't push back, probe for details, or simulate an interviewer who says "walk me through your algorithm choice." None of these products create the *social pressure* that makes real interviews hard.

**The prep journey is fragmented.** A typical job seeker uses 4–5 separate tools: LeetCode for coding ($35/month), Big Interview for behavioral ($39–$299/month), Glassdoor for company research (free), Interviewing.io for calibration ($225/session), ChatGPT for stories (ad hoc). No product covers the whole journey.

**Progress is invisible.** Users practice but don't know if they're improving. There's no score trend, no "you ramble on this topic," no "your STAR answers are missing Results 60% of the time."

### The Secondary Problem (Platform Vision)

Beyond interviews, voice interaction is fundamentally better than text for many AI use cases — language practice, presentation coaching, thinking out loud, real-time tutoring. Building the voice pipeline for SpeakPrep creates the infrastructure for these adjacent products.

---

## 3. Market Context

### Market Size

- AI recruitment market: **$596–706M in 2025**, growing at 6.8–7.5% CAGR
- Candidate-facing AI interview coaching segment: **$1.7B in 2025**, growing at **30.6% CAGR**
- 58% of job applicants now use AI tools during their search
- 93% of job seekers report interview anxiety as a significant barrier

### Competitive Landscape

| Competitor | Price | What They Do | Fatal Weakness |
|---|---|---|---|
| **Final Round AI** | $96–$148/mo | Live CoPilot during interviews, AI mock | Buggy, expensive, generic responses. Users report it "feels like a spell-checker, not a coach." |
| **Google Interview Warmup** | Free | 5 scripted questions, basic keyword feedback | No conversation, no follow-ups, no personalization. Completely static. |
| **Yoodli** | $10–$20/mo | Speech delivery coaching (pacing, fillers) | Coaches delivery only, not content. Won't tell you your STAR answer was weak. |
| **Hume AI** | API only | Voice AI infrastructure with emotional detection | Not a consumer product. Requires engineering to use. |
| **Interviewing.io** | $225+/session | Live mock with FAANG engineers | $1K+ for 5 sessions. Inaccessible to most job seekers. |
| **Pramp/Exponent** | Free–$79/mo | Peer-to-peer mocks | 30% bad peer experiences. No consistency. |
| **Big Interview** | $39–$299 | Video lessons + scripted question practice | Static, not conversational. AI feedback is generic. |

### The Gap SpeakPrep Fills

No competitor combines all four of:
1. **Real-time voice conversation** (not text, not scripted Q&A)
2. **Intelligent probing** (follow-up questions based on your actual answer)
3. **End-to-end coverage** (behavioral + technical + system design in one product)
4. **Progress tracking** (scores trend over time, specific improvement areas)

---

## 4. Target Users

### Primary User: "The Active Job Seeker" (Jane)

**Who she is:**
- Age 22–32, recent graduate or early-career professional (0–5 YOE)
- Actively applying for software engineering or data roles
- Has 3–8 interviews scheduled or expected in the next 4 weeks
- Has tried ChatGPT for practice but finds it too passive
- Can't afford $150/session human coaching

**Her pain:**
> "I know what I want to say but when I actually have to say it out loud in an interview my mind goes blank. I need to practice *speaking*, not just writing."

**What she needs:**
- A practice partner that pushes back like a real interviewer
- Specific feedback ("your Result was vague — what was the actual business impact?")
- Confidence from repetition before the real thing

**Session pattern:** 30–45 min/day, 3–5x per week, for 2–6 weeks before interviews.

---

### Secondary User: "The Career Switcher" (Marcus)

**Who he is:**
- Age 28–40, transitioning from non-technical background (finance, law, sales)
- Pursuing product management, data analytics, or SWE roles
- Less interview experience, more anxiety
- Values structured guidance over open-ended practice

**His pain:**
> "I don't even know what interviewers are looking for. I need someone to explain what a good answer sounds like, not just ask me questions."

**What he needs:**
- More educational scaffolding (explain what STAR means, show examples)
- Gentler difficulty progression
- Post-session written feedback to study

---

### Tertiary User: "The Non-Native Speaker" (Wei)

**Who he is:**
- International student or professional, strong technical skills
- English is second language — confident in writing, less confident speaking
- Particularly anxious about phone screens and verbal communication

**His pain:**
> "I answer technical questions fine but when they ask 'tell me about yourself' I freeze. I need to practice speaking English in an interview context specifically."

**What he needs:**
- Speaking pace and clarity feedback
- Pronunciation-aware scoring (not penalize accents, but flag pace/filler issues)
- Low-stakes environment to build spoken English confidence

---

## 5. Product Vision

### Phase 1 Product (SpeakPrep Interview Coach) — What We're Building Now

A web-based, voice-first AI mock interview platform where:

1. **User uploads resume + selects target role/company**
2. **Selects interview type:** Behavioral, Technical, System Design, Full Loop
3. **Speaks naturally** — SpeakPrep transcribes, understands, responds in real-time
4. **AI probes intelligently** — "Can you be more specific about what you personally contributed?" — not scripted follow-ups
5. **Scoring runs live and post-session** — content, structure, confidence markers, filler words
6. **Post-session report** — per-question breakdown, trends, specific improvement actions
7. **Progress tracked across sessions** — are you actually getting better?

### Phase 2 Product (General Voice AI Platform) — Deferred

Once the voice pipeline is proven and user base established:
- **Speaking coach** (presentations, speeches, public speaking practice)
- **Language learning** (conversational practice in target language)
- **Thinking out loud** (rubber duck debugging with a voice AI)
- **General assistant** (the full-breadth voice AI use case)

This platform expansion uses identical infrastructure. Only the prompting, session logic, and UI differ. This is the architectural decision that makes the general platform achievable: we build it right once.

---

## 6. Feature Set — Phase 1

### F-001: Onboarding & Resume Intake

**What it does:**
- User creates account (email/password or Google OAuth)
- Uploads resume (PDF) — extracted and stored as structured data
- Sets target: job title, target companies (optional), experience level
- Short calibration (3 questions to baseline current skill level)

**Why it matters:** Personalized interviews require knowing who the user is. A generic "Tell me about a time you showed leadership" becomes "You managed a team at ECS Tech in Kathmandu — walk me through a leadership challenge from that role" with resume context. That specificity is what no current tool has.

**Technical requirements:**
- PDF upload (max 5 MB) → PyMuPDF text extraction → LLM structured parsing
- Pydantic schema: name, experience[], education[], skills[], projects[]
- Stored in PostgreSQL JSONB column for flexible querying
- Extraction time target: < 10 seconds

---

### F-002: Session Setup

**What it does:**
- Choose interview type: Behavioral / Technical / System Design / Mixed
- Choose difficulty: Beginner / Intermediate / Advanced (or let AI calibrate)
- Choose interviewer persona: Friendly / Neutral / Challenging / Adversarial
- Choose duration: 15 min / 30 min / 45 min
- Optional: paste job description for company-specific tailoring

**Why it matters:** Difficulty and persona selection creates the "social pressure" simulation that no competitor offers. An adversarial interviewer who interrupts and pushes back is a fundamentally different experience than a friendly one — both are necessary preparation.

---

### F-003: Real-Time Voice Session

**What it does:**
- Push-to-talk or continuous voice input (user configurable)
- Real-time transcription displayed as user speaks (confidence signal)
- AI response in < 2 seconds end-to-end (speech → speech)
- AI voice: select from 4–6 natural-sounding voices (Kokoro TTS)
- Barge-in: user can interrupt AI mid-response
- Session timer visible, question counter visible
- Live filler word counter ("you've said 'um' 4 times this question")

**Technical requirements:**
- WebSocket connection maintained for full session duration
- Silero VAD for end-of-utterance detection
- Deepgram streaming ASR (primary), Faster-Whisper (fallback)
- Groq Llama 70B (primary LLM), Cerebras/Gemini Flash (fallback)
- Kokoro TTS for response audio
- All audio: 16 kHz mono PCM → 32 kbps Opus over WebSocket

---

### F-004: AI Interviewer Intelligence

**What it does:**

The AI doesn't just ask scripted questions. It:
- **Asks intelligent follow-ups** based on what you actually said ("You mentioned you 'worked on' the migration — were you the lead or a contributor?")
- **Probes for STAR components** when missing ("What was the actual outcome? Did it ship?")
- **Challenges weak answers** when in Challenging/Adversarial mode ("That sounds like what the team decided — what would you have done differently?")
- **Transitions naturally** between questions without breaking conversational flow
- **Tracks question coverage** — doesn't ask the same topic twice
- **Adapts difficulty** within session based on answer quality

**Why it matters:** This is the core product moat. Any competitor can ask "Tell me about a time you showed leadership." Only SpeakPrep asks "You said you 'helped coordinate' — can you tell me what you specifically did versus what others did? What was your decision authority?" That's what a real interviewer does.

---

### F-005: Live Scoring (during session)

**What it displays:**
- Filler word count per question (live ticker)
- Response time per question
- Current question score estimate (updates after each answer)
- Speaking pace indicator (WPM, target: 140–160)

**Why it matters:** Real-time feedback changes behavior immediately. Seeing "you've said 'um' 7 times" mid-question triggers self-correction in a way post-session feedback cannot.

---

### F-006: Post-Session Report

**What it contains:**
- Overall session score (0–100)
- Per-question scores across 5 dimensions:
  - Content Quality (30%) — relevance, depth, accuracy
  - Communication (25%) — clarity, structure, conciseness
  - STAR Compliance (20%) — all 4 components, specificity, results
  - Confidence Markers (15%) — assertive language, hedging frequency
  - Filler Words (10%) — rate per minute
- Written feedback per question: what you did well, what to improve, example of better answer
- Audio playback of your answer (optional, for self-review)
- Transcript of full session

**Why it matters:** The report is what users share, save, and reference. It's the "receipt" of their practice. Without a detailed report, sessions feel disposable.

---

### F-007: Progress Dashboard

**What it shows:**
- Score trend over time (line chart per dimension)
- Total practice time, total questions answered
- Strongest and weakest dimensions (rolling 30-day)
- Filler word frequency trend
- Response time trend
- "Your STAR compliance has improved 23% over the last 10 sessions"
- Question bank coverage: which topics have you practiced, which haven't you touched?

**Why it matters:** Progress visibility is the primary retention mechanism. Users who see improvement continue. Users who feel stuck without evidence quit. The dashboard converts single-session users to long-term users.

---

### F-008: Question Bank

**What it contains:**
- 500+ curated questions across categories:
  - Behavioral: Leadership, Teamwork, Conflict, Failure, Decision-Making, Motivation
  - Technical: Algorithms, Data Structures, System Concepts, Language-Specific
  - System Design: Common systems (URL shortener, rate limiter, chat system, etc.)
  - Company-Specific: Common patterns from Glassdoor/Blind for FAANG, startups
- Tagged by: difficulty, category, subcategory, company, role level
- User-contributed questions (Phase 1.5 — after initial launch)

**Adaptive selection:** Questions selected based on:
- User's skill gaps from previous sessions
- Target company/role context
- ELO-based difficulty targeting 60–75% expected success rate
- Coverage balance (don't over-index on one category)

---

### F-009: Authentication & User Accounts

**What it does:**
- Email/password registration with email verification
- Google OAuth (via Supabase Auth)
- JWT access tokens (15-min) + refresh tokens (7-day httpOnly cookies)
- Protected routes on frontend
- Account settings: email, password change, notification preferences
- Data export (GDPR compliance) and account deletion

---

### F-010: Rate Limiting & Usage Tiers

**Free Tier:**
- 3 sessions/week (15 min each)
- Basic post-session report (no audio playback, no full transcript)
- 7-day score history

**Pro Tier ($12/month):**
- Unlimited sessions
- Full post-session reports with audio playback
- 90-day score history with trend charts
- All interviewer personas and difficulty levels
- Company-specific question sets
- Resume-personalized questions

---

## 7. Feature Set — Phase 2 (Deferred)

These features are explicitly **NOT built in Phase 1**. Document them here so the architecture accommodates them without rework.

| Feature | Why Deferred | When to Build |
|---|---|---|
| Mobile app (iOS/Android) | Audio APIs on React Native are unreliable; 4–6 weeks of bugs | After web is stable with 100+ DAU |
| Voice cloning / custom voices | Kokoro doesn't support it; ElevenLabs costs money | Phase 2 premium feature |
| Multi-language support | ASR accuracy drops on non-English; LLM prompts need rewrite | Phase 2 after English is solid |
| Live interview CoPilot | Different product (listen to real interview, whisper answers) | Phase 2 — raises ethical questions too |
| Speaking coach mode | Same pipeline, different prompts | Phase 2 with existing infrastructure |
| General voice assistant mode | Same pipeline, different prompts | Phase 2 after core is proven |
| Team/enterprise accounts | B2B sales motion, different product | Phase 3 |
| Video analysis (body language) | Completely different tech stack (CV models) | Long-term |

---

## 8. User Stories

Organized by feature. Format: `US-[ID]: As a [user], I want to [action], so that [outcome].`

### Onboarding
- `US-001` As a new user, I want to upload my resume so that interview questions are personalized to my experience.
- `US-002` As a new user, I want to set my target role and company so that questions are calibrated to what I'm actually preparing for.
- `US-003` As a new user, I want a calibration session so that the AI doesn't start me too easy or too hard.

### Session
- `US-010` As a user, I want to press a button and speak naturally so that I can practice without typing.
- `US-011` As a user, I want to hear the AI respond in a natural voice within 2 seconds so that the conversation feels real.
- `US-012` As a user, I want the AI to ask intelligent follow-up questions so that it simulates a real interviewer, not a script.
- `US-013` As a user, I want to choose an adversarial interviewer persona so that I can practice high-pressure scenarios.
- `US-014` As a user, I want to interrupt the AI when it's talking so that I can correct myself or add information.
- `US-015` As a user, I want to see a live filler word counter so that I can self-correct in real time.
- `US-016` As a user, I want the AI to probe when I give a vague answer so that I'm forced to be specific.

### Scoring & Reports
- `US-020` As a user, I want a detailed post-session report so that I know exactly what to improve.
- `US-021` As a user, I want to replay my audio answers so that I can hear what the interviewer heard.
- `US-022` As a user, I want AI-written example better answers so that I know what "good" looks like.
- `US-023` As a user, I want per-dimension scores so that I can prioritize what to work on.

### Progress
- `US-030` As a user, I want a score trend chart so that I can see if I'm actually improving.
- `US-031` As a user, I want to see which topics I haven't practiced so that I don't have blind spots.
- `US-032` As a user, I want weekly email summaries so that I stay engaged even between sessions.

### Account
- `US-040` As a user, I want to sign in with Google so that I don't need another password.
- `US-041` As a user, I want to delete my account and all data so that my privacy is protected.

---

## 9. Non-Goals

**These things will NOT be built in Phase 1. Document them explicitly so you don't scope-creep:**

- ❌ Mobile app (iOS or Android)
- ❌ Live interview assistance (listening to a real interview and whispering answers)
- ❌ Video recording or video analysis
- ❌ Custom voice cloning
- ❌ Multi-language support (English only)
- ❌ Peer-to-peer matching
- ❌ Company-specific preparation packs beyond the question bank
- ❌ ATS resume scoring
- ❌ Coding environment (no code editor/execution)
- ❌ Integration with job boards or ATS systems
- ❌ Team/enterprise accounts
- ❌ Offline/on-device processing

---

## 10. Success Metrics & KPIs

### Phase 1 Launch Criteria (before calling it "launched")

- [ ] End-to-end voice latency < 2 seconds for 95% of turns
- [ ] ASR word error rate < 10% on clean English speech
- [ ] Session completion rate > 50% (user reaches end of planned session)
- [ ] Post-session report generated in < 30 seconds
- [ ] Zero data loss on session transcript
- [ ] Uptime > 99% over 7-day rolling window

### Product Health Metrics (post-launch, weekly tracking)

| Metric | Week 4 Target | Week 12 Target | Why It Matters |
|---|---|---|---|
| DAU | 10 | 50 | Core engagement signal |
| DAU/MAU | 15% | 20% | Retention quality |
| Sessions per user per week | 2 | 3 | Habit formation |
| Avg session length | 15 min | 20 min | Depth of engagement |
| D1 Retention | 20% | 25% | First impression quality |
| D7 Retention | 8% | 12% | Product stickiness |
| Free-to-Pro conversion | 1% | 4% | Monetization viability |
| NPS | - | > 30 | Word of mouth potential |
| Session completion rate | 55% | 70% | Product quality |

### Business Metrics (post-monetization)

- Monthly Recurring Revenue (MRR)
- Customer Acquisition Cost (CAC) — target < 3x monthly revenue
- Lifetime Value (LTV) — target > 6 months retention
- Churn rate — target < 8%/month

---

## 11. Assumptions vs. Decisions

This section is critical. It separates what we've *decided* from what we're *assuming to be true*. Assumptions must be validated and can change. Decisions are architectural commitments.

### ASSUMPTIONS (may change — validate as you build)

| Assumption | Risk if Wrong | How to Validate |
|---|---|---|
| Groq free tier remains usable at our scale | Groq throttles us → need paid plan | Monitor rate limit hits weekly |
| Oracle Cloud ARM capacity available in our region | Can't provision → delayed launch | Provision in 2 regions simultaneously |
| Kokoro TTS quality is sufficient for user retention | Users find voice robotic → use Cartesia | User interview, NPS survey after 50 sessions |
| Browser audio APIs are sufficient for voice capture | Mic quality too low for ASR | Test on Chrome/Firefox/Safari/Edge on Day 1 |
| Users prefer push-to-talk over always-on | Users find push-to-talk cumbersome | A/B test both in Phase 1 |
| English-only is acceptable for launch user base | International users churn → limit TAM | Survey first 100 users on language needs |
| 2-second end-to-end latency is acceptable | Users find it too slow → kills conversational feel | User test with explicit latency measurement |
| Resume parsing via LLM is accurate enough | Hallucinated resume data corrupts questions | Manual audit of first 50 parsed resumes |

### DECISIONS (architectural commitments — change requires a new ADR)

| Decision | Rationale | ADR Reference |
|---|---|---|
| WebSocket-based real-time architecture | Only option for bidirectional audio streaming | ADR-001 |
| Web-first (no mobile in Phase 1) | Mobile audio APIs add 4–6 weeks of bugs | ADR-002 |
| Hosted LLM providers (not self-hosted) | Self-hosted LLMs too slow on CPU for real-time voice | ADR-003 |
| Groq as primary LLM | Sub-100ms TTFT, free tier, OpenAI-compatible API | ADR-004 |
| Kokoro TTS (self-hosted) | Apache 2.0, CPU-capable, unlimited usage, 8.5/10 quality | ADR-005 |
| Deepgram for streaming ASR | Best latency, $200 free credit, real-time WebSocket native | ADR-006 |
| Supabase for auth + PostgreSQL | Bundles auth, saves weeks of work in Phase 1 | ADR-007 |
| Valkey for session cache | Open-source Redis fork, self-hosted on Oracle ARM | ADR-008 |
| Oracle Cloud ARM as compute | 24 GB RAM, always free, enough for entire stack | ADR-009 |
| Structured latency logging from Day 1 | Can't optimize what you can't measure | ADR-010 |

---

## 12. Risks

### Technical Risks

**R-001: Real-time latency target is hard to achieve.** Getting end-to-end < 2 seconds is genuinely difficult. It requires every pipeline stage to perform near-optimally. *Mitigation:* Instrument from Day 1. Have a latency budget per stage. Accept 3 seconds for Phase 1 launch, optimize to 2 seconds in Phase 1.5.

**R-002: ASR accuracy degrades in real conditions.** WER of 5% in benchmarks becomes 10–15% with background noise, accents, and technical vocabulary. *Mitigation:* Deepgram Nova-3 is the most robust streaming model. Add Whisper post-processing for technical terms.

**R-003: Oracle Cloud ARM availability.** Oracle may reclaim instances idle < 20% CPU or "Out of Capacity" on ARM provisioning. *Mitigation:* Upgrade to Pay-As-You-Go (free, just needs credit card) for better availability. Use keep-alive script to maintain CPU activity.

**R-004: Groq rate limits hit at scale.** Free tier is 30 RPM and 500K tokens/day per model. At 100 concurrent users, this runs out in minutes. *Mitigation:* Multi-provider fallback chain. Monitor rate limit hits. Budget $20/month for paid Groq when needed — much cheaper than OpenAI.

### Product Risks

**R-005: Product feels robotic, not like a real interviewer.** If the AI responses are generic, users won't return. *Mitigation:* Invest heavily in system prompt design. A/B test prompt variations. Get 10 real users to give honest feedback before calling it launched.

**R-006: Low retention.** Career tools have natural "positive churn" (user gets job, cancels). *Mitigation:* Build for referrals ("I used SpeakPrep and got the job — my friend is looking..."). Track cohort-based retention, not just raw numbers.

**R-007: High free-to-paid friction.** EdTech freemium conversion averages only 2.6%. *Mitigation:* Make free tier genuinely useful but leave meaningful value in Pro (full reports, audio playback, unlimited sessions). Don't cripple free tier to the point of being useless.

---

## 13. Monetization Strategy

### Pricing (Phase 1)

**Free Tier — "Try it"**
- 3 sessions/week, 15 minutes each
- Basic post-session score (overall + top-level dimensions)
- No audio playback, no full transcript
- 7-day history

**Pro — $12/month or $89/year (save 38%)**
- Unlimited sessions, up to 60 minutes each
- Full post-session reports (all 5 dimensions, per-question breakdown)
- Audio playback + full transcript
- 90-day progress history + trend charts
- All interviewer personas (including adversarial)
- Company-specific question sets
- Resume-personalized questions
- Priority support

### Why $12/month

- Below competitor range ($39–$148/month)
- Cheaper than one hour of human coaching ($150+)
- Comparable to a gym membership — users understand recurring fitness/skills investment
- Low enough to not require approval from a partner/parent
- High enough to be a real business at scale: 1,000 Pro users = $12,000 MRR

### Revenue Model Sustainability

At 1% free-to-paid conversion with 1,000 active free users: 10 paid users × $12 = $120 MRR.
At 4% conversion with 5,000 free users: 200 paid × $12 = $2,400 MRR.
At 4% conversion with 25,000 free users: 1,000 paid × $12 = $12,000 MRR (product-market fit territory).

**Variable cost per Pro user per month:**
- Deepgram ASR: ~$2 (unlimited sessions, avg 4 sessions/week × 30 min × $0.0077/min)
- Groq LLM: ~$0.50 (avg 200 turns × 500 tokens × $0.0008/1K tokens)
- Infrastructure: ~$0.01 (Oracle ARM is free; amortize domain/monitoring)
- **Total variable cost: ~$2.50/user/month**
- **Gross margin: ~79%** ✓

---

## 14. Competitive Differentiation

### Why SpeakPrep Wins (or at least earns its users)

| Dimension | SpeakPrep | ChatGPT/Claude | Yoodli | Final Round AI | Big Interview |
|---|---|---|---|---|---|
| Real-time voice conversation | ✅ | ❌ (text) | ✅ | ✅ | ❌ |
| Intelligent probing/follow-ups | ✅ | ❌ | ❌ | Partial | ❌ |
| Resume-personalized questions | ✅ | Manual setup | ❌ | ❌ | ❌ |
| Adaptive difficulty | ✅ | ❌ | ❌ | ❌ | ❌ |
| Progress tracking across sessions | ✅ | ❌ | Basic | ❌ | Basic |
| Detailed AI scoring rubric | ✅ | Variable | Speech only | ❌ | Generic |
| End-to-end interview coverage | ✅ | Ad hoc | Delivery only | Behavioral | Limited |
| Price | $12/mo | $20/mo (Plus) | $10–20/mo | $96–148/mo | $39–299 |

### The One-Sentence Differentiator

> "SpeakPrep is the only voice AI coach that asks intelligent follow-up questions, adapts difficulty to your skill level, and shows you exactly how you're improving over time — for less than the cost of one hour with a human coach."

---

*End of Document 1 — PRD + Product*
*Next: Document 2 — System Design + Architecture*
*Cross-reference: All feature IDs (F-001 through F-010) and user stories (US-001 through US-041) are referenced in Doc 2 and Doc 3.*

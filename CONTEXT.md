# CONTEXT.md — Agent Shared Memory
# Update this every time you finish a task or switch agents

## Project: SpeakPrep — Real-time Voice AI Mock Interview Coach
## Author: Abhiyan Sainju
## Started: April 2026
## Current Phase: 0 — Environment Setup
## Current Task: Initial repository setup

## Architecture Summary
- Backend: Python 3.12, FastAPI, asyncio, WebSockets
- ASR: Deepgram Nova-3 (primary), Faster-Whisper (fallback)
- LLM: Groq/Llama 3.3 70B (primary), Cerebras (fallback)
- TTS: Kokoro TTS self-hosted via Docker
- DB: Supabase PostgreSQL (Phase 1-2), self-hosted later
- Cache: Valkey (Redis-compatible)
- Infra: Oracle Cloud ARM, Docker Compose, Cloudflare Tunnel

## Docs Reference
- PRD: /docs/doc1-prd-product.md
- Architecture: /docs/doc2-system-design-architecture.md
- Build Guide: /docs/doc3-build-guide.md
- Portfolio: /docs/doc4-interview-portfolio.md

## What's Working
- [ ] Nothing yet — day 0

## What's In Progress
- [x] Repository setup

## What's Blocked
- Nothing

## Key Files
- Entry point: backend/app/main.py (not created yet)
- DB models: backend/app/models/ (not created yet)
- WebSocket handler: backend/app/api/ws.py (not created yet)

## DO NOT TOUCH
- Nothing locked yet

## Last Updated
- Date: 2026-04-25
- By: Abhiyan (setup session)

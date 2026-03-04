# LifeOS System Skills (v3.9 - v4.2)

This document contains the "Muscle Memory" of LifeOS—complex logic and autonomous capabilities built into the core.

---

## 🛠️ Autonomous Model Discovery & Sandbox (v3.9)
**Category**: Core Intelligence / Optimization
**Status**: ACTIVE & VERIFIED

### Description
The system can autonomously discover available Gemini models and run "Smoke Tests" (Sandbox heartbeats) to verify compatibility and quota availability before promotion.

### How to use
- **Discovery**: Automatically runs on system startup in a background thread.
- **Reporting**: Run `python model_report.py` in `backend-cortex` to see a Human-Readable compatibility report.
- **Approval**: New models are held in `pending_models` until the user/developer approves the shift in `model_registry.json`.

---

## 🛡️ Quota Resilience & Advanced Defense (v4.2)
**Category**: Core Stability
**Status**: ACTIVE & VERIFIED (2026-02-28)

### Description
A universal failover and backoff protocol that ensures LifeOS remains operational even during severe API congestion or quota exhaustion.

### How to use
- **Automatic**: Integrated into all `generate_content` and `embeddings` calls via `gemini.py`.
- **Tiered Failover**: Automatically cascades through `Smart (3.1)` -> `Fast (2.0)` -> `Emergency (2.5/Flash-Lite)`.
- **Exponential Backoff**: In case of 429 errors, the system adds jittered delays before retries to allow quota reset.

### Technical Logic
- Uses `safe_generate_content` as the primary entrance for text generation.
- Real-time API monitoring validates which models are actually available (verified: No 1.5 models).
- Embedding layer retry logic handles 429s in the RAG pipeline.

---

## 🚦 Smart Ingest Routing (v3.8)
**Category**: Data Management
**Status**: ACTIVE

### Description
Intelligently routes incoming data to `memories` or `documents` table based on origin.
- **Memories**: Captures from web terminal and chat are treated as personal diary entries.
- **Documents**: External files and formal ingestions are kept in the document index for RAG.

---

## 🧠 Two-Stage RAG & Recency Boost (v3.8)
**Category**: Retrieval
**Status**: ACTIVE

### Description
Uses a hybrid algorithm of Semantic Similarity (Embeddings) + Temporal Weighting (Recency) to ensure "Today's context" is prioritized in answers.

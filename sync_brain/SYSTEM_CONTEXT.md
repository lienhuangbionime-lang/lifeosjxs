# [ROLE: DEVELOPMENT CONSTITUTION]
# [FOR: Development AIs & Architects]

# LifeOS v4.0 - System Context (AI Truth Source)

> **Purpose**: This document serves as the **Single Source of Truth** for all AI assistants working on LifeOS. Read this FIRST before generating any code.

---

## 🎯 Project Identity
- **Name**: LifeOS v4.0 "Cortex"
- **Philosophy**: Autopoietic OS - Self-Sensing, Memory-Driven, Proactive Action.
- **Architecture**: Windowed Symbiosis (Body, Cortex, Hippocampus, Brain).
- **Status**: v4.0 Agentic DNA Migration | Autonomous Model Discovery.

---

## 🛠️ Autonomous Intelligence (v3.9 - v4.0)

### 1. Ground Truth Discovery
LifeOS uses an **Autonomous Discovery & Sandbox** loop. The system must verify its own environment (models, database state) and report its health via `model_report.py`.

### 2. Radical Transparency
All AI reasoning—plans (`task.md`), skills (`SKILLS.md`), and historical records (`history/`)—must be permanently mirrored in `sync_brain/` to ensure continuity.

### 3. Skill-Based Evolution
New capabilities are added as documented **Skills**. Future AI instances must inherit these skills by reading `sync_brain/SKILLS.md` before execution.

---

## 🏗️ Technical Stack & Constraints

### 1. Backend (The Cortex)
- **Framework**: FastAPI (Python 3.13+)
- **SDK**: `google.genai` (v1 SDK). Use `app.core.gemini.get_model()` factory.
- **Database**: Supabase (Postgres) via `app.core.database`.
- **Vector**: 3072 dimensions (`text-embedding-004`).
- **Dependencies**: Managed via `uv`. Always check `requirements.txt`.

### 2. Frontend (The Body)
- **Framework**: Next.js 15 (App Router).
- **Styling**: Tailwind CSS (Utility-First) for UI generation. Maintain Dark mode default.
- **State**: React Hooks + localStorage + API Sync.
- **Animation**: Framer Motion | **Icons**: Lucide React.

---

## 🚦 Forbidden Practices (The "Fatal Errors" List)

### ❌ Code & System
- **Emojis**: NEVER use emojis in Python `print()` statements (Windows cp950 encoding crashes).
- **Hardcoding**: NEVER hardcode model IDs. Use `app.core.gemini.get_model()`.
- **SDK**: NEVER use legacy `google.generativeai`.
- **Table Names**: NEVER use `LogEntry` (Correct: `memories`).
- **Git**: NEVER commit directly to `main`. Suggest `feat/` or `fix/` branches.
- **Proxy**: NEVER use `localhost` in Next.js rewrites or local API calls (Windows IPv6 hang). ALWAYS use `127.0.0.1`.

### ✅ Required Practices
- **Validation**: ALWAYS use Pydantic models (v2) for data validation.
- **Async**: ALWAYS use async/await for AI model calls and I/O.
- **Next.js 15**: ALWAYS await `context.params` in API route handlers; it is a Promise.
- **CORS**: ALWAYS explicitly list custom headers (`X-Supabase-URL` etc.) in `main.py` `CORSMiddleware` `allow_headers`.
- **Tracing**: ALWAYS log AI decision paths to `cortex_growth_logs`.
- **Exactness**: ALWAYS use regex post-processing to force-inject user-supplied exact values into LLM output.
- **Resilient Inserts**: ALWAYS use the `safe_write()` wrapper from `app.core.database` for inserting, updating, or upserting into Supabase. NEVER use raw `db.table().insert()` directly. This protects background tasks from crashing due to `PGRST204` (missing column) Schema Drift errors.

---

## 📁 Key File Map

| Path | Purpose |
| :--- | :--- |
| `sync_brain/registry.json` | Database ground truth (Genetic Blueprint). |
| `sync_brain/task.md` | Real-time progress and mission tracking. |
| `sync_brain/SKILLS.md` | Documentation of systemic abilities. |
| `sync_brain/history/` | Atomic records of execution & walkthroughs. |
| `backend-cortex/app/api/v1/` | Cortex API routers. |
| `backend-cortex/skills/` | Dynamic skill protocols (`SKILL.md`). |

---

## 🛑 Critical Safeguards (v4.0)
- **Model Discovery**: Rely on `ModelDiscoveryService` for active model IDs.
- **Model Sanitization**: Always use `sanitize_model_name()` before initialization.
- **Quota Fallback**: Chain-fallback from `Pro` to `Flash Lite` upon 429 error.

---
**Last Updated**: 2026-03-05 | **Status**: v4.0 Agentic DNA Installation (Guest Mode Enabled)

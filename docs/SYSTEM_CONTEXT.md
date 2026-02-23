# LifeOS v3.5 - System Context (AI Truth Source)

> **Purpose**: This document serves as the **Single Source of Truth** for all AI assistants working on LifeOS. Read this FIRST before generating any code.

---

## 🎯 Project Identity & Version Matrix

**Development Framework**: **v3.5** (The Codebase/Skeleton)
**Cortex System**: **v3.2** (The Logic/Soul)
**Journal Protocol**: **v7.1** (The Ingest Engine)

**Philosophy**: Personal Operating System for Life Management  
**Architecture**: Symbiotic AI + Human Intelligence  
**Status**: Production-ready with active schema evolution

---

## ⚠️ CRITICAL ENVIRONMENT CONSTRAINTS (HARD TRUTHS)
> **Mandatory for all AI Operatives**: Failure to follow these specific identifiers will result in system-wide 404/500 errors.

### 1. Gemini Model Identifiers (CRITICAL)
This environment/SDK version requires these **EXACT** identifiers. Do NOT guess. v1 API 不支援 `gemini-1.5-flash` 或帶有 `models/` 前綴的字串 (會返回 404)。
- **Primary Smart Model**: `gemini-3-pro-preview` (Deep Thinking/Review)
- **Primary Fast Model**: `gemini-flash-lite-latest` (Ingest/Basic Chat)
- **Embedding Model**: `text-embedding-004` (Dimension: 3072)
- **Audio Model**: `gemini-2.5-flash-native-audio` (極低延遲)
- **Rule**: ALWAYS pass model strings through `app.core.gemini.sanitize_model_name()` before use.

### 2. CodeSpeak Paradigm (CRITICAL)
系統與 AI 的對話必須「**零冗言贅字、高訊號、直接指令**」。嚴禁在 Prompt 內使用安撫或祈使語氣。所有的系統維護、同步腳本均在 `tools/` 目錄。
- 系統 AI = `backend-cortex/app/` (服務使用者)
- 開發 AI = `sync_brain/` & `tools/` (你的位置，負責系統拓展)

### 3. Runtime Requirements
- **Node.js**: MUST be installed and in path for `frontend-body`.
- **Pydantic**: Project uses V2. Use `model_dump()`, NOT `dict()`.
- **Port 8000**: Exclusively for Backend.
- **Port 3000**: Exclusively for Frontend.

### 4. Database Mappings
- **Core Memory Table**: `memories` (NOT `LogEntry`).
- **Graph Table**: `nodes` and `edges`.

---

## 🏗️ Tech Stack (Mandatory)

### Backend
- **Framework**: FastAPI (Python 3.13+)
- **Database**: Supabase (PostgreSQL)
- **AI**: Google Gemini 2.5 Flash (via `google-genai` SDK)
- **Vector Search**: pgvector extension
- **Schema**: Pydantic v2 (strict typing required)

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Vanilla CSS (NO Tailwind unless explicitly requested)
- **State**: React Hooks + localStorage
- **Animation**: Framer Motion
- **Icons**: Lucide React

### Infrastructure
- **Local Storage**: C Kernel (binary, optional)
- **Cloud Storage**: Supabase
- **Deployment**: Vercel (frontend) + Self-hosted (backend)

---

## 📐 Architectural Principles

### 1. Dual-Write Strategy
```
User Input → AI Analysis → Dual Write
                          ├─ Supabase (cloud, working copy)
                          └─ C Kernel (local, digital original)
```

**Rule**: NEVER write to only one system. Always attempt both, log failures gracefully.

### 2. Schema Evolution Protocol
```
User Request → AI Analysis → Generate Options → User Approval → Execute → Log
```

**Rule**: NEVER modify database schema without:
1. Reading `schemas/registry.json`
2. Generating migration script
3. Updating `evolution_log.json`
4. User confirmation

### 3. AI-First Design
```
Raw Input → Gemini Analysis → Structured Output → Storage
```

**Rule**: All user input goes through AI analysis (SorterAgent) before storage.

## 🗄️ Supabase Schema (AI RAG Focus)
**Rule**: The database is built for AI extraction speed and semantic search, not rigid normalization.

### Core Tables
1. `memories`: The absolute core. Every log, concept, and chat goes here.
   - Requires `content` (pure text signal) and `embedding` (vector(3072)).
   - Expand metadata via the `metadata` JSONB column instead of `ALTER TABLE`.
   - `local_path` is required for Local-First syncing.
2. `edges`: The Neural Graph.
   - Maps `source_id` to `target_id` with a `relation_type` and `weight`.
3. `monthly_review`: Asynchronous AI insights over memory aggregations.

### RAG Operations
- `match_memories` RPC: Uses `query_embedding` (vector(3072)). Called primarily in `chat.py`. 

---

## 🚫 Forbidden Practices

### Code Style
- ❌ **NEVER** use emojis in Python `print()` statements (Windows encoding issues)
- ❌ **NEVER** use Tailwind CSS without explicit user request
- ❌ **NEVER** modify core tables (`memories`, `projects`, `tasks`) without migration
- ❌ **NEVER** use `google.generativeai` (deprecated, use `google.genai`)
- ❌ **NEVER** hardcode API keys or credentials

### Database
- ❌ **NEVER** use `DROP TABLE` without backup
- ❌ **NEVER** add columns without DEFAULT values
- ❌ **NEVER** query without error handling
- ❌ **NEVER** use table name `LogEntry` (correct: `memories`)

### API Design
- ❌ **NEVER** return 500 errors without logging
- ❌ **NEVER** expose internal errors to frontend
- ❌ **NEVER** skip input validation

---

## ✅ Required Practices

### Code Style
- ✅ **ALWAYS** use `[OK]`, `[WARN]`, `[ERROR]` instead of emojis in logs
- ✅ **ALWAYS** use Pydantic models for data validation
- ✅ **ALWAYS** use async/await for I/O operations
- ✅ **ALWAYS** include type hints in Python
- ✅ **ALWAYS** use strict TypeScript

### Database
- ✅ **ALWAYS** read `schemas/registry.json` before schema changes
- ✅ **ALWAYS** generate migration scripts in `migrations/`
- ✅ **ALWAYS** update `evolution_log.json` after changes
- ✅ **ALWAYS** use transactions for multi-step operations

### Error Handling
- ✅ **ALWAYS** wrap Supabase calls in try-except
- ✅ **ALWAYS** provide fallback for C Kernel failures
- ✅ **ALWAYS** log errors with context
- ✅ **ALWAYS** return user-friendly error messages

---

## 📁 Project Structure

```
lifeosjxs/
├── backend-cortex/          # FastAPI backend
│   ├── app/
│   │   ├── agents/          # AI agents (SorterAgent, ThinkerAgent)
│   │   ├── api/v1/          # API routes
│   │   ├── core/            # Core services (database, gemini)
│   │   └── models/          # Pydantic schemas
│   ├── routers/             # FastAPI routers
│   ├── schemas/             # Schema registry (AI-readable)
│   ├── tools/               # Schema evolution tools
│   ├── migrations/          # SQL migration scripts
│   └── main.py              # Entry point
├── frontend-body/           # Next.js frontend
│   ├── app/                 # App router pages
│   ├── components/          # React components
│   ├── lib/                 # Utilities
│   │   ├── ai/              # AI core engine
│   │   └── api/             # API client
│   └── public/              # Static assets
└── docs/                    # Documentation (AI-readable)
    ├── SYSTEM_CONTEXT.md    # This file
    ├── AI_SCHEMA_EVOLUTION_PROTOCOL.md
    ├── DATABASE_EVOLUTION_GUIDE.md
    └── SYSTEM_PROTOCOLS.md
```

---

## 🔑 Key Files (Must Read Before Editing)

### Backend
- **`schemas/registry.json`** - Database schema definition (AI-readable)
- **`schemas/evolution_log.json`** - Schema change history
- **`routers/ingest_dual.py`** - Main ingestion logic
- **`app/agents/sorter.py`** - AI analysis agent
- **`kernel_driver.py`** - C Kernel interface

### Frontend
- **`lib/api/client.ts`** - API client (cortex object)
- **`components/CaptureView.tsx`** - Main input interface
- **`components/NeuralGraph.tsx`** - Brain visualization
- **`lib/ai/core.ts`** - Core engine (graph parsing)

### Documentation
- **`docs/SYSTEM_PROTOCOLS.md`** - System design principles
- **`docs/AI_SCHEMA_USAGE_GUIDE.md`** - How to request schema changes

---

## 🎨 Design Patterns

### 1. API Response Format
```typescript
interface IngestResponse {
  status: "analyzed" | "synced" | "failed";
  message: string;
  model?: string;
  db_id?: string;
  kernel_locked?: boolean;
  data?: {
    markdown_body: string;
    meta: {
      metrics: { mood: number; focus: number; energy: number };
      tags: string[];
      category: string;
      date?: string;
    };
    tasks: Task[];
  };
}
```

### 2. Pydantic Model Pattern
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class LogEntry(BaseModel):
    content: str
    mood: int = Field(default=5, ge=0, le=10)
    focus: int = Field(default=5, ge=0, le=10)
    energy: int = Field(default=5, ge=0, le=10)
    tags: List[str] = []
    category: str = "Life"
    date: Optional[str] = None
```

### 3. Error Handling Pattern
```python
try:
    result = supabase.table("memories").insert(data).execute()
    db_id = result.data[0]['id'] if result.data else None
    print(f"[OK] Supabase: Saved to DB (ID: {db_id})")
except Exception as e:
    print(f"[WARN] Supabase write failed: {e}")
    db_id = None
```

---

## 🧠 AI Agent Protocols

### SorterAgent (Daily Log Analysis)
**Input**: Raw user text  
**Output**: Structured LogEntry with:
- Markdown-formatted content
- Extracted metrics (mood, focus, energy)
- Detected tags (#tag)
- Detected date (YYYY-MM-DD)
- Category classification

**Prompt Location**: `backend-cortex/prompts/system_daily.md`

**Key Behavior**:
- Returns Markdown (NOT JSON)
- Appends JSON metadata block at end
- Extracts date from text if present
- Defaults to current date if not found

### ThinkerAgent (Deep Analysis)
**Status**: Planned (not yet implemented)  
**Purpose**: Long-form reflection and insight generation

---

## 🗄️ Database Schema (Core Tables)

### memories
```sql
CREATE TABLE public.memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Metrics (0-10)
  mood INT DEFAULT 5 CHECK (mood >= 0 AND mood <= 10),
  focus INT DEFAULT 5 CHECK (focus >= 0 AND focus <= 10),
  energy INT DEFAULT 5 CHECK (energy >= 0 AND energy <= 10),
  
  -- AI Metadata
  tags TEXT[] DEFAULT '{}',
  category TEXT DEFAULT 'Life',
  is_ai BOOLEAN DEFAULT FALSE,
  ai_model TEXT,
  
  -- Vector search
  embedding VECTOR(768)
);
```

**Indexes**: date (DESC), tags (GIN), created_at (DESC)

### projects, tasks, nodes, edges
See `schemas/registry.json` for complete definitions.

---

## 🔄 Workflow Examples

### Example 1: User Saves Diary Entry
```
1. User types in CaptureView
2. Clicks "INGEST & ANALYZE"
   → Frontend calls cortex.ingest.submit({ text, skip_ai: false })
   → Backend: SorterAgent.process(text)
   → Returns analyzed markdown + metadata
3. User clicks "SAVE TO BRAIN"
   → Frontend calls cortex.ingest.submit({ text: analyzed, skip_ai: true, date })
   → Backend: ingest_log() writes to Supabase + C Kernel
   → Returns status: "synced" | "db_only" | "kernel_only" | "failed"
4. Frontend updates local state
5. User switches to Brain view
   → Frontend calls cortex.getRecentMemories(50)
   → Backend queries Supabase memories table
   → Returns array of LogEntry objects
3. NeuralGraph renders force-directed graph
```

### Example 2: User Requests New Metric
```
1. User: "我想追蹤睡眠品質"
2. AI reads schemas/registry.json
3. AI analyzes: "simple_numeric" type
4. AI generates 2 options:
   A. JSONB metadata (fast)
   B. New column (optimized)
5. User chooses A
6. AI updates:
   - SorterAgent prompt (recognize sleep_quality)
   - API schema (accept sleep_quality in metadata)
   - Frontend input (optional sleep quality field)
7. AI logs to evolution_log.json
8. After 30 days, AI suggests promoting to column
```

---

## 🐛 Common Pitfalls & Solutions

### Issue 1: 500 Error on Ingest
**Cause**: Emoji in print() causing UnicodeEncodeError on Windows  
**Solution**: Use `[OK]`, `[WARN]`, `[ERROR]` instead  
**Files**: `ingest_dual.py`, `sorter.py`, `kernel_driver.py`

### Issue 2: Empty Memories List
**Cause**: Table name mismatch (`LogEntry` vs `memories`)  
**Solution**: Always use `memories` table  
**Files**: `app/api/v1/memories.py`

### Issue 3: Table Not Found
**Cause**: Supabase schema not initialized  
**Solution**: Run `infra/supabase_reset_and_init.sql`  
**Location**: Supabase Dashboard → SQL Editor

### Issue 4: Date Not Detected
**Cause**: SorterAgent regex not matching format  
**Solution**: Check `sorter.py` line 95, ensure format is `YYYY-MM-DD`  
**Fallback**: Uses current date if not found

---

## 🚀 Development Workflow

### Starting Backend
```bash
cd backend-cortex
python main.py
# Runs on http://0.0.0.0:8000
```

### Starting Frontend
```bash
cd frontend-body
npm run dev
# Runs on http://localhost:3000
```

### Environment Variables Required
```bash
# Backend (.env)
GOOGLE_API_KEY=xxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx

# Frontend (.env.local)
NEXT_PUBLIC_PYTHON_API_URL=http://127.0.0.1:8000
```

---

## 📝 When Generating Code

### Before Writing ANY Code:
1. ✅ Read this file (SYSTEM_CONTEXT.md)
2. ✅ Check `schemas/registry.json` if touching database
3. ✅ Review relevant files in "Key Files" section
4. ✅ Verify tech stack matches requirements
5. ✅ Check "Forbidden Practices" list

### When Modifying Schema:
1. ✅ Read `schemas/registry.json`
2. ✅ Use `tools/schema_assistant.py` to analyze
3. ✅ Generate migration script
4. ✅ Update `evolution_log.json`
5. ✅ Get user approval before executing

### When Adding Features:
1. ✅ Check if similar feature exists
2. ✅ Follow existing patterns
3. ✅ Update relevant documentation
4. ✅ Add error handling
5. ✅ Test both success and failure cases

---

## 🎯 Success Criteria

Code is considered **production-ready** when:
- ✅ Follows all "Required Practices"
- ✅ Avoids all "Forbidden Practices"
- ✅ Has proper error handling
- ✅ Includes type hints/types
- ✅ Updates relevant documentation
- ✅ Passes manual testing
- ✅ Logs important events
- ✅ Handles edge cases gracefully

---

## 🔮 Future Vision

### Phase 1 (Current): Stable Foundation
- ✅ Dual-write strategy
- ✅ AI-driven analysis
- ✅ Schema evolution protocol

### Phase 2 (Next): Intelligence Layer
- 🔄 Semantic search with embeddings
- 🔄 Automated insights generation
- 🔄 Project-memory linking

### Phase 3 (Future): Autonomous System
- 📋 Self-optimizing schema
- 📋 Predictive task generation
- 📋 Cross-memory pattern detection

---

## 📞 When in Doubt

1. **Read this file again**
2. **Check `schemas/registry.json`**
3. **Review `docs/SYSTEM_PROTOCOLS.md`**
4. **Ask user for clarification**
5. **Never guess or assume**

---

**Last Updated**: 2026-02-11T03:29:17+08:00  
**Version**: 3.5  
**Maintained By**: AI + Human Collaboration

---

> "This is not just a codebase. This is a living system that evolves with its user."

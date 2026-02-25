# LifeOS v3.6 - System Context (AI Truth Source)

> **Purpose**: This document serves as the **Single Source of Truth** for all AI assistants working on LifeOS. Read this FIRST before generating any code.

---

## 🎯 Project Identity

**Name**: LifeOS v3.6  
**Philosophy**: Personal Operating System for Life Management  
**Architecture**: Symbiotic AI + Human Intelligence + Self-Reflection  
**Status**: Production-ready with Autonomous Growth Engine (v3.6.3)

---

## 🏗️ Tech Stack (Mandatory)

### Backend
- **Framework**: FastAPI (Python 3.13+)
- **Database**: Supabase (PostgreSQL)
- **AI**: Gemini 3 Pro (Smart) & Gemini Flash Lite (Fast)
- **SDK**: `google-generativeai` (Legacy wrapper, required for current implementation)
- **Vector Search**: pgvector (3072 dimensions)
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

---

## 🚫 Forbidden Practices

### Code Style
- ❌ **NEVER** use emojis in Python `print()` statements (Windows encoding issues)
- ❌ **NEVER** use Tailwind CSS without explicit user request
- ❌ **NEVER** modify core tables (`memories`, `projects`, `tasks`) without migration
- ❌ **NEVER** use identifiers like `gemini-3.0` or `gemini-2.5` (use `sanitize_model_name()` logic)
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

### Code Style
- ✅ **ALWAYS** use `[OK]`, `[WARN]`, `[ERROR]` instead of emojis in logs
- ✅ **ALWAYS** use Pydantic models for data validation
- ✅ **ALWAYS** use async/await for I/O operations
- ✅ **ALWAYS** include type hints in Python

### AI Input Processing
- ✅ **ALWAYS** treat LLM JSON output as untrustworthy for exact values (e.g. Dates, User Manual Scores).
- ✅ **ALWAYS** use Python regex post-processing to force-inject user-supplied exact values into the LLM's generated markdown or metadata. Never rely solely on system prompt instructions for data exactness.
- ✅ **ALWAYS** use strict TypeScript
- ✅ **ALWAYS** use async/await for ALL AI model calls to prevent event loop blocking (v3.6.3 Requirement).
- ✅ **ALWAYS** log AI decision paths to `cortex_growth_logs` for evolution analysis.

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

lifeosjxs/
├── backend-cortex/          # FastAPI backend
│   ├── app/
│   │   ├── agents/          # AI agents (SorterAgent)
│   │   ├── api/v1/          # API routes (crystallize, subconscious, etc)
│   │   ├── core/            # Core services (database, gemini, vector)
│   │   ├── models/          # Pydantic schemas
│   │   ├── services/        # Service logic (rag, subconscious, embedder)
│   │   └── subconscious/    # APScheduler Background Workers
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

### ThinkerAgent / Subconscious Engine
**Status**: Partially Implemented (`services/subconscious.py`)  
**Purpose**: Long-form reflection and insight generation. Runs via APScheduler every 12 hours or via manual API trigger to synthesize recent memories.

### Crystallize Engine
**Status**: Implemented (`api/v1/crystallize.py`)
**Purpose**: Context-Aware generation. Reads the last 48h of memory logs and feeds them into Gemini Flash to provide dynamic Capture UI prompts.

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
  
  -- Vector search (Full Precision Protocol)
  embedding VECTOR(3072)
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
6. NeuralGraph renders force-directed graph
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

### Phase 2 (Current): Intelligence Layer
- ✅ Semantic search with embeddings (`services/rag.py` and `vector.py`)
- ✅ Automated insights generation (`services/subconscious.py`)
- ✅ Context-Aware UI prompts (`api/v1/crystallize.py`)
- 🔄 Project-memory linking

### Phase 3 (Current): Knowledge Crystallization
- ✅ Knowledge Crystallization Engine (`services/crystallizer.py`)
- ✅ Bulk historical processing script (`tools/bulk_crystallize.py`)
- ✅ AI-generated Brain Insights in ContextModal
- ✅ Standardized Gemini model registry via `get_model()`

### Phase 4 (Future): Autonomous System
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

**Last Updated**: 2026-02-25T22:25:00+08:00  
**Version**: 3.6.3 (Autonomous Reflection & Project Synthesis)  
**Maintained By**: AI + Human Collaboration

---

## 🛑 Critical Safeguards (v3.5.1)

### 1. Model Name Sanitization
The system is sensitive to Gemini model versioning. **Always use `app.core.gemini.sanitize_model_name()`** before initializing models to prevent 404 errors. Verified IDs:
- `models/gemini-3-pro-preview` (Smart)
- `models/gemini-flash-lite-latest` (Fast/Reliable)

### 4. Service Imports
Always import functions like `generate_embedding` individually from `app.services.embedder`. Do NOT attempt to import an `embedder` object as it does not exist in the current service architecture.

### 2. Multi-tier Quota Fallback
If the Smart model reaches quota (429), `chat.py` automatically chain-falls back to `Flash Lite` to ensure continuity.

### 3. RAG Robustness
Retrieval in `rag.py` uses **Hybrid Fallback**:
1. If Vector search (3072 dims) returns nothing, keyword/date matching is triggered.
2. System Prompt is strictly tuned to prevent hallucinations when data is missing.

---

> "This is not just a codebase. This is a living system that evolves with its user."

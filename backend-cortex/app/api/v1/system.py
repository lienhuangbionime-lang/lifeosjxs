# app/api/v1/system.py
from fastapi import APIRouter, HTTPException
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from app.core.gemini import get_model
from app.models.schemas import (
    SystemStatusResponse, 
    UpgradeResponse, 
    PromptRequest, 
    PromptResponse
)


router = APIRouter()
logger = logging.getLogger("app.api.v1.system")


@router.get("/status")
async def get_system_status():
    """
    [v5.4] Return system status including active model and quota state from registry.
    """
    try:
        from app.services.model_discovery import model_discovery

        # Get current active models from dynamic registry
        fast = get_model("fast")
        smart = get_model("smart")
        current_model = fast.get("model", "unknown")

        # [v5.7] Defensive Registry Access
        verified = getattr(model_discovery, "verified_models", {})
        exhausted = getattr(model_discovery, "quota_exhausted", {})

        # Ensure they are dicts to prevent AttributeErrors on .get()
        if not isinstance(verified, dict): verified = {"fast": [], "smart": []}
        if not isinstance(exhausted, dict): exhausted = {"fast": [], "smart": []}

        available_fast = verified.get("fast", [])
        available_smart = verified.get("smart", [])
        exhausted_fast = exhausted.get("fast", [])
        exhausted_smart = exhausted.get("smart", [])
        last_probe = model_discovery.last_discovery or "Unknown"

        # Daily usage count from DB
        try:
            from app.core.usage import get_daily_usage
            usage = await get_daily_usage()
            daily_requests = usage.get("request_count", 0)
        except Exception:
            daily_requests = 0

        # Build human-readable quota summary
        n_available = len(available_fast) + len(available_smart)
        n_exhausted = len(exhausted_fast) + len(exhausted_smart)

        if n_available > 0:
            quota_summary = f"{n_available} model(s) with quota, {n_exhausted} exhausted"
        else:
            quota_summary = f"All models quota exhausted ({n_exhausted} checked). Reset pending."

        return {
            "status": "ok" if n_available > 0 else "degraded",
            "current_model": current_model,
            "active_fast_model": available_fast[0] if available_fast else None,
            "active_smart_model": available_smart[0] if available_smart else None,
            "model_versions": available_fast + available_smart,
            "quota_status": {
                "available": {
                    "fast": available_fast,
                    "smart": available_smart
                },
                "exhausted": {
                    "fast": exhausted_fast,
                    "smart": exhausted_smart
                },
                "last_probe": last_probe,
                "daily_api_requests": daily_requests
            },
            "remaining_requests": quota_summary,
            "note": "Run python tools/quota_probe.py to refresh quota status."
        }
    except Exception as e:
        logger.exception("Failed to get system status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


@router.get("/hippocampus/health")
async def get_hippocampus_health():
    """
    [v6.0] Perform a real-time structural health check of the cloud database
    relative to the local static blueprint.
    """
    from app.agents.hippocampus_agent import hippocampus_agent
    try:
        health = await hippocampus_agent.check_health()
        return health
    except Exception as e:
        logger.error(f"Hippocampus health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upgrade", response_model=UpgradeResponse)
async def trigger_upgrade():
    """
    Simulate an upgrade/evolution trigger.
    """
    try:
        logger.info("Evolution triggered via /api/v1/system/upgrade")
        return UpgradeResponse(success=True, message="Evolution triggered (simulated).")
    except Exception as e:
        logger.exception("Upgrade trigger failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to trigger upgrade")


@router.get("/prompts/{name}", response_model=PromptResponse)
async def get_prompt(name: str):
    """
    Retrieve a system prompt by name.
    """
    import os
    from pathlib import Path
    
    prompt_dir = Path(__file__).parent.parent.parent.parent / "prompts"
    file_path = prompt_dir / f"{name}.md"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")
    
    try:
        content = file_path.read_text(encoding="utf-8")
        mtime = os.path.getmtime(file_path)
        last_modified = datetime.fromtimestamp(mtime).isoformat()
        
        return PromptResponse(name=name, content=content, last_modified=last_modified)
    except Exception as e:
        logger.error(f"Error reading prompt {name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read prompt")


from app.models.schemas import PromptRequest
@router.post("/prompts/{name}", response_model=PromptResponse)
async def update_prompt(name: str, request: PromptRequest):
    """
    Update a system prompt.
    """
    import os
    from pathlib import Path
    
    prompt_dir = Path(__file__).parent.parent.parent.parent / "prompts"
    file_path = prompt_dir / f"{name}.md"
    
    # Check if directory exists, if not create it (safety)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        file_path.write_text(request.content, encoding="utf-8")
        mtime = os.path.getmtime(file_path)
        last_modified = datetime.fromtimestamp(mtime).isoformat()
        
        logger.info(f"Prompt '{name}' updated via API.")
        return PromptResponse(name=name, content=request.content, last_modified=last_modified)
    except Exception as e:
        logger.error(f"Error updating prompt {name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update prompt")


# ============================================================================
# [NEW] One-Click Supabase Setup ??runs full LifeOS schema on user's DB
# ============================================================================
from fastapi import Request
from pydantic import BaseModel as _BaseModel

LIFEOS_SETUP_SQL = """
-- LifeOS v3.8.1 Unified Schema Setup (High-Signal Baseline)
-- ?ö® Initial setup requires the 'exec' RPC function in Supabase.

-- 0. Extensions
create extension if not exists vector;

-- 1. Memories (?•Ë??áÊ†∏ÂøÉË???- Forensic Enabled)
create table if not exists public.memories (
  id uuid default gen_random_uuid() primary key,
  content text not null,
  date date not null default current_date,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  mood int default 5,
  focus int default 5,
  energy int default 5,
  tags text[] default '{}',
  category text default 'Life',
  is_ai boolean default false,
  ai_model text,
  local_path text,
  content_hash text,
  ai_insights text,
  embedding vector(3072)
);
create index if not exists idx_memories_date on public.memories(date);
create index if not exists idx_memories_tags on public.memories using gin(tags);

-- 2. Documents (?•Ë??áÊ??ªÈ??¢Â±§)
create table if not exists public.documents (
  id uuid default gen_random_uuid() primary key,
  title text,
  url text unique,
  content text not null,
  doc_type text default 'webpage',
  tags text[] default '{}',
  metadata jsonb default '{}',
  embedding vector(3072),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_documents_url on public.documents(url);

-- 3. Projects (Â∞àÊ?ÁÆ°Á?)
create table if not exists public.projects (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  status text default 'active',
  progress int default 0,
  start_date date,
  due_date date,
  parent_id uuid references public.projects(id),
  meta jsonb default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 4. Tasks (Ë°åÂ?Ê∏ÖÂñÆ)
create table if not exists public.tasks (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  status text default 'todo',
  project_id uuid references public.projects(id),
  source_memory_id uuid references public.memories(id),
  due_date date,
  priority int default 1,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- 5. MonthlyReview (?ûÈ°ßÁ≥ªÁµ±)
create table if not exists public."MonthlyReview" (
    id uuid default gen_random_uuid() primary key,
    year int not null,
    month int not null,
    summary text not null,
    metadata jsonb default '{}',
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique(year, month)
);

-- 6. Neural Graph (ÁØÄÈªûË????)
create table if not exists public.nodes (
  id uuid default gen_random_uuid() primary key,
  label text not null unique,
  type text default 'concept',
  metadata jsonb default '{}',
  created_at timestamptz default now()
);
create table if not exists public.edges (
  id uuid default gen_random_uuid() primary key,
  source_id uuid references public.nodes(id) on delete cascade,
  target_id uuid references public.nodes(id) on delete cascade,
  relation text default 'related',
  weight float default 1.0,
  created_at timestamptz default now(),
  constraint unique_edge unique (source_id, target_id, relation)
);

-- 7. Cortex Growth Logs (AI ?™Ê??êÈï∑?•Ë?)
create table if not exists public.cortex_growth_logs (
  id uuid default gen_random_uuid() primary key,
  decision_context text not null,
  options_provided jsonb not null default '{}',
  user_choice text not null,
  ai_prediction text,
  prediction_match boolean,
  lessons_learned text,
  embedding vector(3072),
  created_at timestamptz default now()
);

-- 8. System Usage
create table if not exists public.system_usage (
  id uuid default gen_random_uuid() primary key,
  date date not null default current_date unique,
  request_count int default 0,
  token_usage int default 0,
  updated_at timestamptz default now()
);

-- 9. RAG Functions
create or replace function match_memories (
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql as $$
begin
  return query
  select
    memories.id,
    memories.content,
    jsonb_build_object(
      'date', memories.date,
      'tags', memories.tags,
      'category', memories.category,
      'mood', memories.mood,
      'focus', memories.focus,
      'energy', memories.energy
    ) as metadata,
    1 - (memories.embedding <=> query_embedding) as similarity
  from memories
  where memories.embedding is not null
    and 1 - (memories.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
end;
$$;

create or replace function match_documents (
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  title text,
  url text,
  content text,
  metadata jsonb,
  similarity float
)
language plpgsql as $$
begin
  return query
  select
    documents.id,
    documents.title,
    documents.url,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) AS similarity
  from documents
  where documents.embedding is not null 
    and 1 - (documents.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
end;
$$;

-- 11. Memory Embeddings RPCs (1536 dim)
create or replace function match_memory_embeddings (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  content text,
  metadata jsonb,
  similarity float,
  created_at timestamptz,
  last_accessed_at timestamptz,
  access_count int
)
language plpgsql as $$
begin
  return query
  select
    m.id,
    m.content,
    m.metadata,
    1 - (m.embedding <=> query_embedding) as similarity,
    m.created_at,
    m.last_accessed_at,
    m.access_count
  from memory_embeddings m
  where m.embedding is not null
    and 1 - (m.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
end;
$$;

create or replace function increment_memory_embeddings_access(ids uuid[])
returns void as $$
begin
  update memory_embeddings
  set access_count = access_count + 1,
      last_accessed_at = now()
  where id = any(ids);
end;
$$ language plpgsql;

-- 10. Security Policies
alter table public.memories enable row level security;
alter table public.projects enable row level security;
alter table public.tasks enable row level security;
alter table public."MonthlyReview" enable row level security;
alter table public.nodes enable row level security;
alter table public.edges enable row level security;
alter table public.documents enable row level security;
alter table public.cortex_growth_logs enable row level security;
alter table public.system_usage enable row level security;

do $$ begin
  if not exists (select 1 from pg_policies where tablename='memories' and policyname='Allow all access') then
    create policy "Allow all access" on public.memories for all using (true) with check (true);
  end if;
end $$;

-- Policies for others (idempotent)
drop policy if exists "Allow all access" on public.projects;
create policy "Allow all access" on public.projects for all using (true) with check (true);
drop policy if exists "Allow all access" on public.tasks;
create policy "Allow all access" on public.tasks for all using (true) with check (true);
drop policy if exists "Allow all access" on public."MonthlyReview";
create policy "Allow all access" on public."MonthlyReview" for all using (true) with check (true);
drop policy if exists "Allow all access" on public.nodes;
create policy "Allow all access" on public.nodes for all using (true) with check (true);
drop policy if exists "Allow all access" on public.edges;
create policy "Allow all access" on public.edges for all using (true) with check (true);
drop policy if exists "Allow all access" on public.documents;
create policy "Allow all access" on public.documents for all using (true) with check (true);
drop policy if exists "Allow all access" on public.cortex_growth_logs;
create policy "Allow all access" on public.cortex_growth_logs for all using (true) with check (true);
drop policy if exists "Allow all access" on public.system_usage;
create policy "Allow all access" on public.system_usage for all using (true) with check (true);
"""


@router.post("/setup-db")
async def setup_database(request: Request):
    """
    Run LifeOS schema by reading migration files from database-hippocampus.
    This ensures the Cloud DB is always in sync with the latest local blueprint.
    """
    from app.core.database import get_request_client
    from pathlib import Path

    supabase_url = request.headers.get("X-Supabase-URL")
    supabase_key = request.headers.get("X-Supabase-Key")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=400, detail="X-Supabase-URL and X-Supabase-Key headers are required")

    try:
        db = get_request_client(request)
        if not db:
            raise HTTPException(status_code=400, detail="Could not connect to your Supabase")
        
        # 1. Locate the Hippocampus Migrations
        # Correct path from backend-cortex/app/api/v1/system.py back to project root
        project_root = Path(__file__).parent.parent.parent.parent.parent
        hippocampus_dir = project_root / "database-hippocampus"
        migrations_dir = hippocampus_dir / "migrations"
        
        sql_files = sorted(list(migrations_dir.glob("*.sql")))
        
        if not sql_files:
            # Fallback to the internal hardcoded baseline if no migrations found
            logger.warning("No migration files found in database-hippocampus. Using internal baseline.")
            all_sql = LIFEOS_SETUP_SQL
        else:
            logger.info(f"Found {len(sql_files)} migration files in {migrations_dir}")
            # Combine migrations in order
            all_sql = ""
            for f in sql_files:
                all_sql += f"\n-- MIGRATION: {f.name}\n"
                all_sql += f.read_text(encoding="utf-8") + "\n"

        # 2. Split and Execute
        statements = [s.strip() for s in all_sql.split(";") if s.strip() and not s.strip().startswith("--")]
        
        errors = []
        success_count = 0
        for stmt in statements:
            try:
                # ?ö® Dependency: User MUST have an 'exec' RPC function defined in Supabase 
                db.rpc("exec", {"sql": stmt}).execute()
                success_count += 1
            except Exception as e:
                err_msg = str(e)
                if "already exists" in err_msg.lower() or "duplicate" in err_msg.lower():
                    success_count += 1
                elif "function public.exec(sql text) does not exist" in err_msg.lower():
                    raise HTTPException(
                        status_code=400, 
                        detail="Missing 'exec' function. Run bootstrap SQL in Supabase Editor first."
                    )
                else:
                    errors.append(f"{stmt[:60]}... ??{err_msg[:100]}")
        
        return {
            "success": True,
            "message": f"Hippocampus Sync Complete. {success_count} statements executed.",
            "migrations_performed": [f.name for f in sql_files] if sql_files else ["Internal Baseline"],
            "errors": errors[:5] if errors else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"setup-db error: {e}")
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


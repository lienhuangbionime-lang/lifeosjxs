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


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Return system status including current model and available versions.
    """
    try:
        from app.core.gemini import gemini_client
        fast = get_model("fast")

        smart = get_model("smart")
        # choose current model based on env preference or default to fast
        current_choice = "smart" if smart.get("configured") else "fast"
        current_model = smart["model"] if current_choice == "smart" else fast["model"]

        status = "ok" if (fast.get("configured") or smart.get("configured")) else "degraded"
        
        # Try to fetch real quota information from Gemini API
        # Get real usage from DB
        try:
            from app.core.usage import get_daily_usage
            usage = await get_daily_usage()
            count = usage.get("request_count", 0)
            
            # Gemini Free Limit: 1500 RPD for Flash/Lite, 50 for Pro
            is_pro = "pro" in current_model.lower()
            limit = 50 if is_pro else 1500
            remaining = max(0, limit - count)
            
            model_label = "Pro" if is_pro else "Flash/Lite"
            remaining_info = f"{remaining} / {limit} ({model_label} Quota Today)"
        except Exception as e:
            remaining_info = "Free Tier (Usage tracking active)"

        return SystemStatusResponse(
            status=status,
            current_model=current_model,
            model_versions=[fast["model"], smart["model"]],
            remaining_requests=remaining_info,
            note="Models obtained from app/core/gemini factory."
        )
    except Exception as e:
        logger.exception("Failed to get system status: %s", e)
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


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
# [NEW] One-Click Supabase Setup — runs full LifeOS schema on user's DB
# ============================================================================
from fastapi import Request
from pydantic import BaseModel as _BaseModel

LIFEOS_SETUP_SQL = """
-- LifeOS v3.5 Full Schema Setup (auto-generated)
create extension if not exists vector;

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
  category text,
  is_ai boolean default false,
  ai_model text,
  local_path text,
  content_hash text,
  ai_insights text,
  embedding vector(3072)
);

create table if not exists public.projects (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  status text default 'active',
  progress int default 0,
  start_date date,
  due_date date,
  parent_id uuid references public.projects(id),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

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

create table if not exists public.system_usage (
  id uuid default gen_random_uuid() primary key,
  date date not null default current_date unique,
  request_count int default 0,
  token_usage int default 0,
  updated_at timestamptz default now()
);

-- RLS: allow all access (user controls their own Supabase)
alter table public.memories enable row level security;
alter table public.projects enable row level security;
alter table public.tasks enable row level security;
alter table public.nodes enable row level security;
alter table public.edges enable row level security;
alter table public.cortex_growth_logs enable row level security;
alter table public.system_usage enable row level security;

do $$ begin
  if not exists (select 1 from pg_policies where tablename='memories' and policyname='Allow all access') then
    create policy "Allow all access" on public.memories for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='projects' and policyname='Allow all access') then
    create policy "Allow all access" on public.projects for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='tasks' and policyname='Allow all access') then
    create policy "Allow all access" on public.tasks for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='nodes' and policyname='Allow all access') then
    create policy "Allow all access" on public.nodes for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='edges' and policyname='Allow all access') then
    create policy "Allow all access" on public.edges for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='cortex_growth_logs' and policyname='Allow all access') then
    create policy "Allow all access" on public.cortex_growth_logs for all using (true) with check (true);
  end if;
  if not exists (select 1 from pg_policies where tablename='system_usage' and policyname='Allow all access') then
    create policy "Allow all access" on public.system_usage for all using (true) with check (true);
  end if;
end $$;

-- RAG Vector Search Function
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
    jsonb_build_object('date', memories.date, 'tags', memories.tags, 'category', memories.category, 'mood', memories.mood, 'focus', memories.focus, 'energy', memories.energy) as metadata,
    1 - (memories.embedding <=> query_embedding) as similarity
  from memories
  where memories.embedding is not null
    and 1 - (memories.embedding <=> query_embedding) > match_threshold
  order by memories.embedding <=> query_embedding
  limit match_count;
end;
$$;

-- Indexes
create index if not exists idx_memories_date on public.memories(date);
create index if not exists idx_memories_tags on public.memories using gin(tags);
"""


@router.post("/setup-db")
async def setup_database(request: Request):
    """
    Run the full LifeOS schema on the user's own Supabase.
    Requires X-Supabase-URL and X-Supabase-Key headers (service_role key recommended).
    """
    from app.core.database import get_request_client
    import httpx

    supabase_url = request.headers.get("X-Supabase-URL")
    supabase_key = request.headers.get("X-Supabase-Key")

    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=400, detail="X-Supabase-URL and X-Supabase-Key headers are required")

    # Use Supabase REST SQL endpoint
    sql_endpoint = f"{supabase_url.rstrip('/')}/rest/v1/rpc/exec_sql"
    
    # Try via pg_query or direct SQL endpoint
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{supabase_url.rstrip('/')}/rest/v1/",
                headers={
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "params=single-object",
                },
            )
        # Supabase doesn't expose raw SQL via REST — use their management API or pg_query
        # Fallback: use supabase-py rpc if available
        db = get_request_client(request)
        if not db:
            raise HTTPException(status_code=400, detail="Could not connect to your Supabase")
        
        # Execute SQL statements one by one via supabase-py
        # Split on semicolons, filter empty
        statements = [s.strip() for s in LIFEOS_SETUP_SQL.split(";") if s.strip() and not s.strip().startswith("--")]
        
        errors = []
        success_count = 0
        for stmt in statements:
            try:
                db.rpc("exec", {"sql": stmt}).execute()
                success_count += 1
            except Exception as e:
                err_msg = str(e)
                # Ignore "already exists" errors — those are OK
                if "already exists" in err_msg.lower() or "duplicate" in err_msg.lower():
                    success_count += 1
                else:
                    errors.append(f"{stmt[:60]}... → {err_msg[:100]}")
        
        if errors:
            logger.warning(f"Setup-db completed with {len(errors)} non-fatal errors: {errors[:3]}")
        
        return {
            "success": True,
            "message": f"LifeOS schema setup complete. {success_count} statements executed.",
            "errors": errors[:5] if errors else []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"setup-db error: {e}")
        raise HTTPException(status_code=500, detail=f"Setup failed: {str(e)}")


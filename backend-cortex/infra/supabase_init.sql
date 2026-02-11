-- ============================================================================
-- LifeOS v3.1 Supabase Initialization SQL
-- Run this in your Supabase SQL Editor to set up all tables and columns.
-- ============================================================================

-- Enable Vector Extension for Embeddings (AI Brain)
create extension if not exists vector;

-- 1. Memories (日記與核心記錄)
-- 包含情緒追蹤 (Mood/Focus/Energy) 與 AI 嵌入向量
create table public.memories (
  id uuid default gen_random_uuid() primary key,
  content text not null,
  date date not null default current_date,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  
  -- Metrics (1-10)
  mood int default 5,
  focus int default 5,
  energy int default 5,
  
  -- AI Metadata
  tags text[] default '{}',
  category text,
  is_ai boolean default false,
  ai_model text,
  
  -- Vector Embedding (for RAG/Search) - 3072 dim for new Gemini
  embedding vector(3072)
);

-- Index for fast retrieval by date (Timeline View)
create index idx_memories_date on public.memories(date);


-- 2. Projects (專案管理)
-- 用於追蹤長期目標與進度圖表
create table public.projects (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  status text default 'active', -- active, completed, on_hold, archived
  progress int default 0, -- 0-100%
  meta jsonb default '{}'::jsonb, -- Category and other metadata
  
  start_date date,
  due_date date,
  
  parent_id uuid references public.projects(id), -- Sub-projects
  
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);


-- 3. Tasks (行動清單)
-- 從日記中提取的可執行項目 (Action Items)
create table public.tasks (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  status text default 'todo', -- todo, in_progress, done
  
  project_id uuid references public.projects(id),
  source_memory_id uuid references public.memories(id), -- 來源日記
  
  due_date date,
  priority int default 1, -- 1-5
  
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);


-- 4. Graph Nodes (知識圖譜節點)
-- 用於視覺化思考網絡 (Neural Graph)
create table public.nodes (
  id uuid default gen_random_uuid() primary key,
  label text not null unique,
  type text default 'concept', -- concept, tag, person, tool
  metadata jsonb default '{}',
  
  created_at timestamptz default now()
);

-- 5. Graph Edges (知識圖譜連線)
create table public.edges (
  id uuid default gen_random_uuid() primary key,
  source_id uuid references public.nodes(id) on delete cascade,
  target_id uuid references public.nodes(id) on delete cascade,
  relation text default 'related',
  weight float default 1.0,
  
  created_at timestamptz default now(),
  
  -- [FIX] Unique constraint for upsert
  constraint unique_edge unique (source_id, target_id, relation)
);


-- 6. System Usage (系統用量)
create table public.system_usage (
    id uuid default gen_random_uuid() primary key,
    date date not null default current_date unique,
    request_count int default 0,
    token_usage int default 0,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create index idx_usage_date on public.system_usage(date);


-- Row Level Security (RLS) - Optional: Enable if you need public read access constraints
alter table public.memories enable row level security;
alter table public.projects enable row level security;
alter table public.tasks enable row level security;
alter table public.nodes enable row level security;
alter table public.edges enable row level security;
alter table public.system_usage enable row level security;

-- Default Policy: Allow all operations for authenticated users (or anon for dev)
create policy "Allow all access" on public.memories for all using (true) with check (true);
create policy "Allow all access" on public.projects for all using (true) with check (true);
create policy "Allow all access" on public.tasks for all using (true) with check (true);
create policy "Allow all access" on public.nodes for all using (true) with check (true);
create policy "Allow all access" on public.edges for all using (true) with check (true);
create policy "Allow all access" on public.system_usage for all using (true) with check (true);

-- Vector Search Function for RAG
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
language plpgsql
as $$
begin
  return query
  select
    memories.id,
    memories.content,
    jsonb_build_object('date', memories.date, 'tags', memories.tags, 'category', memories.category) as metadata,
    1 - (memories.embedding <=> query_embedding) as similarity
  from memories
  where 1 - (memories.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
end;
$$;


-- ============================================================================
-- LifeOS v3.6 - Supabase Migration 011
-- Purpose: Expand Phase E Knowledge Decay to Memories & Nodes
-- Date: 2026-03-05
-- ============================================================================

-- 1. Add decay metrics to 'memories' (documents & nodes already have these from 009)
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0;
ALTER TABLE public.memories ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- 2. RPC to increment access_count for memories
CREATE OR REPLACE FUNCTION increment_memory_access(memory_ids uuid[])
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE public.memories
  SET access_count = access_count + 1,
      last_accessed_at = NOW()
  WHERE id = ANY(memory_ids);
END;
$$;

-- 3. RPC to increment access_count for nodes
CREATE OR REPLACE FUNCTION increment_node_access(node_ids uuid[])
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE public.nodes
  SET access_count = access_count + 1,
      last_accessed_at = NOW()
  WHERE id = ANY(node_ids);
END;
$$;

-- 4. Update 'match_memories' RPC to return decay columns
DROP FUNCTION IF EXISTS public.match_memories(vector, float, int);
CREATE OR REPLACE FUNCTION match_memories(
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  content text,
  ai_insights text,
  metadata jsonb,
  similarity float,
  date date,
  access_count int,
  last_accessed_at timestamptz
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    memories.id,
    memories.content,
    memories.ai_insights,
    jsonb_build_object(
      'date', memories.date,
      'tags', memories.tags,
      'category', memories.category,
      'mood', memories.mood,
      'focus', memories.focus,
      'energy', memories.energy
    ) as metadata,
    1 - (memories.embedding <=> query_embedding) as similarity,
    memories.date,
    memories.access_count,
    memories.last_accessed_at
  FROM memories
  WHERE 
    memories.embedding IS NOT NULL
    AND 1 - (memories.embedding <=> query_embedding) > match_threshold
    AND memories.is_archived = false
  ORDER BY memories.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

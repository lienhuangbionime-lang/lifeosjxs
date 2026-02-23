-- LifeOS v3.5 - Database Schema Sync Migration
-- Purpose: Align Supabase tables with the latest backend capabilities (Local-First, Hybrid Search)
-- Date: 2026-02-23

-- 1. Memories Table Enhancements
ALTER TABLE memories ADD COLUMN IF NOT EXISTS local_path TEXT;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS content_hash TEXT;
ALTER TABLE memories ADD COLUMN IF NOT EXISTS ai_insights TEXT;

-- Ensure vector dimension is 3072 for text-embedding-004
-- If it was previously 768 or 1536, this will require a data migration 
-- but for now we ensure the column can handle it.
-- Note: Changing vector dimension usually requires dropping and recreating.
-- DO NOT RUN THIS IF YOU HAVE PRECIOUS EMBEDDINGS ALREADY.
-- ALTER TABLE memories ALTER COLUMN embedding TYPE vector(3072);

-- 2. Update match_memories RPC
-- This version includes mood, focus, and energy in the metadata for better RAG context.
CREATE OR REPLACE FUNCTION match_memories(
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
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
  FROM memories
  WHERE 
    memories.embedding IS NOT NULL
    AND 1 - (memories.embedding <=> query_embedding) > match_threshold
  ORDER BY memories.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- 3. Ensure Nodes & Edges Constraints
-- D3 visualization relies on these existing correctly
ALTER TABLE nodes ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- 4. Indexing for performance
CREATE INDEX IF NOT EXISTS idx_memories_local_path ON memories(local_path);
CREATE INDEX IF NOT EXISTS idx_memories_content_hash ON memories(content_hash);

COMMENT ON TABLE memories IS 'Cortex Core Memories - V3.5 Local-First Enabled';

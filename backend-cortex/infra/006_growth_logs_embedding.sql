-- Migration: 006_growth_logs_embedding
-- Description: Add embedding vector to cortex_growth_logs for AI semantic search
-- Date: 2026-02-24
-- Rationale: 全部的資料都是要讓 AI 有向量搜尋能力

-- 1. Add embedding column to cortex_growth_logs
ALTER TABLE public.cortex_growth_logs
ADD COLUMN IF NOT EXISTS embedding vector(3072);

-- 2. Add HNSW index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_growth_logs_embedding
ON public.cortex_growth_logs
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 3. Create match_growth_logs RPC function (mirrors match_memories)
CREATE OR REPLACE FUNCTION match_growth_logs (
  query_embedding vector(3072),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  decision_context text,
  lessons_learned text,
  prediction_match boolean,
  ai_prediction text,
  user_choice text,
  created_at timestamptz,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    g.id,
    g.decision_context,
    g.lessons_learned,
    g.prediction_match,
    g.ai_prediction,
    g.user_choice,
    g.created_at,
    1 - (g.embedding <=> query_embedding) AS similarity
  FROM cortex_growth_logs g
  WHERE g.embedding IS NOT NULL
    AND 1 - (g.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

-- Usage note:
-- SELECT * FROM match_growth_logs(
--   '[<3072-dim vector>]',
--   0.5,
--   5
-- );

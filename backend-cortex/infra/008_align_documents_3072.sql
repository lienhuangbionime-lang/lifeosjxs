
-- Phase P18: Architectural Alignment
-- Align 'documents' table to the standard 3072 dimension.
-- Safe to run as 'documents' is currently empty (0 rows).

-- 1. Drop existing match function if it uses old signature
DROP FUNCTION IF EXISTS public.match_documents(vector, float, int);

-- 2. Drop and recreate embedding column with 3072 dimensions
ALTER TABLE public.documents DROP COLUMN IF EXISTS embedding;
ALTER TABLE public.documents ADD COLUMN embedding VECTOR(3072);

-- 3. Re-create match function with 3072 signature
CREATE OR REPLACE FUNCTION match_documents (
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  id uuid,
  title text,
  url text,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    documents.id,
    documents.title,
    documents.url,
    documents.content,
    documents.metadata,
    1 - (documents.embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

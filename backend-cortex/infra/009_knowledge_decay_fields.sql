-- Phase E: Knowledge Decay Metrics and Archival (v4.0)
-- 1. Add decay metrics and archival status to 'documents' table
ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0;
ALTER TABLE public.documents ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- 2. Add decay metrics and archival status to 'nodes' table
ALTER TABLE public.nodes ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.nodes ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0;
ALTER TABLE public.nodes ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- 3. Update 'match_documents' RPC to filter out archived documents
DROP FUNCTION IF EXISTS public.match_documents(vector, float, int);
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
  similarity float,
  access_count int,
  last_accessed_at timestamptz
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
    1 - (documents.embedding <=> query_embedding) AS similarity,
    documents.access_count,
    documents.last_accessed_at
  FROM documents
  WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
    AND documents.is_archived = false -- Knowledge Decay: Exclude archived
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;

-- 4. Update 'match_memories' RPC to also potentially exclude archived memories if we decide to add that to memories later, but for now we focus on documents and nodes per the spec.
-- Note: 'match_memories' currently doesn't have is_archived on memories table, but we ensure 'match_documents' is secure.

-- 5. RPC to easily increment access_count
CREATE OR REPLACE FUNCTION increment_document_access(doc_ids uuid[])
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE public.documents
  SET access_count = access_count + 1,
      last_accessed_at = NOW()
  WHERE id = ANY(doc_ids);
END;
$$;

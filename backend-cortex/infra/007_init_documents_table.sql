-- Phase P10: Knowledge & Memory Isolation
-- Idempotent initialization of the 'documents' table.

-- 1. Create table if it doesn't exist at all
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY
);

-- 2. Add columns individually with safety guards
DO $$
BEGIN
    -- Core Content
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='title') THEN
        ALTER TABLE public.documents ADD COLUMN title TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='url') THEN
        ALTER TABLE public.documents ADD COLUMN url TEXT UNIQUE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='content') THEN
        ALTER TABLE public.documents ADD COLUMN content TEXT NOT NULL DEFAULT '';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='doc_type') THEN
        ALTER TABLE public.documents ADD COLUMN doc_type TEXT DEFAULT 'webpage';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='tags') THEN
        ALTER TABLE public.documents ADD COLUMN tags TEXT[] DEFAULT '{}';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='metadata') THEN
        ALTER TABLE public.documents ADD COLUMN metadata JSONB DEFAULT '{}';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='embedding') THEN
        ALTER TABLE public.documents ADD COLUMN embedding VECTOR(3072);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='created_at') THEN
        ALTER TABLE public.documents ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='documents' AND column_name='updated_at') THEN
        ALTER TABLE public.documents ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Indexing for performance
CREATE INDEX IF NOT EXISTS idx_documents_url ON public.documents(url);
CREATE INDEX IF NOT EXISTS idx_documents_type ON public.documents(doc_type);

-- Vector Search Function for Documents
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

-- RLS
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access" ON public.documents FOR ALL USING (true) WITH CHECK (true);

COMMENT ON TABLE documents IS 'External knowledge, search results, and technical documentation - Physically isolated from personal memories.';

import os
import logging
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from supabase.client import Client, create_client

# Init Logger
logger = logging.getLogger("cortex.memory")

# Using text-embedding-3-small as requested
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

class MemoryService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")  # Ensure this is SERVICE_KEY for writing if RLS is on, or anon if policy allows
        self.client: Optional[Client] = None

        if self.supabase_url and self.supabase_key:
            try:
                self.client = create_client(self.supabase_url, self.supabase_key)
                logger.info("MemoryService: Supabase client initialized.")
            except Exception as e:
                logger.error(f"MemoryService: Failed to init Supabase: {e}")
        else:
            logger.warning("MemoryService: Missing SUPABASE_URL or SUPABASE_KEY.")

    async def save_memory(self, content: str, metadata: Dict[str, Any] = {}) -> bool:
        """
        Embed content and save to 'documents' table via direct insert.
        """
        if not self.client:
            logger.error("MemoryService: Client not ready.")
            return False

        try:
            # 1. Generate Embedding
            vector = embeddings.embed_query(content)

            # 2. Prepare Payload
            payload = {
                "content": content,
                "metadata": metadata,
                "embedding": vector
            }

            # 3. Insert
            # Explicit non-None check for linter
            if self.client:
                self.client.table("documents").insert(payload).execute()
                # Simplify logging to avoid slice type error
                preview = content if len(content) < 30 else content[:30]
                logger.info(f"Memory saved: {preview}...")
                return True
            return False
        except Exception as e:
            logger.error(f"MemoryService: Info save failed: {e}")
            return False

    async def search_memory(self, query: str, limit: int = 5, threshold: float = 0.7):
        """
        Embed query and call RPC 'match_documents'
        """
        if not self.client:
            return []

        try:
            # 1. Embed Query
            vector = embeddings.embed_query(query)

            # 2. RPC Call
            response = self.client.rpc(
                'match_documents',
                {
                    'query_embedding': vector,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()

            return response.data
        except Exception as e:
            logger.error(f"MemoryService: Search failed: {e}")
            return []

memory_service = MemoryService()

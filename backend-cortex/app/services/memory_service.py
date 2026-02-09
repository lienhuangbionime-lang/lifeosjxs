import os
import logging
from typing import List, Dict, Any, Optional
import textwrap
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase.client import Client, create_client

# Init Logger
logger = logging.getLogger("cortex.memory")

# Using Google Gemini Embedding 004 (768 dimensions)
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

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
        # Strict Client Check
        client = self.client
        if client is None:
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
            client.table("documents").insert(payload).execute()
            
            # Safe Logging
            import textwrap
            log_preview = textwrap.shorten(content, width=30, placeholder="...")
            logger.info(f"Memory saved: {log_preview}")
            return True
        except Exception as e:
            logger.error(f"MemoryService: Info save failed: {e}")
            return False

    async def search_memory(self, query: str, limit: int = 5, threshold: float = 0.7):
        """
        Embed query and call RPC 'match_documents'
        """
        client = self.client
        if client is None:
            return []

        try:
            # 1. Embed Query
            vector = embeddings.embed_query(query)

            # 2. RPC Call
            response = client.rpc(
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

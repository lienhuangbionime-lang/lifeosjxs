import os
import logging
from typing import List, Dict, Any, Optional
import textwrap
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase.client import Client, create_client

# Init Logger
logger = logging.getLogger("cortex.memory")

# Lazy load or safe init embeddings
embeddings = None
try:
    # Check if key is available (it should be if main.py ran, but for direct import safety)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not os.getenv("GOOGLE_API_KEY") and gemini_key:
        os.environ["GOOGLE_API_KEY"] = gemini_key
        
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
except Exception as e:
    logger.error(f"Failed to init Gemini Embeddings: {e}")
    embeddings = None

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
            if not embeddings:
                logger.error("MemoryService: Embeddings not initialized.")
                return False
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
            if not embeddings:
                logger.error("MemoryService: Embeddings not initialized.")
                return []
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

    async def ask_brain(self, question: str, limit: int = 5) -> str:
        """
        Ask the brain a question:
        1. Search for relevant memories
        2. Use Gemini Pro to generate an answer based on context
        """
        try:
            # Import Gemini LLM
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            
            # 1. Search for relevant memories
            memories = await self.search_memory(question, limit=limit)
            
            if not memories:
                return "I don't have any relevant memories to answer this question."
            
            # 2. Build context from memories
            context = "\n\n".join([
                f"Memory {i+1}: {mem.get('content', '')}"
                for i, mem in enumerate(memories)
            ])
            
            # 3. Create prompt
            template = """You are a helpful AI assistant with access to the user's memories.
            
Context from memories:
{context}

User question: {question}

Please provide a helpful answer based on the context above. If the context doesn't contain relevant information, say so."""
            
            prompt = ChatPromptTemplate.from_template(template)
            
            # 4. Initialize Gemini Pro
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
            
            # 5. Generate response
            chain = prompt | llm
            response = await chain.ainvoke({"context": context, "question": question})
            
            return response.content
            
        except Exception as e:
            logger.error(f"MemoryService: ask_brain failed: {e}")
            return f"Error generating response: {str(e)}"

memory_service = MemoryService()

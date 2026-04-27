import os
import logging
from typing import List, Dict, Any, Optional
import textwrap
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from supabase.client import Client, create_client

# Init Logger
logger = logging.getLogger("cortex.memory")

from app.services.embedder import generate_embedding

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
            # 1. Generate Embedding (1536 Dimensions)
            vector = await generate_embedding(content, dimensionality=1536)
            if not vector:
                logger.error("MemoryService: Embedding generation failed.")
                return False

            # 2. Prepare Payload
            payload = {
                "content": content,
                "metadata": metadata,
                "embedding": vector
            }

            # 3. Insert
            client.table("memory_embeddings").insert(payload).execute()
            
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
            # 1. Embed Query (1536 Dimensions)
            vector = await generate_embedding(query, task_type="retrieval_query", dimensionality=1536)
            if not vector:
                logger.error("MemoryService: Embedding generation failed.")
                return []

            # 2. RPC Call
            response = client.rpc(
                'match_memories',
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

    async def unified_search(self, question: str, limit: int = 5, namespace: str = "personal"):
        """
        [v7.2] Refactored Master Search with Namespace Isolation & Dual-Query.
        - namespace="personal": Force path filtering for 'memory/' (Diary).
        - namespace="session": Target 'session_history' (Daily Logs).
        - Dual-Query: Parallel search if 'decision/plan' detected.
        """
        from app.services.rag_service import rag_service
        import asyncio

        # 1. Detect Dual-Query Intent (Decision / Plan)
        dual_keywords = ["æ±ºç?", "è¨ˆç•«", "??, "?“ç?", "decision", "plan", "intent", "strategy"]
        is_dual = any(kw in question.lower() for kw in dual_keywords)

        if is_dual:
            logger.info(f"?? Dual-Query triggered for intent: '{question}'")
            # Parallel Execution
            tasks = [
                # Track 1: Personal Diary (Files in memory/)
                rag_service.search_memory_embeddings(question, limit=limit, path_prefix="memory/"),
                # Track 2: Session History (Daily Logs / memories table)
                rag_service.search_and_rerank(question, recall_limit=30, top_k=limit)
            ]
            diary_results, session_results = await asyncio.gather(*tasks)

            # Attribution Grouping
            diary_text = "\n\n".join([f"[{r.get('metadata', {}).get('file_name', 'Entry')}] {r.get('content', '')}" for r in diary_results])
            session_text = "\n\n".join([f"[{r.get('date', 'Discussion')}] {r.get('content', '')}" for r in session_results])

            combined_memories = f"### [ä¾†è‡ª?¨ç??¥è? (Personal Diary)]\n{diary_text or '?¡ç›¸?œç???}\n\n### [ä¾†è‡ª?‘å€‘é?å¾€è¨Žè? (Previous Discussions)]\n{session_text or '?¡ç›¸?œç???}"
            
            return {
                "memories": combined_memories.strip()
            }
        
        # 2. Single Namespace Mode
        if namespace == "session":
            results = await rag_service.search_and_rerank(question, recall_limit=30, top_k=limit)
            text = "\n\n".join([f"[{r.get('date', 'Discussion')}] {r.get('content', '')}" for r in results])
            return {"memories": f"### [ä¾†è‡ª?‘å€‘é?å¾€è¨Žè?]\n{text}"}
        else:
            # Default to personal namespace (memory/ prefix)
            results = await rag_service.search_memory_embeddings(question, limit=limit, path_prefix="memory/")
            text = "\n\n".join([f"[{r.get('metadata', {}).get('file_name', 'Entry')}] {r.get('content', '')}" for r in results])
            return {"memories": f"### [ä¾†è‡ª?¨ç??¥è?]\n{text}"}

    async def ask_brain(self, question: str, limit: int = 5) -> str:
        """
        Ask the brain a question:
        1. Search for relevant memories
        2. Use Gemma Pro to generate an answer based on context
        """
        try:
            # Import Gemma LLM
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
            
            # 4. Initialize Gemma Pro
            llm = ChatGoogleGenerativeAI(model="gemma-2.0-flash", temperature=0.7)
            
            # 5. Generate response
            chain = prompt | llm
            response = await chain.ainvoke({"context": context, "question": question})
            
            return response.content
            
        except Exception as e:
            logger.error(f"MemoryService: ask_brain failed: {e}")
            return f"Error generating response: {str(e)}"

memory_service = MemoryService()

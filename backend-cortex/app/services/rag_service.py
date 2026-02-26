import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import UploadFile

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from supabase.client import Client, create_client

# For Upgrade Features
from PIL import Image
import io
import re
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

# Init Logger
logger = logging.getLogger("cortex.rag")

# Init Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Optional[Client] = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Failed to init Supabase: {e}")

# Init Gemini
try:
    from app.core.gemini import get_model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    smart_config = get_model("smart")
    llm = ChatGoogleGenerativeAI(model=smart_config["model"], temperature=0)
    logger.info(f"RAG Service initialized with model: {smart_config['model']}")
except Exception as e:
    logger.warning(f"Failed to init Gemini: {e}")
    embeddings = None
    llm = None

class RAGService:
    def __init__(self):
        if not supabase or not embeddings:
            logger.warning("RAG Service Disabled: Missing Supabase or Gemini Config")
            self.memories_store = None
            self.documents_store = None
            return

        self.memories_store = SupabaseVectorStore(
            client=supabase,
            embedding=embeddings,
            table_name="memories",
            query_name="match_memories",
        )
        self.documents_store = SupabaseVectorStore(
            client=supabase,
            embedding=embeddings,
            table_name="documents",
            query_name="match_documents",
        )
        self.llm = llm

    async def check_duplicate(self, url: str) -> bool:
        """Check if a URL already exists in the documents table."""
        if not supabase:
            return False
        try:
            res = supabase.table("documents").select("id").eq("url", url).execute()
            return len(res.data) > 0
        except Exception as e:
            logger.error(f"Error checking duplicate URL: {e}")
            return False
    async def ingest_text(self, text: str, meta: Dict[str, Any] = {}, target: str = "memories"):
        """Chunk text and store in the specified Supabase Vector Store"""
        logger.info(f"Ingesting text into {target}... {meta}")
        
        # 1. Check for URL/YouTube
        url_content = self._try_fetch_url_content(text)
        if url_content:
            url = text.strip()
            # De-duplication check
            if await self.check_duplicate(url):
                logger.info(f"URL {url} already exists in documents. Skipping duplicate ingestion.")
                return 0
                
            text = f"Source URL: {url}\n\nContent:\n{url_content}"
            meta["url"] = url
            # Auto-route URLs to documents if target is memories but it's clearly an external link
            if target == "memories" and meta.get("source") != "capture":
                target = "documents"

        # 2. Crystallize 2.0: Generate summary for documents
        if target == "documents" and len(text) > 500:
            summary = await self._crystallize_document(text)
            meta["summary"] = summary
            logger.info(f"Crystallize 2.0: Generated summary ({len(summary)} chars)")

        # 3. Split
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.create_documents([text], metadatas=[meta])
        
        # 4. Store
        store = self.documents_store if target == "documents" else self.memories_store
        if store:
            store.add_documents(docs)
            logger.info(f"Ingested {len(docs)} chunks into {target}.")
            return len(docs)
        return 0

    async def ingest_file(self, file: UploadFile, target: str = "memories"):
        """Process file (PDF/Text/Image) and store in the specified target"""
        logger.info(f"Processing file: {file.filename} ({file.content_type})")
        
        # 1. Handle Image
        if file.content_type and file.content_type.startswith("image/"):
            return await self._process_image(file)

        # 2. Handle Documents (PDF/Text)
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
            
        try:
            if file.filename.lower().endswith(".pdf"):
                loader = PyPDFLoader(temp_path)
            else:
                loader = TextLoader(temp_path)
            
            raw_docs = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.split_documents(raw_docs)
            
            for doc in docs:
                doc.metadata["source"] = file.filename
                
            if target == "documents" and self.documents_store:
                self.documents_store.add_documents(docs)
                logger.info(f"Ingested {len(docs)} chunks from {file.filename} into documents")
                return len(docs)
            elif self.memories_store:
                self.memories_store.add_documents(docs)
                logger.info(f"Ingested {len(docs)} chunks from {file.filename} into memories")
                return len(docs)
            return 0
            
        except Exception as e:
            logger.error(f"Error ingesting file: {e}")
            raise e
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def _process_image(self, file: UploadFile) -> int:
        """Analyze image with Gemini Vision and store description"""
        try:
            content = await file.read()
            image_data = {"mime_type": file.content_type, "data": content}
            
            # Use LLM to describe image
            prompt = "Describe this image in detail. Extract any text, charts, or key information."
            message = HumanMessage(
                content=[{"type": "text", "text": prompt}, {"type": "image_url", "image_url": f"data:{file.content_type};base64,{image_data}"}] # Langchain format varies, checking docs
            )
            # Actually LangChain Google GenAI supports passing image bytes directly or base64
            # Simplified: Use PIL and pass to model if strictly typed, but simpler approach:
            
            import base64
            b64_data = base64.b64encode(content).decode("utf-8")
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": "Describe this image in detail."},
                    {"type": "image_url", "image_url": f"data:{file.content_type};base64,{b64_data}"}
                ]
            )
            
            response = await self.llm.ainvoke([message])
            description = response.content
            
            logger.info(f"Image analysis complete: {description[:50]}...")
            
            # Store description
            return await self.ingest_text(description, {"source": file.filename, "type": "image_description"})
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return 0

    def _try_fetch_url_content(self, text: str) -> Optional[str]:
        """Detect if text is a URL and fetch content"""
        text = text.strip()
        url_pattern = re.compile(r'https?://\S+')
        if not url_pattern.match(text):
            return None
            
        try:
            # YouTube
            if "youtube.com" in text or "youtu.be" in text:
                return self._fetch_youtube_transcript(text)
            
            # General Web
            response = requests.get(text, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script/style
            for script in soup(["script", "style"]):
                script.decompose()
                
            return soup.get_text(separator='\n', strip=True)
            
        except Exception as e:
            logger.warning(f"Failed to fetch URL {text}: {e}")
            return None

    def _fetch_youtube_transcript(self, url: str) -> str:
        """Fetch YouTube transcript"""
        try:
            video_id = ""
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
            
            if not video_id:
                return "Could not extract Video ID"
                
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([t['text'] for t in transcript_list])
            return f"YouTube Transcript ({video_id}):\n{full_text}"
            
        except Exception as e:
            return f"Failed to fetch YouTube transcript: {e}"

    async def _crystallize_document(self, text: str) -> str:
        """Crystallize 2.0: Generate a high-signal technical summary for a document"""
        if not self.llm:
            return "Summary unavailable."
            
        prompt = ChatPromptTemplate.from_template("""
        [PROTOCOL: CRYSTALLIZE 2.0]
        Analyze the following external content and generate a highly structured, high-signal summary.
        
        Guidelines:
        1. [CORE]: Extract the primary purpose and technical architecture.
        2. [BINDING]: Suggest how this connects to LifeOS (Projects, Systems).
        3. [ACTION]: Identify 2-3 immediate actionable insights or upgrades.
        4. [DIAGRAM]: If applicable, describe a Mermaid chart structure.
        
        Content:
        {content}
        
        Output format: Concise Markdown with GitHub alerts.
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        try:
            # Take only first 10k chars for summary to avoid bloat
            summary = await chain.ainvoke({"content": text[:10000]})
            return summary
        except Exception as e:
            logger.error(f"Crystallization failed: {e}")
            return "Crystallization failed."

    async def unified_search(self, question: str, limit: int = 5) -> Dict[str, str]:
        """
        Dual-Track Retrieval: Search both memories and documents.
        Returns a dictionary with formatted context for both.
        """
        mem_context = ""
        doc_context = ""
        
        try:
            if self.memories_store:
                mem_matches = await self.memories_store.asimilarity_search(question, k=limit)
                mem_context = "\n\n".join([d.page_content for d in mem_matches])
                
            if self.documents_store:
                doc_matches = await self.documents_store.asimilarity_search(question, k=limit)
                doc_context = "\n\n".join([d.page_content for d in doc_matches])
                
            return {
                "memories": mem_context,
                "documents": doc_context
            }
        except Exception as e:
            logger.error(f"Unified Search failed: {e}")
            return {"memories": "", "documents": ""}

    async def query(self, question: str, history: List[Dict[str, str]] = []):
        """RAG Query with History and System Context (Dual-Track Awareness)"""
        logger.info(f"Querying: {question} with history of {len(history)} messages")
        
        if not self.memories_store and not self.documents_store:
            yield "Cortex Error: Vector Stores Unavailable"
            return

        try:
            # 1. Fetch System Context (Projects & Recent Memories)
            system_context = await self._get_system_context()
            
            # 2. Dual-Track Search
            search_results = await self.unified_search(question)
            mem_context = search_results["memories"]
            doc_context = search_results["documents"]
            
            # 3. Load System Persona from Markdown
            persona_path = Path(__file__).parent.parent.parent / "prompts" / "system_cortex.md"
            try:
                cortex_persona = persona_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not load cortex_brain.md: {e}")
                cortex_persona = "You are Cortex, a Senior Tech Lead AI Assistant."

            # 4. Build Messages
            messages = [
                SystemMessage(content=f"""{cortex_persona}
                
                --- SYSTEM CONTEXT (CURRENT STATE) ---
                {system_context}
                
                --- PERSONAL MEMORIES (RAG) ---
                {mem_context if mem_context else "No related personal memories."}
                
                --- EXTERNAL DOCUMENTS & KNOWLEDGE (RAG) ---
                {doc_context if doc_context else "No related external documents."}
                
                Current Task: Assist the user with his request while adhering to the Value Weights and Operational Directives. 
                Synthesize insights from both personal memories and external knowledge where relevant.
                """)
            ]

            
            # Add History
            for h in history:
                if h["role"] == "user":
                    messages.append(HumanMessage(content=h["content"]))
                else:
                    messages.append(AIMessage(content=h["content"]))
            
            # Add Current Question
            messages.append(HumanMessage(content=question))
            
            # 4. Stream Response
            async for chunk in self.llm.astream(messages):
                 yield chunk.content

        except Exception as e:
            logger.error(f"RAG Error: {e}")
            yield f"Error: {str(e)}"

    async def _get_system_context(self) -> str:
        """Fetch current projects and recent memories for prompt context"""
        if not supabase:
            return "No system connection."
        
        try:
            # Fetch active projects
            proj_res = supabase.table("projects").select("name, status, progress").eq("status", "active").limit(5).execute()
            projects = proj_res.data if proj_res.data else []
            proj_str = "\n".join([f"- {p['name']} ({p['status']}, {p['progress']}%)" for p in projects])
            
            # Fetch recent memories
            mem_res = supabase.table("memories").select("content, date").order("date", desc=True).limit(5).execute()
            memories = mem_res.data if mem_res.data else []
            mem_lines = []
            for m in memories:
                content = m.get('content') or ""
                date = m.get('date') or "Unknown"
                mem_lines.append(f"[{date}] {content[:100]}...")
            mem_str = "\n".join(mem_lines)
            
            return f"Active Projects:\n{proj_str}\n\nRecent Memories:\n{mem_str}"
        except Exception as e:
            logger.warning(f"Failed to fetch system context: {e}")
            return "Context unavailable."

rag_service = RAGService()

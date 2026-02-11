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
            self.vector_store = None
            return

        self.vector_store = SupabaseVectorStore(
            client=supabase,
            embedding=embeddings,
            table_name="memories",
            query_name="match_memories",
        )
        self.llm = llm

    async def ingest_text(self, text: str, meta: Dict[str, Any] = {}):
        """Chunk text and store in Supabase Vector Store"""
        logger.info(f"Ingesting text... {meta}")
        
        # 1. Check for URL/YouTube
        url_content = self._try_fetch_url_content(text)
        if url_content:
            text = f"Source URL: {text}\n\nContent:\n{url_content}"
            meta["original_url"] = text.strip()

        # 2. Split
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.create_documents([text], metadatas=[meta])
        
        # 3. Store
        if self.vector_store:
            self.vector_store.add_documents(docs)
            logger.info(f"Ingested {len(docs)} chunks.")
            return len(docs)
        return 0

    async def ingest_file(self, file: UploadFile):
        """Process file (PDF/Text/Image)"""
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
                
            if self.vector_store:
                self.vector_store.add_documents(docs)
                logger.info(f"Ingested {len(docs)} chunks from {file.filename}")
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

    async def query(self, question: str, history: List[Dict[str, str]] = []):
        """RAG Query with History and System Context"""
        logger.info(f"Querying: {question} with history of {len(history)} messages")
        
        if not self.vector_store:
            yield "Cortex Error: Vector Store Unavailable"
            return

        try:
            # 1. Fetch System Context (Projects & Recent Memories)
            system_context = await self._get_system_context()
            
            # 2. Prepare Context from Vector Store (RAG)
            docs = await self.vector_store.asimilarity_search(question, k=5)
            doc_context = "\n\n".join([d.page_content for d in docs])
            
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
                
                --- RETRIEVED KNOWLEDGE (RAG) ---
                {doc_context}
                
                Current Task: Assist 蒼禾 with his request while adhering to the Value Weights and Operational Directives.
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
            mem_str = "\n".join([f"[{m['date']}] {m['content'][:100]}..." for m in memories])
            
            return f"Active Projects:\n{proj_str}\n\nRecent Memories:\n{mem_str}"
        except Exception as e:
            logger.warning(f"Failed to fetch system context: {e}")
            return "Context unavailable."

rag_service = RAGService()

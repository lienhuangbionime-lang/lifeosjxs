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
from supabase.client import Client, create_client

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

# Init Gemini (Lazy or Module Level - assumming GOOGLE_API_KEY is present)
# If GOOGLE_API_KEY is missing, this might also throw, but let's assume it's set for now.
try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
except Exception as e:
    logger.warning(f"Failed to init Gemini: {e}")
    embeddings = None
    llm = None

class RAGService:
    def __init__(self):
        if not supabase:
            logger.warning("Supabase client not initialized. RAG service will fail.")
        
        if not embeddings:
            logger.warning("Embeddings model not initialized. RAG service will fail.")
            self.vector_store = None
            return

        self.vector_store = SupabaseVectorStore(
            client=supabase,
            embedding=embeddings,
            table_name="documents",
            query_name="match_documents",
        )

    async def ingest_text(self, text: str, meta: Dict[str, Any] = {}):
        """
        Chunk text and store in Supabase Vector Store
        """
        logger.info(f"Ingesting text... {meta}")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        docs = text_splitter.create_documents([text], metadatas=[meta])
        
        # Store in Supabase
        # Store in Supabase
        if self.vector_store:
            # Type guard for linter
            vs = self.vector_store
            vs.add_documents(docs)
            logger.info(f"Ingested {len(docs)} chunks.")
            return len(docs)
        return 0

    async def ingest_file(self, file: UploadFile):
        """
        Process uploaded file (PDF/TXT) and ingest
        """
        logger.info(f"Processing file: {file.filename}")
        
        # Save temp file using tempfile for cross-platform compatibility
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
            
        try:
            # Load
            if file.filename.lower().endswith(".pdf"):
                loader = PyPDFLoader(temp_path)
            else:
                loader = TextLoader(temp_path)
            
            raw_docs = loader.load()
            
            # Split
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            docs = text_splitter.split_documents(raw_docs)
            
            # Add metadata
            for doc in docs:
                doc.metadata["source"] = file.filename
                
            # Store
            if self.vector_store:
                vs = self.vector_store
                vs.add_documents(docs)
                logger.info(f"Ingested {len(docs)} chunks from {file.filename}")
                return len(docs)
            return 0
            
        except Exception as e:
            logger.error(f"Error ingesting file: {e}")
            raise e
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def query(self, question: str):
        """
        RAG Query
        """
        logger.info(f"Querying: {question}")
        
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
        
        template = """Answer the question based only on the following context:
        {context}

        Question: {question}
        """
        prompt = ChatPromptTemplate.from_template(template)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            RunnableParallel({"context": retriever | format_docs, "question": RunnablePassthrough()})
            | prompt
            | llm
            | StrOutputParser()
        )

        return rag_chain.stream(question)

rag_service = RAGService()

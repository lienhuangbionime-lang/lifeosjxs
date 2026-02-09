from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.services.memory_service import memory_service

router = APIRouter()

class MemoryRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = {}

class MemoryResponse(BaseModel):
    status: str
    message: str

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str
    context: List[Dict[str, Any]]

@router.post("/remember", response_model=MemoryResponse)
async def remember(request: MemoryRequest):
    """
    Manually ingest a unified memory.
    """
    try:
        success = await memory_service.save_memory(request.content, request.metadata)
        if success:
            return {"status": "success", "message": "Memory stored successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to store memory.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    RAG Endpoint: Search memory + Generate Answer
    """
    # 1. Search
    context_docs = await memory_service.search_memory(request.query)
    
    # 2. Extract Text Context
    context_text = "\n\n".join([doc['content'] for doc in context_docs])
    
    # 3. Generate (Using LangChain ChatOpenAI from svc or direct here)
    # For now, let's reuse the LLM from rag_service or simple new instance
    # To keep it clean, let's just use langchain direct here or import from a shared place
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    template = """You are Cortex, the second brain of LifeOS. 
    Answer the user's question based ONLY on the following context from their life.
    If the context doesn't cover it, say "I don't recall that in our records."
    
    Context:
    {context}
    
    User Question: {question}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    
    answer = await chain.ainvoke({"context": context_text, "question": request.query})
    
    return {
        "answer": answer,
        "context": context_docs
    }

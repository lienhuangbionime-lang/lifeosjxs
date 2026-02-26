import asyncio
import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import CrossEncoder

# Add parent directory to path to allow importing app modules if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configuration
# Explicitly look for .env in the parent directory if not found in current (tools/)
if not os.getenv("SUPABASE_URL"):
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# Using a lightweight but powerful reranker model from Hugging Face
# BAAI/bge-reranker-v2-m3 is state-of-the-art for multilingual retrieval
RERANKER_MODEL_ID = "BAAI/bge-reranker-v2-m3"

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] Missing SUPABASE_URL or SUPABASE_KEY in .env")
    sys.exit(1)

async def fetch_candidate_memories(supabase: Client, query_text: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Simulates the initial retrieval step. 
    In a real scenario, this would use vector search (rpc 'match_memories').
    Here we use a simple text search to get a mix of relevant and irrelevant results for demonstration.
    """
    print(f"[INFO] Fetching candidates for query: '{query_text}'...")
    
    try:
        # We fetch more candidates than we need, to let the Reranker filter them
        # Using simple 'ilike' for demo purposes since we might not have local embedding running
        # Split by space to get first keyword for search
        keyword = query_text.split()[0] if query_text else ""
        response = supabase.table("memories") \
            .select("id, content, created_at, tags") \
            .ilike("content", f"%{keyword}%") \
            .limit(limit) \
            .execute()
        
        data = response.data
        print(f"[INFO] Found {len(data)} candidate memories via simple search.")
        return data
    except Exception as e:
        print(f"[ERROR] Supabase fetch failed: {e}")
        return []

def rerank_memories(query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Uses Hugging Face Cross-Encoder to verify relevance.
    This acts as a 'Judge' to score how actually relevant a memory is to the query.
    """
    print(f"[INFO] Loading Hugging Face model: {RERANKER_MODEL_ID}...")
    try:
        # CrossEncoder download might take time on first run
        model = CrossEncoder(RERANKER_MODEL_ID)
        
        # Prepare pairs for the model: [ (Query, Doc1), (Query, Doc2), ... ]
        # We use the 'content' field for comparison
        pairs = [[query, doc["content"]] for doc in documents]
        
        print("[INFO] Reranking candidates...")
        scores = model.predict(pairs)
        
        # Attach score to document and sort
        ranked_results = []
        for i, doc in enumerate(documents):
            doc["_rerank_score"] = float(scores[i]) # Convert numpy float to python float
            ranked_results.append(doc)
            
        # Sort by score descending (Higher is better)
        ranked_results.sort(key=lambda x: x["_rerank_score"], reverse=True)
        
        return ranked_results
    except Exception as e:
        print(f"[ERROR] Reranking failed: {e}")
        return documents

async def main():
    print("[START] LifeOS RAG Reranker Experiment (v3.7.4)")
    
    # Initialize Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Define a test query that implies specific intent
    # Try changing this to something specific in your diary like "Project X architecture"
    test_query = "LifeOS 系統架構設計" 
    
    # 2. Get Candidates (Simulating the 'Recall' phase)
    candidates = await fetch_candidate_memories(supabase, test_query, limit=10)
    
    if not candidates:
        print("[WARN] No memories found in Supabase containing the keywords.")
        print("[INFO] Falling back to generic query to test Reranker logic...")
        # Try a more common keyword if the specific one fails
        candidates = await fetch_candidate_memories(supabase, "LifeOS", limit=10)
        if not candidates:
             print("[ERROR] Database empty or query returned zero results.")
             return

    print("\n--- [Phase 1: Initial Retrieval Order] ---")
    for i, doc in enumerate(candidates[:5]):
        print(f"{i+1}. {doc['content'][:60]}...")

    # 3. Rerank (The 'Precision' phase using HF)
    ranked_memories = rerank_memories(test_query, candidates)
    
    print("\n--- [Phase 2: Hugging Face Refined Order] ---")
    for i, doc in enumerate(ranked_memories[:5]):
        score = doc['_rerank_score']
        # Sigmoid-like interpretation: >0 is positive correlation, <0 is negative
        relevance = "HIGH" if score > 0 else "LOW" 
        print(f"{i+1}. [{relevance} | Score: {score:.2f}] {doc['content'][:60]}...")

    print("\n[SUCCESS] Experiment Complete. This logic is ready for 'app/services/rag.py'.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())


import os
from typing import List, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment
load_dotenv()

class VectorEngine:
    """
    Handles all vector operations: Embedding Generation & Similarity Search.
    Uses Google GenAI (Gemini) for embeddings.
    """
    
    def __init__(self):
        # Try GEMINI_API_KEY first (from .env), then GOOGLE_API_KEY
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            print("[WARN] GEMINI_API_KEY not found. Vector operations will fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
            
        self.model = "text-embedding-004"

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generates a 768-dimensional embedding for the given text.
        """
        if not self.client or not text:
            return None

        try:
            # New GenAI SDK syntax
            result = self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=3072)
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"[ERROR] Embedding generation failed: {e}")
            return None

    def search_memories(self, supabase_client, query_text: str, limit: int = 10, match_threshold: float = 0.5):
        """
        Performs a semantic search on the 'memories' table.
        Requires 'match_memories' function in Supabase (we will create this via migration if needed, 
        but for now we assume standard pgvector select or rpc).
        
        Since we might not have a dedicated RPC yet, we'll try to use the direct filter if user has set it up,
        otherwise we gracefully warn.
        
        Actually, standard Supabase vector search usually requires an RPC function 'match_documents' or similar.
        Let's try to call a standard one or just return empty if not set up.
        """
        query_embedding = self.get_embedding(query_text)
        if not query_embedding:
            return []

        try:
            # RPC call to 'match_memories' provided by pgvector setup
            # We will define this function in the migration if it doesn't exist.
            # For now, let's write the code assuming it exists.
            response = supabase_client.rpc(
                'match_memories',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': match_threshold,
                    'match_count': limit
                }
            ).execute()
            
            return response.data
        except Exception as e:
            print(f"[WARN] Vector search failed (RPC missing?): {e}")
            return []

# Singleton instance
vector_engine = VectorEngine()

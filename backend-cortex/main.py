import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Map GEMINI_API_KEY to GOOGLE_API_KEY for LangChain if missing
gemini_key = os.getenv("GEMINI_API_KEY")
if not os.getenv("GOOGLE_API_KEY") and gemini_key:
    os.environ["GOOGLE_API_KEY"] = gemini_key

# Routers
from app.api.v1 import ingest as ingest_router_mod
from app.api.v1 import chat as chat_router_mod
from app.api.v1 import brain as brain_router_mod
from app.api.v1 import memories as memories_router_mod
from app.api.v1 import system as system_router_mod
from app.api.v1 import projects as projects_router_mod
from app.api.v1 import url_fetch as url_fetch_router_mod
from app.api.v1 import crystallize as crystallize_router_mod
from app.api.v1 import tasks as tasks_router_mod
from app.api.v1 import subconscious as subconscious_router_mod
from app.api.v1 import growth as growth_router_mod
from app.api.v1 import radar as radar_router_mod
from app.api.v1 import enav as enav_router_mod
from app.api.v1 import webhook
from app.core.scheduler import subconscious_scheduler

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cortex.main")
logging.getLogger("httpx").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🧠 Cortex is waking up...")
    try:
        subconscious_scheduler.start_scheduler()
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
    yield
    # Shutdown
    logger.info("💤 Cortex is sleeping...")
    try:
        subconscious_scheduler.stop_scheduler()
    except Exception as e:
        logger.error(f"Scheduler shutdown error: {e}")

app = FastAPI(
    title="LifeOS Cortex v7.1",
    version="7.1.0",
    lifespan=lifespan,
    redirect_slashes=False
)

# CORS
raw_origins = os.getenv("ALLOWED_ORIGINS", "")
env_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

# Core White-list
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://lifeosjxs.vercel.app",
    "https://lifeosjxs.vercel.app/",
]

# Support for Dynamic Vercel Previews and Local IPs
# We use allow_origin_regex for more complex patterns if needed, but for now, 
# we'll add the most common Vercel preview pattern.
if env_origins:
    origins.extend(env_origins)
    logger.info(f"CORS origins extended with: {env_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("DEBUG_MODE") == "True" else origins,
    allow_origin_regex="https://lifeosjxs-.*\.vercel\.app" if os.getenv("DEBUG_MODE") != "True" else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-Supabase-URL", "X-Supabase-Key", "X-Gemini-Key", "x-supabase-url", "x-supabase-key"],
)

# Include Routers
app.include_router(ingest_router_mod.router, prefix="/api/v1/ingest", tags=["Ingest"])
app.include_router(webhook.router, prefix="/api", tags=["webhook"])
app.include_router(chat_router_mod.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(brain_router_mod.router, prefix="/api/v1/brain", tags=["Brain"])
app.include_router(memories_router_mod.router, prefix="/api/v1/memories", tags=["Memories"])
app.include_router(system_router_mod.router, prefix="/api/v1/system", tags=["System"])
app.include_router(projects_router_mod.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(url_fetch_router_mod.router, prefix="/api/v1/url", tags=["Tool"])
app.include_router(crystallize_router_mod.router, prefix="/api/v1/brain", tags=["Brain"])
app.include_router(tasks_router_mod.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(subconscious_router_mod.router, prefix="/api/v1/subconscious", tags=["Subconscious"])
app.include_router(radar_router_mod.router, prefix="/api/v1/radar", tags=["Radar"])
app.include_router(growth_router_mod.router, prefix="/api/v1/growth", tags=["Growth"])
app.include_router(enav_router_mod.router, prefix="/api/v1/enav", tags=["E-Nav"])

# Root Route
@app.get("/")
def root():
    return {
        "status": "online",
        "system": "LifeOS v7.1 Refined Core: Actionable Intelligence",
        "cortex": "Active"
    }

@app.get("/api/health")
async def health_check():
    """
    [v7.1] Comprehensive System Diagnostic.
    Checks Supabase, Gemini API, and Reranker status.
    """
    from app.core.database import supabase
    from app.core.gemini import gemini_client
    import httpx
    
    health = {
        "status": "healthy",
        "version": "7.1.0",
        "services": {}
    }
    
    # 1. Check Supabase
    try:
        if supabase:
            # Check for memories count to verify table access
            res = supabase.table("memories").select("id", count="exact").limit(1).execute()
            health["services"]["database"] = {"status": "connected", "memories": res.count}
        else:
            health["services"]["database"] = {"status": "unconfigured"}
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["database"] = {"status": "error", "message": str(e)}
        health["status"] = "degraded"

    # 2. Check Gemini
    try:
        if gemini_key:
            health["services"]["gemini"] = {"status": "configured"}
        else:
            health["services"]["gemini"] = {"status": "missing_key"}
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["gemini"] = {"status": "error", "message": str(e)}

    # 3. Check Reranker
    reranker_url = os.getenv("RERANKER_SERVICE_URL", "http://localhost:8001")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{reranker_url}/", timeout=2.0)
            if resp.status_code == 200:
                health["services"]["reranker"] = {"status": "online", "url": reranker_url}
            else:
                health["services"]["reranker"] = {"status": "unreachable", "code": resp.status_code}
    except Exception:
        health["services"]["reranker"] = {"status": "offline", "url": reranker_url}

    return health

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, log_level="info")
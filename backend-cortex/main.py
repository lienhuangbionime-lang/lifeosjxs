import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Map GEMINI_API_KEY to GOOGLE_API_KEY for LangChain if missing
gemini_key = os.getenv("GEMINI_API_KEY")
if not os.getenv("GOOGLE_API_KEY") and gemini_key:
    os.environ["GOOGLE_API_KEY"] = gemini_key

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# Routers
from app.api.v1 import ingest as ingest_router_mod
from app.api.v1 import chat as chat_router_mod
from app.api.v1 import brain as brain_router_mod
from app.api.v1 import memories as memories_router_mod
from app.api.v1 import system as system_router_mod
from app.api.v1 import analyze as analyze_router_mod
from app.api.v1.endpoints import projects as projects_router_mod
from app.api.v1 import url_fetch as url_fetch_router_mod
from app.api.v1 import crystallize as crystallize_router_mod
from app.api.v1 import tasks as tasks_router_mod
from app.api.v1 import subconscious as subconscious_router_mod
from app.api.v1 import growth as growth_router_mod
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
    title="LifeOS Cortex v3.1",
    version="3.1.0",
    lifespan=lifespan
)

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://lifeosjxs.vercel.app",      # Vercel Production
    "https://lifeosjxs.vercel.app/",     # Vercel Production (trailing slash safety)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(ingest_router_mod.router, prefix="/api/v1/ingest", tags=["Ingest"])
app.include_router(chat_router_mod.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(brain_router_mod.router, prefix="/api/v1/brain", tags=["Brain"])
app.include_router(memories_router_mod.router, prefix="/api/v1/memories", tags=["Memories"])
app.include_router(system_router_mod.router, prefix="/api/v1/system", tags=["System"])
app.include_router(analyze_router_mod.router, prefix="/api/v1/analyze", tags=["Analyze"])
app.include_router(projects_router_mod.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(url_fetch_router_mod.router, prefix="/api/v1/url", tags=["Tool"])
app.include_router(crystallize_router_mod.router, prefix="/api/v1/brain", tags=["Brain"]) # Same prefix as brain for now or specialized
app.include_router(tasks_router_mod.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(subconscious_router_mod.router, prefix="/api/v1/subconscious", tags=["Subconscious"])
app.include_router(growth_router_mod.router, prefix="/api/v1/growth", tags=["Growth"])


# 根路徑檢查
@app.get("/")
def root():
    return {
        "status": "online",
        "system": "LifeOS v3.1 Autopoiesis",
        "cortex": "Active"
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000)) # Default to 8000 for local proxy
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, log_level="info")
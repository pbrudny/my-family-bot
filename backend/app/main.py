import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import settings
from app.db.neo4j_client import close_driver, init_driver
from app.routers import admin, chat, whatsapp

STATIC_DIR = Path("/app/static")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — connecting to Neo4j")
    await init_driver()
    yield
    logger.info("Shutting down — closing Neo4j driver")
    await close_driver()


app = FastAPI(
    title="Family Tree AI Assistant",
    description="Ask questions about your family tree in Polish, Czech or English.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(whatsapp.router)
app.include_router(admin.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str) -> FileResponse:
    """Serve the React SPA: return the requested file or fall back to index.html."""
    if not STATIC_DIR.exists():
        raise HTTPException(status_code=404)
    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    index = STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(status_code=404)

"""
SentinelAI — FastAPI Application Entry Point

This is the main application module that:
- Initialises the FastAPI app with metadata
- Configures CORS for frontend communication
- Registers all API routers
- Sets up the SQLite database on startup
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db, get_user_by_username, create_user
from app.routers import text_detection, image_detection, document_detection, audit
from app.routers import auth as auth_router
from app.routers import cases as cases_router
from app.routers import clients as clients_router
from app.routers import analytics as analytics_router
from app.services.model_loader import load_models, models_available
from app.services.llm_service import check_ollama_health, close_client
from app.services.auth import hash_password

logger = logging.getLogger(__name__)


# ── Lifespan: runs once on startup / shutdown ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise resources on startup and clean up on shutdown."""
    await init_db()
    load_models()          # Load ML models into memory

    # Seed default admin user if none exists
    existing = await get_user_by_username("admin")
    if not existing:
        await create_user("admin", hash_password("sentinel"), "admin", "System Administrator")
        logger.info("Seeded default admin user (admin / sentinel)")

    yield  # application runs here
    await close_client()   # Clean up HTTP clients


# ── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(
    title="SentinelAI",
    description="AI-Generated Fraud Detection API for Banking",
    version="1.0.0",
    lifespan=lifespan,
)


# ── CORS Configuration ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js dev server
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routers ──────────────────────────────────────────────────────
app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(text_detection.router, prefix="/analyze", tags=["Text Detection"])
app.include_router(image_detection.router, prefix="/analyze", tags=["Image Detection"])
app.include_router(document_detection.router, prefix="/analyze", tags=["Document Detection"])
app.include_router(audit.router, prefix="/audit", tags=["Audit Log"])
app.include_router(cases_router.router, prefix="/cases", tags=["Case Management"])
app.include_router(clients_router.router, prefix="/clients", tags=["Client Management"])
app.include_router(analytics_router.router, prefix="/analytics", tags=["Analytics"])


# ── Health Check ───────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """Health check with model and LLM status."""
    ollama_ok = await check_ollama_health()
    return {
        "status": "healthy",
        "service": "SentinelAI",
        "version": "1.0.0",
        "models": models_available(),
        "ollama": ollama_ok,
    }

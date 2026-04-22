"""
FastAPI application factory and configuration.

This module sets up the FastAPI application with:
- Lifespan events for startup/shutdown
- CORS middleware for frontend communication
- API routers for modular endpoint organization
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api import auth, chat, knowledge, actions, admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== DATABASE INITIALIZATION ====================
# Initialize database tables BEFORE starting the app
logger.info("🚀 Initializing Database...")
try:
    from app.core.init_db import init_database
    init_database()
except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    
    Startup: Initialize critical resources (FAISS index, connections)
    Shutdown: Clean up resources (save indices, close connections)
    """
    logger.info("🚀 Starting AI Sales Assistant...")
    yield
    # Shutdown logic: Save FAISS indices, close DB connections
    logger.info("👋 Shutting down...")


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="RAG-powered AI Sales Assistant with multi-tenant support",
    lifespan=lifespan
)

# ==================== CORS Configuration ====================
# Allow frontend and local development, but restrict in production
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS_STR.split(',') if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",  # Allow local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== API Routes ====================
# Modular endpoint organization by feature
app.include_router(auth.router)          # Authentication & JWT tokens
app.include_router(chat.router)           # Conversations & messages
app.include_router(knowledge.router)      # Knowledge base management
app.include_router(actions.router, prefix="/actions")  # Custom actions
app.include_router(admin.router)          # Admin operations


@app.get("/")
async def root():
    """Root endpoint - returns API metadata"""
    return {
        "message": "AI Sales Assistant API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint - used by load balancers and monitoring"""
    return {"status": "healthy"}

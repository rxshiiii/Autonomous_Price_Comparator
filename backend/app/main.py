"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print("🚀 Starting up Autonomous Price Comparator API...")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️  Database: {settings.DATABASE_URL}")

    yield

    # Shutdown
    print("👋 Shutting down Autonomous Price Comparator API...")


# Create FastAPI app
app = FastAPI(
    title="Autonomous Price Comparator API",
    description="AI-powered price comparison platform with personalized recommendations",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "message": "Welcome to Autonomous Price Comparator API",
        "version": "0.1.0",
        "status": "running",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


# Include API v1 routes
app.include_router(api_router, prefix="/api/v1")

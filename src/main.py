"""FastAPI application main entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from src.config import settings, get_logger
from src.database import init_db

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Blog Post Scraper",
    description="Web scraper for blog posts with pagination and rate limiting",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("Application starting up")
    await init_db()
    logger.info("Database initialized")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "blog-post-scraper"}


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": str(exc)}
    )


@app.exception_handler(500)
async def server_error_handler(request, exc):
    """Handle 500 errors."""
    logger.error("Server error", error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .api.routes import router, set_scheduler_service
from .services.scheduler import SchedulerService
from .config import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scheduler service
scheduler_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global scheduler_service
    
    # Startup
    logger.info("Starting AI Stock Dashboard backend...")
    scheduler_service = SchedulerService()
    set_scheduler_service(scheduler_service)
    scheduler_service.start()
    logger.info("Backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down backend...")
    if scheduler_service:
        scheduler_service.stop()
    logger.info("Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Stock Dashboard",
    description="AI-powered stock analysis dashboard with periodic updates",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Stock Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/status"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "AI Stock Dashboard backend is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
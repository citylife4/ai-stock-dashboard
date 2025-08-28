from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .api.routes import router, set_scheduler_service
from .api.admin_routes import router as admin_router
from .api.user_routes import router as user_router
from .services.scheduler import SchedulerService
from .config import config
from .database import connect_to_mongo, close_mongo_connection

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
    
    # Connect to database
    await connect_to_mongo()
    
    # Ensure admin user exists
    from .services.user_service import UserService
    user_service = UserService()
    await user_service.ensure_admin_user_exists(
        username=config.ADMIN_USERNAME,
        email=f"{config.ADMIN_USERNAME}@admin.local",
        password=config.ADMIN_PASSWORD
    )
    
    scheduler_service = SchedulerService()
    set_scheduler_service(scheduler_service)
    scheduler_service.start()
    logger.info("Backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down backend...")
    if scheduler_service:
        scheduler_service.stop()
    
    # Close database connection
    await close_mongo_connection()
    logger.info("Backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="AI Stock Dashboard",
    description="AI-powered stock analysis dashboard with user management and multi-AI analysis",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Stock Dashboard API",
        "version": "2.0.0",
        "features": [
            "User Management",
            "Subscription Tiers",
            "Multi-AI Analysis",
            "Per-user Stock Tracking"
        ],
        "docs": "/docs",
        "health": "/api/v1/status"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from .database import is_database_available
    return {
        "status": "healthy", 
        "message": "AI Stock Dashboard backend is running",
        "database": "connected" if is_database_available() else "not available"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError
import logging
from .config import config

logger = logging.getLogger(__name__)

# Global database connection
client = None
database = None

async def connect_to_mongo():
    """Create database connection."""
    global client, database
    try:
        # Use environment variable or default to local MongoDB
        mongo_url = config.MONGODB_URL or "mongodb://localhost:27017"
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
        
        # Test the connection
        await client.admin.command('ping')
        database = client[config.DATABASE_NAME or "ai_stock_dashboard"]
        
        # Create indexes for performance
        await create_indexes()
        
        logger.info(f"Connected to MongoDB at {mongo_url}")
        
    except ServerSelectionTimeoutError:
        logger.warning("MongoDB not available, using in-memory storage")
        client = None
        database = None
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        client = None
        database = None

async def close_mongo_connection():
    """Close database connection."""
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")

async def create_indexes():
    """Create database indexes for performance."""
    if not database:
        return
    
    try:
        # User indexes
        await database.users.create_index("email", unique=True)
        await database.users.create_index("username", unique=True)
        
        # Stock indexes
        await database.stocks.create_index("symbol")
        await database.stocks.create_index("last_updated")
        
        # User stocks indexes
        await database.user_stocks.create_index([("user_id", 1), ("symbol", 1)], unique=True)
        await database.user_stocks.create_index("user_id")
        await database.user_stocks.create_index("symbol")
        
        # AI analysis indexes
        await database.ai_analyses.create_index([("symbol", 1), ("ai_model", 1), ("timestamp", -1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

def get_database():
    """Get database instance."""
    return database

def is_database_available():
    """Check if database is available."""
    return database is not None
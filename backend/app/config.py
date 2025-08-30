import os
import asyncio
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Alpha Vantage Configuration (fallback from environment)
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    # Polygon.io Configuration (fallback from environment)
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    
    # Server Configuration
    HOST = os.getenv("HOST", "localhost")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    # Admin Configuration
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Database Configuration
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_stock_dashboard")
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    # Scheduler settings (in minutes)
    UPDATE_INTERVAL = 30  # Update every 30 minutes
    
    # Admin config service will be initialized later to avoid circular imports
    _admin_config_service = None
    
    @classmethod
    def set_admin_config_service(cls, service):
        """Set the admin config service instance."""
        cls._admin_config_service = service
    
    @classmethod
    async def get_admin_config_service(cls):
        """Get or create admin config service."""
        if cls._admin_config_service is None:
            from .services.admin_config_service import AdminConfigService
            from .database import get_database
            
            cls._admin_config_service = AdminConfigService()
            cls._admin_config_service.set_database(get_database())
        
        return cls._admin_config_service
    
    # MongoDB-based configuration methods
    @classmethod
    async def get_config(cls):
        """Get admin configuration from MongoDB."""
        service = await cls.get_admin_config_service()
        return await service.get_config()
    
    @classmethod
    def get_stock_symbols(cls) -> List[str]:
        """Get current stock symbols from MongoDB config."""
        try:
            loop = asyncio.get_event_loop()
            config_data = loop.run_until_complete(cls.get_config())
            return config_data.stock_symbols
        except:
            # Fallback to default symbols
            return ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]
    
    @classmethod
    def get_ai_analysis_prompt(cls) -> str:
        """Get current AI analysis prompt from MongoDB config."""
        try:
            loop = asyncio.get_event_loop()
            config_data = loop.run_until_complete(cls.get_config())
            return config_data.ai_analysis_prompt
        except:
            return "Default analysis prompt"
    
    @classmethod
    async def update_stock_symbols(cls, symbols: List[str]) -> bool:
        """Update stock symbols in MongoDB config."""
        service = await cls.get_admin_config_service()
        return await service.update_stock_symbols(symbols)
    
    @classmethod
    async def update_ai_analysis_prompt(cls, prompt: str) -> bool:
        """Update AI analysis prompt in MongoDB config."""
        service = await cls.get_admin_config_service()
        return await service.update_ai_analysis_prompt(prompt)
    
    @classmethod
    def get_data_source(cls) -> str:
        """Get current data source from MongoDB config."""
        try:
            loop = asyncio.get_event_loop()
            config_data = loop.run_until_complete(cls.get_config())
            return config_data.data_source
        except:
            return "yahoo"
    
    @classmethod
    def get_alpha_vantage_api_key(cls) -> str:
        """Get Alpha Vantage API key from MongoDB config or environment."""
        try:
            loop = asyncio.get_event_loop()
            config_data = loop.run_until_complete(cls.get_config())
            return config_data.alpha_vantage_api_key or cls.ALPHA_VANTAGE_API_KEY or ""
        except:
            return cls.ALPHA_VANTAGE_API_KEY or ""
    
    @classmethod
    async def update_data_source(cls, data_source: str) -> bool:
        """Update data source in MongoDB config."""
        service = await cls.get_admin_config_service()
        return await service.update_data_source(data_source)
    
    @classmethod
    async def update_alpha_vantage_api_key(cls, api_key: str) -> bool:
        """Update Alpha Vantage API key in MongoDB config."""
        service = await cls.get_admin_config_service()
        return await service.update_alpha_vantage_api_key(api_key)
    
    @classmethod
    def get_polygon_api_key(cls) -> str:
        """Get Polygon.io API key from MongoDB config or environment."""
        try:
            loop = asyncio.get_event_loop()
            config_data = loop.run_until_complete(cls.get_config())
            return config_data.polygon_api_key or cls.POLYGON_API_KEY or ""
        except:
            return cls.POLYGON_API_KEY or ""
    
    @classmethod
    async def update_polygon_api_key(cls, api_key: str) -> bool:
        """Update Polygon.io API key in MongoDB config."""
        service = await cls.get_admin_config_service()
        return await service.update_polygon_api_key(api_key)
    
    @classmethod
    def get_ai_provider(cls) -> str:
        """Get AI provider from MongoDB config."""
        try:
            loop = asyncio.get_event_loop()
            config_data = loop.run_until_complete(cls.get_config())
            return config_data.ai_provider
        except:
            return "openai"
    
    @classmethod
    def get_ai_model(cls) -> str:
        """Get AI model from MongoDB config."""
        try:
            loop = asyncio.get_event_loop()
            config_data = loop.run_until_complete(cls.get_config())
            return config_data.ai_model
        except:
            return "gpt-3.5-turbo"
    
    @classmethod
    async def update_ai_provider(cls, provider: str) -> bool:
        """Update AI provider in MongoDB config."""
        service = await cls.get_admin_config_service()
        return await service.update_ai_provider(provider)
    
    @classmethod
    async def update_ai_model(cls, model: str) -> bool:
        """Update AI model in MongoDB config."""
        service = await cls.get_admin_config_service()
        return await service.update_ai_model(model)


config = Config()
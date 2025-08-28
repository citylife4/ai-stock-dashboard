import os
import json
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
    
    # Stock symbols to analyze (default values)
    _DEFAULT_STOCK_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]
    
    # Scheduler settings (in minutes)
    UPDATE_INTERVAL = 30  # Update every 30 minutes
    
    # Default AI Analysis prompt
    _DEFAULT_AI_ANALYSIS_PROMPT = """
    Analyze the following stock data and provide:
    1. A score from 0-100 (100 being the best investment opportunity)
    2. A brief reason for the score (2-3 sentences)
    
    Consider factors like:
    - Recent price performance
    - Trading volume
    - Market cap
    - General market sentiment for the sector
    
    Stock Data:
    Symbol: {symbol}
    Current Price: ${current_price}
    Previous Close: ${previous_close}
    Daily Change: {change_percent}%
    Volume: {volume}
    Market Cap: ${market_cap}
    
    Respond in JSON format:
    {{"score": <number>, "reason": "<explanation>"}}
    """
    
    # Configuration file path
    CONFIG_FILE = "admin_config.json"
    
    @classmethod
    def load_dynamic_config(cls):
        """Load dynamic configuration from file."""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                with open(cls.CONFIG_FILE, 'r') as f:
                    config_data = json.load(f)
                    return config_data
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Return default configuration
        return {
            "stock_symbols": cls._DEFAULT_STOCK_SYMBOLS,
            "ai_analysis_prompt": cls._DEFAULT_AI_ANALYSIS_PROMPT.strip(),
            "data_source": "yahoo",  # Default to Yahoo Finance
            "alpha_vantage_api_key": cls.ALPHA_VANTAGE_API_KEY or "",
            "polygon_api_key": cls.POLYGON_API_KEY or "",
            "ai_provider": "openai",  # Default AI provider
            "ai_model": "gpt-3.5-turbo"  # Default AI model
        }
    
    @classmethod
    def save_dynamic_config(cls, config_data):
        """Save dynamic configuration to file."""
        try:
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    @classmethod
    def get_stock_symbols(cls) -> List[str]:
        """Get current stock symbols from dynamic config."""
        config_data = cls.load_dynamic_config()
        return config_data.get("stock_symbols", cls._DEFAULT_STOCK_SYMBOLS)
    
    @classmethod
    def get_ai_analysis_prompt(cls) -> str:
        """Get current AI analysis prompt from dynamic config."""
        config_data = cls.load_dynamic_config()
        return config_data.get("ai_analysis_prompt", cls._DEFAULT_AI_ANALYSIS_PROMPT.strip())
    
    @classmethod
    def update_stock_symbols(cls, symbols: List[str]) -> bool:
        """Update stock symbols in dynamic config."""
        config_data = cls.load_dynamic_config()
        config_data["stock_symbols"] = symbols
        return cls.save_dynamic_config(config_data)
    
    @classmethod
    def update_ai_analysis_prompt(cls, prompt: str) -> bool:
        """Update AI analysis prompt in dynamic config."""
        config_data = cls.load_dynamic_config()
        config_data["ai_analysis_prompt"] = prompt
        return cls.save_dynamic_config(config_data)
    
    @classmethod
    def get_data_source(cls) -> str:
        """Get current data source from dynamic config."""
        config_data = cls.load_dynamic_config()
        return config_data.get("data_source", "yahoo")
    
    @classmethod
    def get_alpha_vantage_api_key(cls) -> str:
        """Get Alpha Vantage API key from dynamic config or environment."""
        config_data = cls.load_dynamic_config()
        return config_data.get("alpha_vantage_api_key") or cls.ALPHA_VANTAGE_API_KEY or ""
    
    @classmethod
    def update_data_source(cls, data_source: str) -> bool:
        """Update data source in dynamic config."""
        if data_source not in ["yahoo", "alpha_vantage", "polygon"]:
            return False
        config_data = cls.load_dynamic_config()
        config_data["data_source"] = data_source
        return cls.save_dynamic_config(config_data)
    
    @classmethod
    def update_alpha_vantage_api_key(cls, api_key: str) -> bool:
        """Update Alpha Vantage API key in dynamic config."""
        config_data = cls.load_dynamic_config()
        config_data["alpha_vantage_api_key"] = api_key
        return cls.save_dynamic_config(config_data)
    
    @classmethod
    def get_polygon_api_key(cls) -> str:
        """Get Polygon.io API key from dynamic config or environment."""
        config_data = cls.load_dynamic_config()
        return config_data.get("polygon_api_key") or cls.POLYGON_API_KEY or ""
    
    @classmethod
    def update_polygon_api_key(cls, api_key: str) -> bool:
        """Update Polygon.io API key in dynamic config."""
        config_data = cls.load_dynamic_config()
        config_data["polygon_api_key"] = api_key
        return cls.save_dynamic_config(config_data)
    
    @classmethod
    def get_ai_provider(cls) -> str:
        """Get AI provider from dynamic config."""
        config_data = cls.load_dynamic_config()
        return config_data.get("ai_provider", "openai")
    
    @classmethod
    def get_ai_model(cls) -> str:
        """Get AI model from dynamic config."""
        config_data = cls.load_dynamic_config()
        return config_data.get("ai_model", "gpt-3.5-turbo")
    
    @classmethod
    def update_ai_provider(cls, provider: str) -> bool:
        """Update AI provider in dynamic config."""
        if provider not in ["openai", "groq"]:
            return False
        config_data = cls.load_dynamic_config()
        config_data["ai_provider"] = provider
        return cls.save_dynamic_config(config_data)
    
    @classmethod
    def update_ai_model(cls, model: str) -> bool:
        """Update AI model in dynamic config."""
        config_data = cls.load_dynamic_config()
        config_data["ai_model"] = model
        return cls.save_dynamic_config(config_data)


config = Config()
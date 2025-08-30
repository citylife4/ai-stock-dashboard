import logging
from typing import Optional, List
from datetime import datetime
from ..models import AdminConfig

logger = logging.getLogger(__name__)

class AdminConfigService:
    def __init__(self, db=None):
        self.db = db
    
    def set_database(self, db):
        """Set the database connection."""
        self.db = db
    
    async def get_config(self) -> AdminConfig:
        """Get admin configuration from MongoDB."""
        if self.db is None:
            return self._get_default_config()
        
        try:
            config_doc = await self.db.admin_config.find_one()
            if config_doc:
                # Convert MongoDB document to AdminConfig
                return AdminConfig(**config_doc)
            else:
                # Create default config if none exists
                default_config = self._get_default_config()
                await self.create_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error getting admin config: {e}")
            return self._get_default_config()
    
    async def create_config(self, config: AdminConfig) -> bool:
        """Create initial admin configuration."""
        if self.db is None:
            return False
        
        try:
            config_dict = config.dict(exclude={"id"})
            config_dict["created_at"] = datetime.utcnow()
            config_dict["updated_at"] = datetime.utcnow()
            
            result = await self.db.admin_config.insert_one(config_dict)
            return result.inserted_id is not None
        except Exception as e:
            logger.error(f"Error creating admin config: {e}")
            return False
    
    async def update_config(self, updates: dict) -> bool:
        """Update admin configuration in MongoDB."""
        if self.db is None:
            return False
        
        try:
            # Ensure config exists
            await self.get_config()
            
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.db.admin_config.update_one(
                {},  # Update the single config document
                {"$set": updates},
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            logger.error(f"Error updating admin config: {e}")
            return False
    
    async def update_stock_symbols(self, symbols: List[str]) -> bool:
        """Update stock symbols."""
        return await self.update_config({"stock_symbols": symbols})
    
    async def update_ai_analysis_prompt(self, prompt: str) -> bool:
        """Update AI analysis prompt."""
        return await self.update_config({"ai_analysis_prompt": prompt})
    
    async def update_data_source(self, data_source: str) -> bool:
        """Update data source."""
        if data_source not in ["yahoo", "alpha_vantage", "polygon"]:
            return False
        return await self.update_config({"data_source": data_source})
    
    async def update_alpha_vantage_api_key(self, api_key: str) -> bool:
        """Update Alpha Vantage API key."""
        return await self.update_config({"alpha_vantage_api_key": api_key})
    
    async def update_polygon_api_key(self, api_key: str) -> bool:
        """Update Polygon.io API key."""
        return await self.update_config({"polygon_api_key": api_key})
    
    async def update_ai_provider(self, provider: str) -> bool:
        """Update AI provider."""
        if provider not in ["openai", "groq"]:
            return False
        return await self.update_config({"ai_provider": provider})
    
    async def update_ai_model(self, model: str) -> bool:
        """Update AI model."""
        return await self.update_config({"ai_model": model})
    
    def _get_default_config(self) -> AdminConfig:
        """Get default configuration."""
        default_prompt = """
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
        """.strip()
        
        return AdminConfig(
            stock_symbols=["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"],
            ai_analysis_prompt=default_prompt,
            data_source="yahoo",
            alpha_vantage_api_key="",
            polygon_api_key="",
            ai_provider="openai",
            ai_model="gpt-3.5-turbo"
        )

# Service will be initialized with database in main.py

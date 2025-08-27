import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Server Configuration
    HOST = os.getenv("HOST", "localhost")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    
    # Stock symbols to analyze
    STOCK_SYMBOLS = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]
    
    # Scheduler settings (in minutes)
    UPDATE_INTERVAL = 30  # Update every 30 minutes
    
    # AI Analysis prompt
    AI_ANALYSIS_PROMPT = """
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

config = Config()
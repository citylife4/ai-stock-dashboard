from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class StockData(BaseModel):
    symbol: str
    current_price: float
    previous_close: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    last_updated: datetime


class AIAnalysis(BaseModel):
    score: int  # 0-100
    reason: str


class StockAnalysis(BaseModel):
    stock_data: StockData
    ai_analysis: AIAnalysis
    timestamp: datetime


class DashboardResponse(BaseModel):
    stocks: List[StockAnalysis]
    last_updated: datetime
    total_stocks: int
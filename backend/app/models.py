from datetime import datetime
from typing import Optional, List, Dict
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


class ApiError(BaseModel):
    type: str  # "stock_data", "ai_analysis", "general"
    symbol: str
    message: str


class DashboardResponse(BaseModel):
    stocks: List[StockAnalysis]
    last_updated: datetime
    total_stocks: int
    errors: List[ApiError] = []  # Include API errors in dashboard response


# Admin models
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str


class AdminStockRequest(BaseModel):
    symbol: str


class AdminPromptRequest(BaseModel):
    ai_analysis_prompt: Optional[str] = None


class AdminConfigRequest(BaseModel):
    data_source: Optional[str] = None  # "yahoo" or "alpha_vantage"
    alpha_vantage_api_key: Optional[str] = None


class AdminConfigResponse(BaseModel):
    data_source: str
    alpha_vantage_api_key: str


class AdminPromptResponse(BaseModel):
    ai_analysis_prompt: str


class AdminStockListResponse(BaseModel):
    symbols: List[str]


class AdminActionLog(BaseModel):
    timestamp: datetime
    action: str  # "add_stock", "remove_stock", "update_prompt"
    details: str
    admin_user: str
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr
from enum import Enum


# Subscription Tiers
class SubscriptionTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    EXPERT = "expert"


# AI Models
class AIModelType(str, Enum):
    BASIC = "basic"
    WARREN_BUFFET = "warren_buffet"
    PETER_LYNCH = "peter_lynch"
    DCF_MATH = "dcf_math"


# User Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    id: Optional[str] = None
    username: str
    email: EmailStr
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    max_stocks: int = 5
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    is_admin: bool = False


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    subscription_tier: SubscriptionTier
    max_stocks: int
    created_at: datetime
    is_active: bool
    is_admin: bool = False


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class StockData(BaseModel):
    symbol: str
    current_price: float
    previous_close: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    last_updated: datetime


class AIAnalysis(BaseModel):
    ai_model: AIModelType
    score: int  # 0-100
    reason: str


class MultiAIAnalysis(BaseModel):
    analyses: List[AIAnalysis]
    average_score: float
    timestamp: datetime


class StockAnalysis(BaseModel):
    stock_data: StockData
    ai_analysis: MultiAIAnalysis
    timestamp: datetime


class UserStock(BaseModel):
    user_id: str
    symbol: str
    added_at: datetime


class ApiError(BaseModel):
    type: str  # "stock_data", "ai_analysis", "general"
    symbol: str
    message: str


class DashboardResponse(BaseModel):
    stocks: List[StockAnalysis]
    last_updated: datetime
    total_stocks: int
    max_stocks: int
    subscription_tier: SubscriptionTier
    errors: List[ApiError] = []


# Admin models
class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str


class AdminStockRequest(BaseModel):
    symbol: str


class AdminUserUpdate(BaseModel):
    subscription_tier: Optional[SubscriptionTier] = None
    max_stocks: Optional[int] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    subscription_tier: SubscriptionTier
    max_stocks: int
    created_at: datetime
    is_active: bool
    stock_count: int


class AdminPromptRequest(BaseModel):
    ai_analysis_prompt: Optional[str] = None


class AdminConfigRequest(BaseModel):
    data_source: Optional[str] = None  # "yahoo", "alpha_vantage", or "polygon"
    alpha_vantage_api_key: Optional[str] = None
    polygon_api_key: Optional[str] = None
    ai_provider: Optional[str] = None  # "openai" or "groq"
    ai_model: Optional[str] = None


class AdminConfigResponse(BaseModel):
    data_source: str
    alpha_vantage_api_key: str
    polygon_api_key: str
    ai_provider: str
    ai_model: str


class AdminPromptResponse(BaseModel):
    ai_analysis_prompt: str


class AdminStockListResponse(BaseModel):
    symbols: List[str]


class AdminActionLog(BaseModel):
    timestamp: datetime
    action: str  # "add_stock", "remove_stock", "update_prompt", "update_user"
    details: str
    admin_user: str


# Subscription Management
class SubscriptionPlan(BaseModel):
    tier: SubscriptionTier
    name: str
    max_stocks: int
    ai_models: List[AIModelType]
    price_monthly: float
    description: str


class SubscriptionLimits(BaseModel):
    max_stocks: int
    ai_models: List[AIModelType]


# AI Model Configuration
class AIModelConfig(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    model_type: AIModelType
    name: str
    description: str
    prompt_template: str
    subscription_tiers: List[SubscriptionTier]
    is_active: bool = True
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from ..models import (
    UserCreate, UserLogin, LoginResponse, UserResponse, User,
    SubscriptionTier, AdminUserUpdate
)
from ..services.user_service import UserService, UserStockService
from ..services.auth_service import auth_service, get_current_active_user
from ..database import is_database_available
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

user_service = UserService()
user_stock_service = UserStockService()

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user."""
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database not available. User registration requires database connection."
        )
    
    # Check if user already exists
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create user
    user = await user_service.create_user(user_data)
    if not user:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        subscription_tier=user.subscription_tier,
        max_stocks=user.max_stocks,
        created_at=user.created_at,
        is_active=user.is_active
    )

@router.post("/login", response_model=LoginResponse)
async def login_user(login_data: UserLogin):
    """Login user and return access token."""
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database not available. User login requires database connection."
        )
    
    login_response = await auth_service.login(login_data)
    if not login_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return login_response

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        subscription_tier=current_user.subscription_tier,
        max_stocks=current_user.max_stocks,
        created_at=current_user.created_at,
        is_active=current_user.is_active,
        is_admin=getattr(current_user, 'is_admin', False)
    )

@router.post("/stocks/{symbol}")
async def add_user_stock(symbol: str, current_user: User = Depends(get_current_active_user)):
    """Add stock to user's tracking list."""
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    
    success = await user_stock_service.add_user_stock(current_user.id, symbol)
    if not success:
        # Check if it's a limit issue
        current_stocks = await user_stock_service.get_user_stocks(current_user.id)
        if len(current_stocks) >= current_user.max_stocks:
            raise HTTPException(
                status_code=400,
                detail=f"Stock limit reached. Your {current_user.subscription_tier.value} plan allows {current_user.max_stocks} stocks."
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Stock already tracked or failed to add"
            )
    
    return {"message": f"Stock {symbol.upper()} added to tracking list"}

@router.delete("/stocks/{symbol}")
async def remove_user_stock(symbol: str, current_user: User = Depends(get_current_active_user)):
    """Remove stock from user's tracking list."""
    if not is_database_available():
        raise HTTPException(
            status_code=503,
            detail="Database not available"
        )
    
    success = await user_stock_service.remove_user_stock(current_user.id, symbol)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Stock not found in tracking list"
        )
    
    return {"message": f"Stock {symbol.upper()} removed from tracking list"}

@router.get("/stocks")
async def get_user_stocks(current_user: User = Depends(get_current_active_user)):
    """Get user's tracked stocks."""
    if not is_database_available():
        return {"symbols": []}  # Return empty list if no database
    
    stocks = await user_stock_service.get_user_stocks(current_user.id)
    return {"symbols": stocks}
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import List, Optional

from ..models import DashboardResponse, StockAnalysis, ApiError, User
from ..services.scheduler import SchedulerService
from ..services.user_service import UserStockService
from ..services.multi_ai_service import MultiAIService
from ..services.auth_service import auth_service
from ..database import is_database_available
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)  # Don't auto-error so we can handle optional auth

# Global scheduler instance
scheduler_service = None

# Services
user_stock_service = UserStockService()
multi_ai_service = MultiAIService()


def get_scheduler_service() -> SchedulerService:
    """Get the global scheduler service instance."""
    global scheduler_service
    if scheduler_service is None:
        raise HTTPException(status_code=500, detail="Scheduler service not initialized")
    return scheduler_service


def set_scheduler_service(service: SchedulerService):
    """Set the global scheduler service instance."""
    global scheduler_service
    scheduler_service = service


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    if not credentials or not is_database_available():
        return None
    
    try:
        return await auth_service.get_current_user(credentials)
    except HTTPException:
        # Invalid token or user, return None for optional auth
        return None


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: Optional[User] = Depends(get_current_user_optional)):
    """Get the current stock dashboard data."""
    try:
        # If user is not authenticated, return sample/welcome data
        if not current_user or not is_database_available():
            # Return sample data for welcome page
            from ..models import StockData, AIAnalysis, MultiAIAnalysis, StockAnalysis, SubscriptionTier, AIModelType
            
            # Create sample stock data for demonstration
            sample_stocks = [
                StockAnalysis(
                    stock_data=StockData(
                        symbol="AAPL",
                        current_price=175.50,
                        previous_close=173.15,
                        change_percent=1.36,
                        volume=45678900,
                        market_cap=2750000000000,
                        last_updated=datetime.now()
                    ),
                    ai_analysis=MultiAIAnalysis(
                        analyses=[
                            AIAnalysis(
                                ai_model=AIModelType.WARREN_BUFFET,
                                score=85,
                                reason="Strong technology company with solid fundamentals and excellent brand loyalty. High-quality business with durable competitive advantages."
                            ),
                            AIAnalysis(
                                ai_model=AIModelType.PETER_LYNCH,
                                score=82,
                                reason="Growth company with strong innovation pipeline. Excellent management and consistent earnings growth."
                            ),
                            AIAnalysis(
                                ai_model=AIModelType.DCF_MATH,
                                score=88,
                                reason="Strong free cash flow generation and healthy balance sheet. Fair valuation based on discounted cash flow analysis."
                            )
                        ],
                        average_score=85.0,
                        timestamp=datetime.now()
                    ),
                    timestamp=datetime.now()
                ),
                StockAnalysis(
                    stock_data=StockData(
                        symbol="TSLA",
                        current_price=245.80,
                        previous_close=249.00,
                        change_percent=-1.28,
                        volume=67890123,
                        market_cap=780000000000,
                        last_updated=datetime.now()
                    ),
                    ai_analysis=MultiAIAnalysis(
                        analyses=[
                            AIAnalysis(
                                ai_model=AIModelType.WARREN_BUFFET,
                                score=68,
                                reason="High growth potential but significant volatility and competitive risks. Requires careful evaluation of long-term prospects."
                            ),
                            AIAnalysis(
                                ai_model=AIModelType.PETER_LYNCH,
                                score=75,
                                reason="Market leader in EV technology with expanding global presence. High growth story but needs monitoring of execution."
                            ),
                            AIAnalysis(
                                ai_model=AIModelType.DCF_MATH,
                                score=73,
                                reason="High growth assumptions reflected in current valuation. Sensitive to execution risk and competitive dynamics."
                            )
                        ],
                        average_score=72.0,
                        timestamp=datetime.now()
                    ),
                    timestamp=datetime.now()
                )
            ]
            
            return DashboardResponse(
                stocks=sample_stocks,
                last_updated=datetime.now(),
                total_stocks=2,
                max_stocks=5,
                subscription_tier=SubscriptionTier.FREE,
                errors=[],
                is_sample_data=True  # Add flag to indicate this is sample data
            )
        
        # User is authenticated - show their personalized dashboard
        try:
            # Get user's tracked stocks
            user_stocks = await user_stock_service.get_user_stocks(str(current_user.id))
            max_stocks = current_user.max_stocks
            subscription_tier = current_user.subscription_tier.value
            
            # If user has no tracked stocks, return empty dashboard
            if not user_stocks:
                from ..models import SubscriptionTier
                tier_enum = SubscriptionTier.FREE
                if subscription_tier == "pro":
                    tier_enum = SubscriptionTier.PRO
                elif subscription_tier == "expert":
                    tier_enum = SubscriptionTier.EXPERT
                
                return DashboardResponse(
                    stocks=[],
                    last_updated=datetime.now(),
                    total_stocks=0,
                    max_stocks=max_stocks,
                    subscription_tier=tier_enum,
                    errors=[],
                    is_sample_data=False
                )
            
            # Get analysis for user's tracked stocks from global analysis
            service = get_scheduler_service()
            analysis_results = service.get_latest_analysis()
            latest_errors = service.get_latest_errors()
            last_updated = service.get_last_updated()
            
            # Filter analysis results to only include user's tracked stocks
            filtered_results = [
                analysis for analysis in analysis_results
                if analysis.stock_data.symbol.upper() in [symbol.upper() for symbol in user_stocks]
            ]
            
            # Create error entries for user stocks that don't have analysis
            analyzed_symbols = {analysis.stock_data.symbol.upper() for analysis in filtered_results}
            missing_symbols = [symbol for symbol in user_stocks if symbol.upper() not in analyzed_symbols]
            
            user_errors = []
            for symbol in missing_symbols:
                user_errors.append(ApiError(
                    type="analysis_missing",
                    symbol=symbol,
                    message=f"Analysis not available for {symbol}. Data will be updated soon."
                ))
            
            # Add relevant global errors for user's stocks
            for error in latest_errors:
                if error["symbol"].upper() in [symbol.upper() for symbol in user_stocks]:
                    user_errors.append(ApiError(
                        type=error["type"],
                        symbol=error["symbol"],
                        message=error["message"]
                    ))
            
            logger.info(f"User {current_user.username} dashboard: {len(user_stocks)} tracked stocks, {len(filtered_results)} analysis results")
            
            from ..models import SubscriptionTier
            tier_enum = SubscriptionTier.FREE
            if subscription_tier == "pro":
                tier_enum = SubscriptionTier.PRO
            elif subscription_tier == "expert":
                tier_enum = SubscriptionTier.EXPERT
            
            return DashboardResponse(
                stocks=filtered_results,
                last_updated=last_updated or datetime.now(),
                total_stocks=len(filtered_results),
                max_stocks=max_stocks,
                subscription_tier=tier_enum,
                errors=user_errors,
                is_sample_data=False
            )
            
        except Exception as e:
            logger.error(f"Error getting user stocks for dashboard: {e}")
            # Return empty dashboard on error
            return DashboardResponse(
                stocks=[],
                last_updated=datetime.now(),
                total_stocks=0,
                max_stocks=current_user.max_stocks,
                subscription_tier=current_user.subscription_tier,
                errors=[ApiError(
                    type="system_error",
                    symbol="SYSTEM",
                    message="Error loading your dashboard. Please try again."
                )],
                is_sample_data=False
            )
        
    except Exception as e:
        logger.error(f"Error in dashboard endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard data: {str(e)}")


@router.post("/refresh")
async def refresh_dashboard():
    """Force a refresh of the stock analysis - non-blocking."""
    try:
        service = get_scheduler_service()
        
        if service.is_update_in_progress():
            return {
                "message": "Update already in progress", 
                "timestamp": datetime.now(),
                "status": "in_progress"
            }
        
        service.force_update()
        return {
            "message": "Dashboard refresh initiated", 
            "timestamp": datetime.now(),
            "status": "started"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing dashboard: {str(e)}")


@router.get("/status")
async def get_status():
    """Get the current status of the service."""
    try:
        service = get_scheduler_service()
        last_updated = service.get_last_updated()
        total_stocks = len(service.get_latest_analysis())
        
        # Get database status
        db_status = "connected" if is_database_available() else "not available"
        
        # Get total users count if database available
        total_users = 0
        if is_database_available():
            try:
                from ..database import get_database
                db = get_database()
                if db is not None:
                    total_users = await db.users.count_documents({})
            except Exception:
                pass
        
        return {
            "status": "running",
            "last_updated": last_updated,
            "total_stocks_analyzed": total_stocks,
            "update_in_progress": service.is_update_in_progress(),
            "database_status": db_status,
            "total_users": total_users,
            "using_mock_data": {
                "stocks": service.stock_service.use_mock_data,
                "ai_analysis": service.ai_service.use_mock_analysis
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving status: {str(e)}")


@router.get("/stocks/{symbol}")
async def get_stock_analysis(symbol: str):
    """Get analysis for a specific stock symbol."""
    try:
        # Fallback to global analysis for backward compatibility
        service = get_scheduler_service()
        analysis_results = service.get_latest_analysis()
        
        for analysis in analysis_results:
            if analysis.stock_data.symbol.upper() == symbol.upper():
                # Return analysis (already in multi-AI format)
                return analysis
        
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in current analysis")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stock data: {str(e)}")
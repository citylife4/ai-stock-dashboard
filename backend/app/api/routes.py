from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List, Optional

from ..models import DashboardResponse, StockAnalysis, ApiError, User
from ..services.scheduler import SchedulerService
from ..services.user_service import UserStockService
from ..services.multi_ai_service import MultiAIService
from ..database import is_database_available
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

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


async def get_current_user_optional():
    """Get current user if authenticated, otherwise None."""
    try:
        from fastapi import Depends
        from fastapi.security import HTTPBearer
        from ..services.auth_service import get_current_active_user
        # This would be called by FastAPI dependency injection
        return None  # For now, return None as default
    except:
        return None


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """Get the current stock dashboard data."""
    try:
        current_user = None  # For backward compatibility, assume no user auth
        
        if not current_user or not is_database_available():
            # Fallback to global stock tracking for non-authenticated users or no database
            service = get_scheduler_service()
            analysis_results = service.get_latest_analysis()
            last_updated = service.get_last_updated()
            latest_errors = service.get_latest_errors()
            
            if not analysis_results and not latest_errors:
                service.force_update()
                analysis_results = service.get_latest_analysis()
                last_updated = service.get_last_updated()
                latest_errors = service.get_latest_errors()
            
            # Convert to new format with multi-AI
            converted_results = []
            for old_analysis in analysis_results:
                # Convert old single AI analysis to multi-AI format
                from ..models import MultiAIAnalysis, AIAnalysis, AIModelType
                multi_ai_analysis = MultiAIAnalysis(
                    analyses=[AIAnalysis(
                        ai_model=AIModelType.BASIC,
                        score=old_analysis.ai_analysis.score,
                        reason=old_analysis.ai_analysis.reason
                    )],
                    average_score=float(old_analysis.ai_analysis.score),
                    timestamp=old_analysis.timestamp
                )
                
                new_analysis = StockAnalysis(
                    stock_data=old_analysis.stock_data,
                    ai_analysis=multi_ai_analysis,
                    timestamp=old_analysis.timestamp
                )
                converted_results.append(new_analysis)
            
            api_errors = [
                ApiError(
                    type=error["type"],
                    symbol=error["symbol"],
                    message=error["message"]
                )
                for error in latest_errors
            ]
            
            from ..models import SubscriptionTier
            return DashboardResponse(
                stocks=converted_results,
                last_updated=last_updated or datetime.now(),
                total_stocks=len(converted_results),
                max_stocks=5,  # Default for non-authenticated
                subscription_tier=SubscriptionTier.FREE,
                errors=api_errors
            )
        
        # This code would handle authenticated users when auth is enabled
        return DashboardResponse(
            stocks=[],
            last_updated=datetime.now(),
            total_stocks=0,
            max_stocks=5,
            subscription_tier="free",
            errors=[]
        )
        
    except Exception as e:
        logger.error(f"Error in dashboard endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard data: {str(e)}")


@router.post("/refresh")
async def refresh_dashboard():
    """Force a refresh of the stock analysis."""
    try:
        service = get_scheduler_service()
        service.force_update()
        return {"message": "Dashboard refresh initiated", "timestamp": datetime.now()}
        
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
                if db:
                    total_users = await db.users.count_documents({})
            except Exception:
                pass
        
        return {
            "status": "running",
            "last_updated": last_updated,
            "total_stocks_analyzed": total_stocks,
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
                # Convert old format to new format
                from ..models import MultiAIAnalysis, AIAnalysis, AIModelType
                multi_ai_analysis = MultiAIAnalysis(
                    analyses=[AIAnalysis(
                        ai_model=AIModelType.BASIC,
                        score=analysis.ai_analysis.score,
                        reason=analysis.ai_analysis.reason
                    )],
                    average_score=float(analysis.ai_analysis.score),
                    timestamp=analysis.timestamp
                )
                
                return StockAnalysis(
                    stock_data=analysis.stock_data,
                    ai_analysis=multi_ai_analysis,
                    timestamp=analysis.timestamp
                )
        
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in current analysis")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stock data: {str(e)}")
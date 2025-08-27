from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import List

from ..models import DashboardResponse, StockAnalysis
from ..services.scheduler import SchedulerService

router = APIRouter()

# Global scheduler instance
scheduler_service = None


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


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """Get the current stock dashboard data."""
    try:
        service = get_scheduler_service()
        analysis_results = service.get_latest_analysis()
        last_updated = service.get_last_updated()
        
        if not analysis_results:
            # If no data available, force an update
            service.force_update()
            analysis_results = service.get_latest_analysis()
            last_updated = service.get_last_updated()
        
        return DashboardResponse(
            stocks=analysis_results,
            last_updated=last_updated or datetime.now(),
            total_stocks=len(analysis_results)
        )
    except Exception as e:
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
        
        return {
            "status": "running",
            "last_updated": last_updated,
            "total_stocks_analyzed": total_stocks,
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
        service = get_scheduler_service()
        analysis_results = service.get_latest_analysis()
        
        # Find the specific stock
        for analysis in analysis_results:
            if analysis.stock_data.symbol.upper() == symbol.upper():
                return analysis
        
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found in current analysis")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stock data: {str(e)}")
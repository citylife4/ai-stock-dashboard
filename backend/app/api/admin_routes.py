from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from typing import List

from ..models import (
    AdminLoginRequest, AdminLoginResponse, AdminStockRequest, 
    AdminPromptRequest, AdminPromptResponse, AdminStockListResponse,
    AdminConfigRequest, AdminConfigResponse
)
from ..services.auth_service import AuthService
from ..services.audit_service import AuditService
from ..config import config
from .routes import get_scheduler_service

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()

# Services
auth_service = AuthService()
audit_service = AuditService()


def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated admin user."""
    username = auth_service.verify_token(credentials.credentials)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint."""
    if not auth_service.authenticate_admin(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    
    audit_service.log_action("admin_login", f"Admin {request.username} logged in", request.username)
    
    return AdminLoginResponse(access_token=access_token, token_type="bearer")


@router.get("/stocks", response_model=AdminStockListResponse)
async def get_stock_list(current_admin: str = Depends(get_current_admin)):
    """Get current list of stocks being tracked."""
    try:
        symbols = config.get_stock_symbols()
        return AdminStockListResponse(symbols=symbols)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stock list: {str(e)}")


@router.post("/stocks")
async def add_stock(
    request: AdminStockRequest,
    current_admin: str = Depends(get_current_admin)
):
    """Add a new stock to the tracked list."""
    try:
        # Get current symbols
        current_symbols = config.get_stock_symbols()
        
        # Check if symbol already exists
        symbol = request.symbol.upper()
        if symbol in current_symbols:
            raise HTTPException(status_code=400, detail=f"Stock {symbol} is already being tracked")
        
        # Add new symbol
        new_symbols = current_symbols + [symbol]
        
        # Update configuration
        if not config.update_stock_symbols(new_symbols):
            raise HTTPException(status_code=500, detail="Failed to update configuration")
        
        # Log the action
        audit_service.log_action(
            "add_stock", 
            f"Added stock {symbol} to tracking list", 
            current_admin
        )
        
        # Force update to start tracking immediately
        scheduler_service = get_scheduler_service()
        scheduler_service.force_update()
        
        return {"message": f"Successfully added {symbol} to tracked stocks", "symbol": symbol}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding stock: {str(e)}")


@router.delete("/stocks/{symbol}")
async def remove_stock(
    symbol: str,
    current_admin: str = Depends(get_current_admin)
):
    """Remove a stock from the tracked list."""
    try:
        # Get current symbols
        current_symbols = config.get_stock_symbols()
        
        # Check if symbol exists
        symbol = symbol.upper()
        if symbol not in current_symbols:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} is not currently being tracked")
        
        # Remove symbol
        new_symbols = [s for s in current_symbols if s != symbol]
        
        # Ensure at least one stock remains
        if not new_symbols:
            raise HTTPException(status_code=400, detail="Cannot remove all stocks - at least one must remain")
        
        # Update configuration
        if not config.update_stock_symbols(new_symbols):
            raise HTTPException(status_code=500, detail="Failed to update configuration")
        
        # Log the action
        audit_service.log_action(
            "remove_stock", 
            f"Removed stock {symbol} from tracking list", 
            current_admin
        )
        
        # Force update to reflect changes immediately
        scheduler_service = get_scheduler_service()
        scheduler_service.force_update()
        
        return {"message": f"Successfully removed {symbol} from tracked stocks", "symbol": symbol}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing stock: {str(e)}")


@router.get("/prompts", response_model=AdminPromptResponse)
async def get_prompts(current_admin: str = Depends(get_current_admin)):
    """Get current AI analysis prompt."""
    try:
        prompt = config.get_ai_analysis_prompt()
        return AdminPromptResponse(ai_analysis_prompt=prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prompts: {str(e)}")


@router.put("/prompts")
async def update_prompts(
    request: AdminPromptRequest,
    current_admin: str = Depends(get_current_admin)
):
    """Update AI analysis prompt."""
    try:
        if request.ai_analysis_prompt is None:
            raise HTTPException(status_code=400, detail="AI analysis prompt is required")
        
        # Validate prompt has required placeholders
        required_placeholders = ["{symbol}", "{current_price}", "{previous_close}", "{change_percent}", "{volume}", "{market_cap}"]
        missing_placeholders = [p for p in required_placeholders if p not in request.ai_analysis_prompt]
        
        if missing_placeholders:
            raise HTTPException(
                status_code=400, 
                detail=f"Prompt must contain all required placeholders: {', '.join(missing_placeholders)}"
            )
        
        # Update configuration
        if not config.update_ai_analysis_prompt(request.ai_analysis_prompt):
            raise HTTPException(status_code=500, detail="Failed to update configuration")
        
        # Log the action
        audit_service.log_action(
            "update_prompt", 
            "Updated AI analysis prompt", 
            current_admin
        )
        
        # Force update to use new prompt immediately
        scheduler_service = get_scheduler_service()
        scheduler_service.force_update()
        
        return {"message": "Successfully updated AI analysis prompt"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating prompts: {str(e)}")


@router.get("/logs")
async def get_audit_logs(
    limit: int = 100,
    current_admin: str = Depends(get_current_admin)
):
    """Get audit logs."""
    try:
        logs = audit_service.get_logs(limit=min(limit, 1000))  # Cap at 1000
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving audit logs: {str(e)}")


@router.get("/config", response_model=AdminConfigResponse)
async def get_config(current_admin: str = Depends(get_current_admin)):
    """Get current data source and API key configuration."""
    try:
        data_source = config.get_data_source()
        alpha_vantage_api_key = config.get_alpha_vantage_api_key()
        polygon_api_key = config.get_polygon_api_key()
        ai_provider = config.get_ai_provider()
        ai_model = config.get_ai_model()
        return AdminConfigResponse(
            data_source=data_source, 
            alpha_vantage_api_key=alpha_vantage_api_key,
            polygon_api_key=polygon_api_key,
            ai_provider=ai_provider,
            ai_model=ai_model
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving configuration: {str(e)}")


@router.put("/config")
async def update_config(
    request: AdminConfigRequest,
    current_admin: str = Depends(get_current_admin)
):
    """Update data source and API key configuration."""
    try:
        updated = False
        
        if request.data_source is not None:
            if request.data_source not in ["yahoo", "alpha_vantage", "polygon"]:
                raise HTTPException(status_code=400, detail="Invalid data source. Must be 'yahoo', 'alpha_vantage', or 'polygon'")
            
            if not config.update_data_source(request.data_source):
                raise HTTPException(status_code=500, detail="Failed to update data source")
            
            audit_service.log_action(
                "update_data_source", 
                f"Changed data source to {request.data_source}", 
                current_admin
            )
            updated = True
        
        if request.alpha_vantage_api_key is not None:
            if not config.update_alpha_vantage_api_key(request.alpha_vantage_api_key):
                raise HTTPException(status_code=500, detail="Failed to update Alpha Vantage API key")
            
            audit_service.log_action(
                "update_api_key", 
                "Updated Alpha Vantage API key", 
                current_admin
            )
            updated = True
        
        if request.polygon_api_key is not None:
            if not config.update_polygon_api_key(request.polygon_api_key):
                raise HTTPException(status_code=500, detail="Failed to update Polygon.io API key")
            
            audit_service.log_action(
                "update_api_key", 
                "Updated Polygon.io API key", 
                current_admin
            )
            updated = True
        
        if request.ai_provider is not None:
            if not config.update_ai_provider(request.ai_provider):
                raise HTTPException(status_code=500, detail="Failed to update AI provider")
            
            audit_service.log_action(
                "update_ai_provider", 
                f"Changed AI provider to {request.ai_provider}", 
                current_admin
            )
            updated = True
        
        if request.ai_model is not None:
            if not config.update_ai_model(request.ai_model):
                raise HTTPException(status_code=500, detail="Failed to update AI model")
            
            audit_service.log_action(
                "update_ai_model", 
                f"Changed AI model to {request.ai_model}", 
                current_admin
            )
            updated = True
        
        if updated:
            # Force update to use new configuration immediately
            scheduler_service = get_scheduler_service()
            scheduler_service.refresh_stock_service()  # Need to add this method
            scheduler_service.force_update()
        
        return {"message": "Configuration updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")


@router.post("/refresh")
async def force_refresh(current_admin: str = Depends(get_current_admin)):
    """Force refresh of stock data (admin only)."""
    try:
        scheduler_service = get_scheduler_service()
        scheduler_service.force_update()
        
        audit_service.log_action(
            "force_refresh", 
            "Manually triggered stock data refresh", 
            current_admin
        )
        
        return {"message": "Stock data refresh initiated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forcing refresh: {str(e)}")
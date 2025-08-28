from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import List, Dict, Optional
import logging

from .stock_service import StockService
from .ai_service import AIService
from ..models import StockAnalysis
from ..config import config
from ..exceptions import StockDataException, AIAnalysisException

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.stock_service = StockService()
        self.ai_service = AIService()
        self.latest_analysis: List[StockAnalysis] = []
        self.last_updated = None
        self.latest_errors: List[Dict[str, str]] = []  # Store latest errors for frontend display
        
    def start(self):
        """Start the scheduler."""
        # Test connections on startup
        self.stock_service.test_real_data_connection()
        
        # Run initial analysis
        self.update_stock_analysis()
        
        # Schedule periodic updates
        self.scheduler.add_job(
            func=self.update_stock_analysis,
            trigger=IntervalTrigger(minutes=config.UPDATE_INTERVAL),
            id='stock_analysis_job',
            name='Update stock analysis',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(f"Scheduler started with {config.UPDATE_INTERVAL} minute intervals")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def update_stock_analysis(self):
        """Update stock analysis for all configured symbols."""
        logger.info("Starting stock analysis update...")
        
        # Clear previous errors
        self.latest_errors = []
        
        try:
            # Get current stock symbols from dynamic config
            stock_symbols = config.get_stock_symbols()
            
            # Analyze each stock individually to collect specific errors
            analysis_results = []
            for symbol in stock_symbols:
                try:
                    # Fetch stock data
                    stock_data = self.stock_service.fetch_stock_data(symbol)
                    if not stock_data:
                        error_msg = f"No stock data available for {symbol}"
                        self.latest_errors.append({
                            "type": "stock_data",
                            "symbol": symbol,
                            "message": error_msg
                        })
                        logger.error(error_msg)
                        continue
                        
                    # Analyze stock with AI
                    ai_analysis = self.ai_service.analyze_stock(stock_data)
                    
                    # Convert single AI analysis to multi-AI format for compatibility
                    from ..models import MultiAIAnalysis
                    multi_ai_analysis = MultiAIAnalysis(
                        analyses=[ai_analysis],
                        average_score=float(ai_analysis.score),
                        timestamp=datetime.now()
                    )
                    
                    stock_analysis = StockAnalysis(
                        stock_data=stock_data,
                        ai_analysis=multi_ai_analysis,
                        timestamp=datetime.now()
                    )
                    analysis_results.append(stock_analysis)
                    logger.info(f"Analyzed {stock_data.symbol}: Score {multi_ai_analysis.average_score}")
                    
                except StockDataException as e:
                    self.latest_errors.append({
                        "type": "stock_data",
                        "symbol": symbol,
                        "message": str(e)
                    })
                    logger.error(f"Stock data error for {symbol}: {e}")
                    
                except AIAnalysisException as e:
                    self.latest_errors.append({
                        "type": "ai_analysis", 
                        "symbol": symbol,
                        "message": str(e)
                    })
                    logger.error(f"AI analysis error for {symbol}: {e}")
                    
                except Exception as e:
                    error_msg = f"Unexpected error analyzing {symbol}: {e}"
                    self.latest_errors.append({
                        "type": "general",
                        "symbol": symbol,
                        "message": error_msg
                    })
                    logger.error(error_msg)
            
            # Sort by AI average score (highest first)
            analysis_results.sort(key=lambda x: x.ai_analysis.average_score, reverse=True)
            
            # Update stored results
            self.latest_analysis = analysis_results
            self.last_updated = datetime.now()
            
            if analysis_results:
                logger.info(f"Stock analysis update completed. Analyzed {len(analysis_results)} stocks.")
            else:
                logger.warning("Stock analysis update completed but no stocks were successfully analyzed.")
                
            if self.latest_errors:
                logger.warning(f"Stock analysis completed with {len(self.latest_errors)} errors.")
            
        except Exception as e:
            error_msg = f"Error during stock analysis update: {e}"
            self.latest_errors.append({
                "type": "general",
                "symbol": "system",
                "message": error_msg
            })
            logger.error(error_msg)
    
    def get_latest_analysis(self) -> List[StockAnalysis]:
        """Get the latest stock analysis results."""
        return self.latest_analysis
    
    def get_last_updated(self) -> datetime:
        """Get the timestamp of the last update."""
        return self.last_updated
    
    def force_update(self):
        """Force an immediate update of stock analysis."""
        logger.info("Forcing immediate stock analysis update...")
        self.update_stock_analysis()
    
    def get_latest_errors(self) -> List[Dict[str, str]]:
        """Get the latest errors from stock analysis."""
        return self.latest_errors
    
    def refresh_stock_service(self):
        """Refresh the stock service configuration - call when data source changes."""
        logger.info("Refreshing stock service configuration...")
        self.stock_service.refresh_data_sources()
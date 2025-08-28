from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import List, Dict, Optional
import logging
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

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
        self.is_updating = False  # Track if update is in progress
        self.executor = ThreadPoolExecutor(max_workers=4)  # For parallel processing
        
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
        self.executor.shutdown(wait=True)
        logger.info("Scheduler stopped")
    
    def analyze_single_stock(self, symbol: str) -> Optional[StockAnalysis]:
        """Analyze a single stock symbol - runs in thread pool."""
        try:
            # Fetch stock data
            stock_data = self.stock_service.fetch_stock_data(symbol)
            if not stock_data:
                error_msg = f"No stock data available for {symbol}"
                logger.error(error_msg)
                return None
                
            # Analyze stock
            ai_analysis = self.ai_service.analyze_stock(stock_data)
            stock_analysis = StockAnalysis(
                stock_data=stock_data,
                ai_analysis=ai_analysis,
                timestamp=datetime.now()
            )
            logger.info(f"Analyzed {stock_data.symbol}: Score {ai_analysis.score}")
            return stock_analysis
            
        except StockDataException as e:
            logger.error(f"Stock data error for {symbol}: {e}")
            return None
            
        except AIAnalysisException as e:
            logger.error(f"AI analysis error for {symbol}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error analyzing {symbol}: {e}")
            return None
    
    def update_stock_analysis(self):
        """Update stock analysis for all configured symbols - non-blocking."""
        if self.is_updating:
            logger.info("Stock analysis update already in progress, skipping...")
            return
            
        # Run the actual update in a separate thread to avoid blocking
        thread = threading.Thread(target=self._update_stock_analysis_async, daemon=True)
        thread.start()
    
    def _update_stock_analysis_async(self):
        """Internal method that runs the actual analysis asynchronously."""
        logger.info("Starting stock analysis update...")
        self.is_updating = True
        
        try:
            # Clear previous errors
            self.latest_errors = []
            
            # Get current stock symbols from dynamic config
            stock_symbols = config.get_stock_symbols()
            
            # Use ThreadPoolExecutor for parallel processing
            analysis_results = []
            error_count = 0
            
            # Submit all stock analysis tasks to thread pool
            future_to_symbol = {
                self.executor.submit(self.analyze_single_stock, symbol): symbol 
                for symbol in stock_symbols
            }
            
            # Collect results as they complete
            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    result = future.result(timeout=30)  # 30 second timeout per stock
                    if result:
                        analysis_results.append(result)
                    else:
                        error_count += 1
                        self.latest_errors.append({
                            "type": "stock_data",
                            "symbol": symbol,
                            "message": f"Failed to analyze {symbol}"
                        })
                except Exception as e:
                    error_count += 1
                    error_msg = f"Error analyzing {symbol}: {str(e)}"
                    self.latest_errors.append({
                        "type": "general",
                        "symbol": symbol,
                        "message": error_msg
                    })
                    logger.error(error_msg)
            
            # Sort by AI score (highest first)
            analysis_results.sort(key=lambda x: x.ai_analysis.score, reverse=True)
            
            # Update stored results atomically
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
        finally:
            self.is_updating = False
    
    def get_latest_analysis(self) -> List[StockAnalysis]:
        """Get the latest stock analysis results."""
        return self.latest_analysis
    
    def get_last_updated(self) -> Optional[datetime]:
        """Get the timestamp of the last update."""
        return self.last_updated
    
    def force_update(self):
        """Force an immediate update of stock analysis - non-blocking."""
        logger.info("Forcing immediate stock analysis update...")
        self.update_stock_analysis()  # This is now non-blocking
    
    def get_latest_errors(self) -> List[Dict[str, str]]:
        """Get the latest errors from stock analysis."""
        return self.latest_errors
    
    def is_update_in_progress(self) -> bool:
        """Check if an update is currently in progress."""
        return self.is_updating
    
    def refresh_stock_service(self):
        """Refresh the stock service configuration - call when data source changes."""
        logger.info("Refreshing stock service configuration...")
        self.stock_service.refresh_data_sources()
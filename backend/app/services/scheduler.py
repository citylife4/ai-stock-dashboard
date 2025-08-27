from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import List
import logging

from .stock_service import StockService
from .ai_service import AIService
from ..models import StockAnalysis
from ..config import config

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.stock_service = StockService()
        self.ai_service = AIService()
        self.latest_analysis: List[StockAnalysis] = []
        self.last_updated = None
        
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
        
        try:
            # Fetch stock data
            stock_data_list = self.stock_service.fetch_multiple_stocks(config.STOCK_SYMBOLS)
            
            # Analyze each stock
            analysis_results = []
            for stock_data in stock_data_list:
                try:
                    ai_analysis = self.ai_service.analyze_stock(stock_data)
                    stock_analysis = StockAnalysis(
                        stock_data=stock_data,
                        ai_analysis=ai_analysis,
                        timestamp=datetime.now()
                    )
                    analysis_results.append(stock_analysis)
                    logger.info(f"Analyzed {stock_data.symbol}: Score {ai_analysis.score}")
                except Exception as e:
                    logger.error(f"Error analyzing {stock_data.symbol}: {e}")
            
            # Sort by AI score (highest first)
            analysis_results.sort(key=lambda x: x.ai_analysis.score, reverse=True)
            
            # Update stored results
            self.latest_analysis = analysis_results
            self.last_updated = datetime.now()
            
            logger.info(f"Stock analysis update completed. Analyzed {len(analysis_results)} stocks.")
            
        except Exception as e:
            logger.error(f"Error during stock analysis update: {e}")
    
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
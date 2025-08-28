from alpha_vantage.timeseries import TimeSeries
import random
from datetime import datetime
from typing import List, Optional
from ..models import StockData
from ..config import config
import logging

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self):
        self.use_mock_data = True  # Start with mock data, switch to real if Alpha Vantage works
        self.alpha_vantage = None
        if config.ALPHA_VANTAGE_API_KEY:
            try:
                self.alpha_vantage = TimeSeries(key=config.ALPHA_VANTAGE_API_KEY, output_format='json')
            except Exception as e:
                logger.warning(f"Failed to initialize Alpha Vantage client: {e}")
        
    def fetch_stock_data(self, symbol: str) -> Optional[StockData]:
        """Fetch stock data for a given symbol."""
        try:
            if not self.use_mock_data:
                return self._fetch_real_data(symbol)
            else:
                return self._generate_mock_data(symbol)
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return self._generate_mock_data(symbol)
    
    def fetch_multiple_stocks(self, symbols: List[str]) -> List[StockData]:
        """Fetch stock data for multiple symbols."""
        stocks = []
        for symbol in symbols:
            stock_data = self.fetch_stock_data(symbol)
            if stock_data:
                stocks.append(stock_data)
        return stocks
    
    def _fetch_real_data(self, symbol: str) -> Optional[StockData]:
        """Fetch real stock data using Alpha Vantage."""
        try:
            if not self.alpha_vantage:
                logger.warning(f"Alpha Vantage client not initialized for {symbol}, using mock data")
                return self._generate_mock_data(symbol)
            
            # Get quote data (current price info)
            quote_data, quote_meta = self.alpha_vantage.get_quote_endpoint(symbol)
            
            if not quote_data:
                logger.warning(f"No quote data for {symbol}, using mock data")
                return self._generate_mock_data(symbol)
            
            # Get daily data for historical comparison
            daily_data, daily_meta = self.alpha_vantage.get_daily(symbol, outputsize='compact')
            
            current_price = float(quote_data['05. price'])
            previous_close = float(quote_data['08. previous close'])
            change_percent = float(quote_data['10. change percent'].rstrip('%'))
            volume = int(quote_data['06. volume'])
            
            # Try to get market cap from daily metadata or set to None
            market_cap = None
            
            return StockData(
                symbol=symbol,
                current_price=round(current_price, 2),
                previous_close=round(previous_close, 2),
                change_percent=round(change_percent, 2),
                volume=volume,
                market_cap=market_cap,
                last_updated=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error fetching real data for {symbol}: {e}")
            return self._generate_mock_data(symbol)
    
    def _generate_mock_data(self, symbol: str) -> StockData:
        """Generate realistic mock stock data."""
        # Base prices for common stocks
        base_prices = {
            "AAPL": 180.0,
            "GOOGL": 140.0,
            "MSFT": 380.0,
            "TSLA": 250.0,
            "AMZN": 150.0,
            "NVDA": 450.0,
            "META": 320.0,
            "NFLX": 440.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        
        # Add some realistic variation
        price_variation = random.uniform(-0.05, 0.05)  # ±5%
        current_price = base_price * (1 + price_variation)
        
        # Previous close
        daily_change = random.uniform(-0.03, 0.03)  # ±3% daily change
        previous_close = current_price / (1 + daily_change)
        
        change_percent = ((current_price - previous_close) / previous_close) * 100
        
        # Volume
        volume = random.randint(50000000, 200000000)  # 50M to 200M shares
        
        # Market cap (in billions, rough estimates)
        market_caps = {
            "AAPL": 2800000000000,  # $2.8T
            "GOOGL": 1700000000000,  # $1.7T
            "MSFT": 2900000000000,  # $2.9T
            "TSLA": 800000000000,   # $800B
            "AMZN": 1500000000000,  # $1.5T
            "NVDA": 1100000000000,  # $1.1T
            "META": 800000000000,   # $800B
            "NFLX": 200000000000    # $200B
        }
        
        market_cap = market_caps.get(symbol, 500000000000)  # Default $500B
        
        return StockData(
            symbol=symbol,
            current_price=round(current_price, 2),
            previous_close=round(previous_close, 2),
            change_percent=round(change_percent, 2),
            volume=volume,
            market_cap=market_cap,
            last_updated=datetime.now()
        )
    
    def test_real_data_connection(self) -> bool:
        """Test if we can fetch real data and switch mode accordingly."""
        try:
            if not self.alpha_vantage:
                logger.warning("Alpha Vantage client not initialized")
                self.use_mock_data = True
                logger.info("Using mock stock data")
                return False
                
            # Test with AAPL
            quote_data, _ = self.alpha_vantage.get_quote_endpoint("AAPL")
            if quote_data and '05. price' in quote_data:
                self.use_mock_data = False
                logger.info("Successfully connected to Alpha Vantage stock data")
                return True
        except Exception as e:
            logger.warning(f"Could not connect to Alpha Vantage stock data: {e}")
        
        self.use_mock_data = True
        logger.info("Using mock stock data")
        return False
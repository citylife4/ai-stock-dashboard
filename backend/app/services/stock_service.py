from alpha_vantage.timeseries import TimeSeries
import yfinance as yf
from polygon import RESTClient
import random
from datetime import datetime
from typing import List, Optional
from ..models import StockData
from ..config import config
from ..exceptions import YahooFinanceException, AlphaVantageException, PolygonException
import logging

logger = logging.getLogger(__name__)


class StockService:
    def __init__(self):
        self.use_mock_data = True  # Start with mock data, will switch based on configuration and connectivity
        self.alpha_vantage = None
        self.polygon_client = None
        self._initialize_data_sources()
        
    def _initialize_data_sources(self):
        """Initialize data sources based on configuration."""
        data_source = config.get_data_source()
        
        if data_source == "alpha_vantage":
            api_key = config.get_alpha_vantage_api_key()
            if api_key:
                try:
                    self.alpha_vantage = TimeSeries(key=api_key, output_format='json')
                    logger.info("Alpha Vantage client initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Alpha Vantage client: {e}")
            else:
                logger.warning("Alpha Vantage selected but no API key provided")
        elif data_source == "polygon":
            api_key = config.get_polygon_api_key()
            if api_key:
                try:
                    self.polygon_client = RESTClient(api_key=api_key)
                    logger.info("Polygon.io client initialized")
                except Exception as e:
                    logger.warning(f"Failed to initialize Polygon.io client: {e}")
            else:
                logger.warning("Polygon.io selected but no API key provided")
        
        # Test connection and set data mode
        self.test_real_data_connection()
        
    def refresh_data_sources(self):
        """Refresh data source configuration - call when config changes."""
        self._initialize_data_sources()
        
    def fetch_stock_data(self, symbol: str) -> Optional[StockData]:
        """Fetch stock data for a given symbol."""
        try:
            if not self.use_mock_data:
                return self._fetch_real_data(symbol)
            else:
                if config.DEBUG:
                    # In development, fall back to mock data
                    return self._generate_mock_data(symbol)
                else:
                    # In production, raise exception instead of using mock data
                    data_source = config.get_data_source()
                    if data_source == "alpha_vantage":
                        raise AlphaVantageException(f"Alpha Vantage API connection failed for symbol {symbol}")
                    elif data_source == "polygon":
                        raise PolygonException(f"Polygon.io API connection failed for symbol {symbol}")
                    else:
                        raise YahooFinanceException(f"Yahoo Finance API connection failed for symbol {symbol}")
        except (YahooFinanceException, AlphaVantageException, PolygonException):
            # Re-raise these exceptions so they bubble up
            raise
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            if config.DEBUG:
                # In development, fall back to mock data
                return self._generate_mock_data(symbol)
            else:
                # In production, raise exception with details
                data_source = config.get_data_source()
                if data_source == "alpha_vantage":
                    raise AlphaVantageException(f"Alpha Vantage API error for symbol {symbol}: {str(e)}")
                elif data_source == "polygon":
                    raise PolygonException(f"Polygon.io API error for symbol {symbol}: {str(e)}")
                else:
                    raise YahooFinanceException(f"Yahoo Finance API error for symbol {symbol}: {str(e)}")
    
    def fetch_multiple_stocks(self, symbols: List[str]) -> List[StockData]:
        """Fetch stock data for multiple symbols."""
        stocks = []
        for symbol in symbols:
            try:
                stock_data = self.fetch_stock_data(symbol)
                if stock_data:
                    stocks.append(stock_data)
            except (YahooFinanceException, AlphaVantageException, PolygonException) as e:
                # In production, don't skip the error but let it bubble up
                if not config.DEBUG:
                    raise
                # In development, log the error and continue
                logger.error(f"Error fetching data for {symbol}: {e}")
        return stocks
    
    def _fetch_real_data(self, symbol: str) -> Optional[StockData]:
        """Fetch real stock data using configured data source."""
        data_source = config.get_data_source()
        
        if data_source == "alpha_vantage":
            return self._fetch_alpha_vantage_data(symbol)
        elif data_source == "polygon":
            return self._fetch_polygon_data(symbol)
        else:  # Default to Yahoo Finance
            return self._fetch_yahoo_data(symbol)
    
    def _fetch_yahoo_data(self, symbol: str) -> Optional[StockData]:
        """Fetch real stock data using Yahoo Finance."""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="2d")
            
            if hist.empty or len(hist) < 2:
                error_msg = f"Insufficient data for {symbol} from Yahoo Finance"
                logger.warning(error_msg)
                if config.DEBUG:
                    return self._generate_mock_data(symbol)
                else:
                    raise YahooFinanceException(error_msg)
            
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2]
            change_percent = ((current_price - previous_close) / previous_close) * 100
            volume = int(hist['Volume'].iloc[-1])
            
            market_cap = info.get('marketCap')
            
            return StockData(
                symbol=symbol,
                current_price=round(current_price, 2),
                previous_close=round(previous_close, 2),
                change_percent=round(change_percent, 2),
                volume=volume,
                market_cap=market_cap,
                last_updated=datetime.now()
            )
        except YahooFinanceException:
            # Re-raise our custom exception
            raise
        except Exception as e:
            error_msg = f"Error fetching Yahoo Finance data for {symbol}: {e}"
            logger.error(error_msg)
            if config.DEBUG:
                return self._generate_mock_data(symbol)
            else:
                raise YahooFinanceException(error_msg)
    
    def _fetch_alpha_vantage_data(self, symbol: str) -> Optional[StockData]:
        """Fetch real stock data using Alpha Vantage."""
        try:
            if not self.alpha_vantage:
                error_msg = f"Alpha Vantage client not initialized for {symbol}"
                logger.warning(error_msg)
                if config.DEBUG:
                    return self._generate_mock_data(symbol)
                else:
                    raise AlphaVantageException(error_msg)
            
            # Get quote data (current price info)
            quote_data, quote_meta = self.alpha_vantage.get_quote_endpoint(symbol)
            
            if not quote_data:
                error_msg = f"No quote data for {symbol} from Alpha Vantage"
                logger.warning(error_msg)
                if config.DEBUG:
                    return self._generate_mock_data(symbol)
                else:
                    raise AlphaVantageException(error_msg)
            
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
        except AlphaVantageException:
            # Re-raise our custom exception
            raise
        except Exception as e:
            error_msg = f"Error fetching Alpha Vantage data for {symbol}: {e}"
            logger.error(error_msg)
            if config.DEBUG:
                return self._generate_mock_data(symbol)
            else:
                raise AlphaVantageException(error_msg)
    
    def _fetch_polygon_data(self, symbol: str) -> Optional[StockData]:
        """Fetch real stock data using Polygon.io."""
        try:
            if not self.polygon_client:
                error_msg = f"Polygon.io client not initialized for {symbol}"
                logger.warning(error_msg)
                if config.DEBUG:
                    return self._generate_mock_data(symbol)
                else:
                    raise PolygonException(error_msg)
            
            # Get previous close with improved error handling
            prev_close_response = self.polygon_client.get_previous_close_agg(symbol)
            
            # Handle different response formats
            prev_close_data = None
            if prev_close_response:
                # Check if response is a list (alternate API format)
                if isinstance(prev_close_response, list):
                    if len(prev_close_response) > 0:
                        prev_close_data = prev_close_response[0]
                # Check if response has results attribute (standard format)
                elif hasattr(prev_close_response, 'results') and prev_close_response.results:
                    prev_close_data = prev_close_response.results[0]
                # Check if response is directly the data object
                elif hasattr(prev_close_response, 'c'):
                    prev_close_data = prev_close_response
            
            if not prev_close_data:
                error_msg = f"No previous close data for {symbol} from Polygon.io"
                logger.warning(error_msg)
                if config.DEBUG:
                    return self._generate_mock_data(symbol)
                else:
                    raise PolygonException(error_msg)
            
            # Extract previous close price and volume
            previous_close = getattr(prev_close_data, 'c', None)
            volume = getattr(prev_close_data, 'v', None)
            
            if previous_close is None:
                error_msg = f"Invalid previous close data format for {symbol} from Polygon.io"
                logger.warning(error_msg)
                if config.DEBUG:
                    return self._generate_mock_data(symbol)
                else:
                    raise PolygonException(error_msg)
            
            # Get current day aggregates (if available)
            current_price = previous_close  # Default to previous close
            try:
                from datetime import date
                today = date.today().strftime('%Y-%m-%d')
                current_agg_response = self.polygon_client.get_aggs(
                    symbol, 1, "day", today, today
                )
                
                # Handle different response formats for current aggregates
                current_data = None
                if current_agg_response:
                    if isinstance(current_agg_response, list):
                        if len(current_agg_response) > 0:
                            current_data = current_agg_response[0]
                    elif hasattr(current_agg_response, 'results') and current_agg_response.results:
                        current_data = current_agg_response.results[0]
                    elif hasattr(current_agg_response, 'c'):
                        current_data = current_agg_response
                
                if current_data and hasattr(current_data, 'c'):
                    current_price = current_data.c
                    if hasattr(current_data, 'v'):
                        volume = current_data.v
                        
            except Exception as e:
                # Log the error but continue with previous close data
                logger.debug(f"Could not get current day data for {symbol}: {e}")
            
            # Get ticker details for market cap
            market_cap = None
            try:
                ticker_details = self.polygon_client.get_ticker_details(symbol)
                if ticker_details:
                    # Handle different response formats for ticker details
                    if hasattr(ticker_details, 'market_cap'):
                        market_cap = ticker_details.market_cap
                    elif hasattr(ticker_details, 'results') and ticker_details.results:
                        results = ticker_details.results
                        if hasattr(results, 'market_cap'):
                            market_cap = results.market_cap
            except Exception as e:
                # Market cap is optional, log but don't fail
                logger.debug(f"Could not get market cap for {symbol}: {e}")
            
            # Calculate change percentage
            change_percent = ((current_price - previous_close) / previous_close) * 100 if previous_close > 0 else 0
            
            return StockData(
                symbol=symbol,
                current_price=round(current_price, 2),
                previous_close=round(previous_close, 2),
                change_percent=round(change_percent, 2),
                volume=volume or 0,
                market_cap=market_cap,
                last_updated=datetime.now()
            )
        except PolygonException:
            # Re-raise our custom exception
            raise
        except Exception as e:
            error_msg = f"Error fetching Polygon.io data for {symbol}: {e}"
            logger.error(error_msg)
            
            # Check for rate limiting (429 error)
            if "429" in str(e) or "too many" in str(e).lower():
                error_msg = f"Polygon.io rate limit exceeded for {symbol}. Please wait before retrying."
                logger.warning(error_msg)
                if config.DEBUG:
                    return self._generate_mock_data(symbol)
                else:
                    raise PolygonException(error_msg)
            
            if config.DEBUG:
                return self._generate_mock_data(symbol)
            else:
                raise PolygonException(error_msg)
    
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
        data_source = config.get_data_source()
        
        try:
            if data_source == "alpha_vantage":
                if not self.alpha_vantage:
                    logger.warning("Alpha Vantage selected but client not initialized")
                    self.use_mock_data = True
                    logger.info("Using mock stock data")
                    return False
                    
                # Test with AAPL
                quote_data, _ = self.alpha_vantage.get_quote_endpoint("AAPL")
                if quote_data and '05. price' in quote_data:
                    self.use_mock_data = False
                    logger.info("Successfully connected to Alpha Vantage stock data")
                    return True
            elif data_source == "polygon":
                if not self.polygon_client:
                    logger.warning("Polygon.io selected but client not initialized")
                    self.use_mock_data = True
                    logger.info("Using mock stock data")
                    return False
                    
                # Test with AAPL
                ticker_data = self.polygon_client.get_ticker_details("AAPL")
                if ticker_data and hasattr(ticker_data, 'ticker'):
                    self.use_mock_data = False
                    logger.info("Successfully connected to Polygon.io stock data")
                    return True
            else:  # Yahoo Finance
                stock = yf.Ticker("AAPL")
                hist = stock.history(period="1d")
                if not hist.empty:
                    self.use_mock_data = False
                    logger.info("Successfully connected to Yahoo Finance stock data")
                    return True
        except Exception as e:
            logger.warning(f"Could not connect to {data_source} stock data: {e}")
        
        self.use_mock_data = True
        logger.info("Using mock stock data")
        return False
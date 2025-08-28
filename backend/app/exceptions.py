"""Custom exceptions for the AI Stock Dashboard."""


class StockDataException(Exception):
    """Base exception for stock data related errors."""
    pass


class YahooFinanceException(StockDataException):
    """Exception raised when Yahoo Finance API fails."""
    pass


class AlphaVantageException(StockDataException):
    """Exception raised when Alpha Vantage API fails."""
    pass


class AIAnalysisException(Exception):
    """Base exception for AI analysis related errors."""
    pass


class OpenAIException(AIAnalysisException):
    """Exception raised when OpenAI API fails."""
    pass


class GroqException(AIAnalysisException):
    """Exception raised when Groq API fails."""
    pass
import time
import asyncio
from functools import wraps
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API calls with exponential backoff."""
    
    def __init__(self, calls_per_minute: int = 5, calls_per_day: int = 1000):
        self.calls_per_minute = calls_per_minute
        self.calls_per_day = calls_per_day
        self.minute_calls: Dict[int, int] = {}
        self.day_calls: Dict[int, int] = {}
        self.last_call_time = 0
        self.retry_delay = 12  # Start with 12 seconds between calls for free tier
        
    def can_make_call(self) -> tuple[bool, Optional[int]]:
        """Check if we can make a call now. Returns (can_call, wait_seconds)."""
        current_time = time.time()
        current_minute = int(current_time // 60)
        current_day = int(current_time // (24 * 3600))
        
        # Check daily limit
        daily_calls = self.day_calls.get(current_day, 0)
        if daily_calls >= self.calls_per_day:
            reset_time = (current_day + 1) * 24 * 3600
            wait_seconds = int(reset_time - current_time)
            logger.warning(f"Daily API limit reached. Resets in {wait_seconds} seconds")
            return False, wait_seconds
        
        # Check minute limit
        minute_calls = self.minute_calls.get(current_minute, 0)
        if minute_calls >= self.calls_per_minute:
            wait_seconds = 60 - int(current_time % 60)
            logger.warning(f"Per-minute API limit reached. Wait {wait_seconds} seconds")
            return False, wait_seconds
        
        # Check minimum time between calls
        time_since_last = current_time - self.last_call_time
        if time_since_last < self.retry_delay:
            wait_seconds = int(self.retry_delay - time_since_last)
            logger.info(f"Rate limiting: wait {wait_seconds} seconds")
            return False, wait_seconds
        
        return True, None
    
    def record_call(self, success: bool = True):
        """Record a successful API call."""
        current_time = time.time()
        current_minute = int(current_time // 60)
        current_day = int(current_time // (24 * 3600))
        
        # Update counters
        self.minute_calls[current_minute] = self.minute_calls.get(current_minute, 0) + 1
        self.day_calls[current_day] = self.day_calls.get(current_day, 0) + 1
        self.last_call_time = current_time
        
        # Adjust retry delay based on success
        if success:
            # Gradually reduce delay on success (but keep minimum)
            self.retry_delay = max(12, self.retry_delay * 0.9)
        else:
            # Increase delay on failure (exponential backoff)
            self.retry_delay = min(300, self.retry_delay * 1.5)  # Max 5 minutes
        
        # Clean old entries (keep only last hour for minutes, last week for days)
        current_hour_start = current_minute - 60
        self.minute_calls = {k: v for k, v in self.minute_calls.items() if k > current_hour_start}
        
        last_week = current_day - 7
        self.day_calls = {k: v for k, v in self.day_calls.items() if k > last_week}
    
    def wait_if_needed(self):
        """Wait if necessary before making a call."""
        can_call, wait_seconds = self.can_make_call()
        if not can_call and wait_seconds:
            logger.info(f"Rate limiting: sleeping for {wait_seconds} seconds")
            time.sleep(wait_seconds)


def with_rate_limiting(rate_limiter: RateLimiter):
    """Decorator to add rate limiting to API calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rate_limiter.wait_if_needed()
            try:
                result = func(*args, **kwargs)
                rate_limiter.record_call(success=True)
                return result
            except Exception as e:
                # Check if it's a rate limit error
                if "429" in str(e) or "too many" in str(e).lower() or "rate limit" in str(e).lower():
                    rate_limiter.record_call(success=False)
                    logger.warning(f"Rate limit detected in API response: {e}")
                    # Wait longer before next call
                    time.sleep(rate_limiter.retry_delay)
                raise
        return wrapper
    return decorator


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator to retry function calls with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        # Last attempt, re-raise the exception
                        raise
                    
                    # Check if it's a retryable error
                    error_str = str(e).lower()
                    if any(phrase in error_str for phrase in [
                        "429", "too many", "rate limit", "timeout", 
                        "connection", "network", "temporary"
                    ]):
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Retryable error on attempt {attempt + 1}: {e}. Retrying in {delay}s")
                        time.sleep(delay)
                    else:
                        # Non-retryable error, re-raise immediately
                        raise
        return wrapper
    return decorator


# Global rate limiter instances
polygon_rate_limiter = RateLimiter(calls_per_minute=5, calls_per_day=1000)  # Free tier limits
alpha_vantage_rate_limiter = RateLimiter(calls_per_minute=5, calls_per_day=500)  # Free tier limits

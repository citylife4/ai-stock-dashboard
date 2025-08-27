import json
import random
from typing import Optional
import openai
from ..models import StockData, AIAnalysis
from ..config import config
import logging
from groq import Groq

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.use_mock_analysis = not (config.OPENAI_API_KEY or config.GROQ_API_KEY)
        if config.OPENAI_API_KEY:
            openai.api_key = config.OPENAI_API_KEY
        if config.GROQ_API_KEY:
            self.groq_client = Groq(api_key=config.GROQ_API_KEY)
    
    def analyze_stock(self, stock_data: StockData) -> AIAnalysis:
        """Analyze stock data using AI or mock analysis."""
        try:
            if self.use_mock_analysis:
                return self._generate_mock_analysis(stock_data)
            else:
                if config.GROQ_API_KEY:
                    return self._get_real_analysis_groq(stock_data)
                else:
                    return self._get_real_analysis_open_ai(stock_data)
        except Exception as e:
            logger.error(f"Error analyzing stock {stock_data.symbol}: {e}")
            return self._generate_mock_analysis(stock_data)
       
    def _get_real_analysis_groq(self, stock_data: StockData) -> AIAnalysis:
        """Get real AI analysis using OpenAI."""
        try:
            # Format the prompt with stock data
            prompt = config.AI_ANALYSIS_PROMPT.format(
                symbol=stock_data.symbol,
                current_price=stock_data.current_price,
                previous_close=stock_data.previous_close,
                change_percent=stock_data.change_percent,
                volume=f"{stock_data.volume:,}",
                market_cap=f"{stock_data.market_cap:,}" if stock_data.market_cap else "N/A"
            )
            
            completion = self.groq_client.chat.completions.create(
                model="compound-beta-mini",
                messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst AI. Provide objective stock analysis based on the given data. Only ouput JSON as your response, don't add any extra text. respond anything else"
                },
                {
                    "role": "user",
                    "content": prompt
                }
                ],
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=True,
                stop=None
            )
            analysis_text = ""
            for chunk in completion:
                analysis_text += chunk.choices[0].delta.content or ""

            # Try to parse JSON response
            try:
                logger.info(f"API response for {analysis_text}")
                analysis_json = json.loads(analysis_text)
                score = max(0, min(100, int(analysis_json.get("score", 50))))
                reason = analysis_json.get("reason", "AI analysis completed")
            except json.JSONDecodeError:
                # Fallback if AI doesn't return proper JSON
                score = 50
                reason = analysis_text[:200] if analysis_text else "AI analysis completed"
            
            return AIAnalysis(score=score, reason=reason)
            
        except Exception as e:
            logger.error(f"OpenAI API error for {stock_data.symbol}: {e}")
            return self._generate_mock_analysis(stock_data)

    def _get_real_analysis_open_ai(self, stock_data: StockData) -> AIAnalysis:
        """Get real AI analysis using OpenAI."""
        try:
            # Format the prompt with stock data
            prompt = config.AI_ANALYSIS_PROMPT.format(
                symbol=stock_data.symbol,
                current_price=stock_data.current_price,
                previous_close=stock_data.previous_close,
                change_percent=stock_data.change_percent,
                volume=f"{stock_data.volume:,}",
                market_cap=f"{stock_data.market_cap:,}" if stock_data.market_cap else "N/A"
            )
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial analyst AI. Provide objective stock analysis based on the given data."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            analysis_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                analysis_json = json.loads(analysis_text)
                score = max(0, min(100, int(analysis_json.get("score", 50))))
                reason = analysis_json.get("reason", "AI analysis completed")
            except json.JSONDecodeError:
                # Fallback if AI doesn't return proper JSON
                score = 50
                reason = analysis_text[:200] if analysis_text else "AI analysis completed"
            
            return AIAnalysis(score=score, reason=reason)
            
        except Exception as e:
            logger.error(f"OpenAI API error for {stock_data.symbol}: {e}")
            return self._generate_mock_analysis(stock_data)
    
    def _generate_mock_analysis(self, stock_data: StockData) -> AIAnalysis:
        """Generate realistic mock AI analysis."""
        symbol = stock_data.symbol
        change_percent = stock_data.change_percent
        
        # Base scoring logic
        base_score = 50
        
        # Adjust score based on daily performance
        if change_percent > 2:
            base_score += 20
        elif change_percent > 0:
            base_score += 10
        elif change_percent < -2:
            base_score -= 20
        elif change_percent < 0:
            base_score -= 10
        
        # Add some company-specific adjustments
        company_adjustments = {
            "AAPL": 15,   # Strong brand, consistent performance
            "GOOGL": 10,  # Strong tech fundamentals
            "MSFT": 15,   # Enterprise strength
            "TSLA": 5,    # High volatility, innovation
            "AMZN": 10,   # E-commerce dominance
            "NVDA": 20,   # AI boom beneficiary
            "META": 0,    # Mixed sentiment
            "NFLX": -5    # Competitive streaming market
        }
        
        base_score += company_adjustments.get(symbol, 0)
        
        # Add some randomness for realism
        base_score += random.randint(-10, 10)
        
        # Ensure score is within bounds
        score = max(10, min(90, base_score))
        
        # Generate reasoning based on score and performance
        reasons = self._generate_mock_reasoning(symbol, score, change_percent, stock_data)
        
        return AIAnalysis(score=score, reason=reasons)
    
    def _generate_mock_reasoning(self, symbol: str, score: int, change_percent: float, stock_data: StockData) -> str:
        """Generate realistic reasoning for the mock analysis."""
        
        company_info = {
            "AAPL": "Apple Inc.",
            "GOOGL": "Alphabet Inc.",
            "MSFT": "Microsoft Corporation", 
            "TSLA": "Tesla Inc.",
            "AMZN": "Amazon.com Inc.",
            "NVDA": "NVIDIA Corporation",
            "META": "Meta Platforms Inc.",
            "NFLX": "Netflix Inc."
        }
        
        company_name = company_info.get(symbol, f"{symbol} Corporation")
        
        if score >= 75:
            performance_desc = "strong upward momentum" if change_percent > 0 else "resilient performance despite market conditions"
            outlook = "Excellent investment opportunity with strong fundamentals and positive market sentiment."
        elif score >= 60:
            performance_desc = "steady performance" if abs(change_percent) < 1 else "moderate volatility"
            outlook = "Good investment potential with balanced risk-reward profile."
        elif score >= 40:
            performance_desc = "mixed signals" if abs(change_percent) < 2 else "concerning volatility"
            outlook = "Neutral outlook with moderate investment risk."
        else:
            performance_desc = "declining performance" if change_percent < 0 else "uncertain momentum"
            outlook = "Higher risk investment requiring careful consideration."
        
        volume_analysis = "high trading volume indicates strong investor interest" if stock_data.volume > 100000000 else "moderate trading activity"
        
        return f"{company_name} shows {performance_desc} with a {change_percent:+.1f}% daily change. The {volume_analysis}. {outlook}"
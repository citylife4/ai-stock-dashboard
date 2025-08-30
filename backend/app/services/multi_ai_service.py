from typing import List, Dict, Optional
from datetime import datetime
import logging
from ..models import (
    StockData, AIAnalysis, MultiAIAnalysis, AIModelType, 
    SubscriptionTier, AIModelConfig, SubscriptionLimits
)
from ..config import config
from ..exceptions import OpenAIException, GroqException
from .ai_service import AIService
import openai
from groq import Groq
import json
import random

logger = logging.getLogger(__name__)

class MultiAIService:
    def __init__(self):
        self.basic_ai_service = AIService()
        self.ai_models = self._initialize_ai_models()
        
    def _initialize_ai_models(self) -> Dict[AIModelType, AIModelConfig]:
        """Initialize AI model configurations."""
        return {
            AIModelType.BASIC: AIModelConfig(
                model_type=AIModelType.BASIC,
                name="Basic AI Analyst",
                description="General purpose stock analysis",
                prompt_template=config.get_ai_analysis_prompt(),
                subscription_tiers=[SubscriptionTier.FREE, SubscriptionTier.PRO, SubscriptionTier.EXPERT],
                is_active=True
            ),
            AIModelType.WARREN_BUFFET: AIModelConfig(
                model_type=AIModelType.WARREN_BUFFET,
                name="Warren Buffet Style",
                description="Value investing approach focusing on fundamental analysis",
                prompt_template=self._get_warren_buffet_prompt(),
                subscription_tiers=[SubscriptionTier.PRO, SubscriptionTier.EXPERT],
                is_active=True
            ),
            AIModelType.PETER_LYNCH: AIModelConfig(
                model_type=AIModelType.PETER_LYNCH,
                name="Peter Lynch Style",
                description="Growth at reasonable price (GARP) investment strategy",
                prompt_template=self._get_peter_lynch_prompt(),
                subscription_tiers=[SubscriptionTier.PRO, SubscriptionTier.EXPERT],
                is_active=True
            ),
            AIModelType.DCF_MATH: AIModelConfig(
                model_type=AIModelType.DCF_MATH,
                name="DCF Mathematical",
                description="Quantitative analysis using mathematical models",
                prompt_template=self._get_dcf_math_prompt(),
                subscription_tiers=[SubscriptionTier.EXPERT],
                is_active=True
            )
        }
    
    def get_subscription_limits(self, subscription_tier: SubscriptionTier) -> SubscriptionLimits:
        """Get AI access limits for subscription tier."""
        limits = {
            SubscriptionTier.FREE: SubscriptionLimits(
                max_stocks=5,
                ai_models=[AIModelType.BASIC]
            ),
            SubscriptionTier.PRO: SubscriptionLimits(
                max_stocks=10,
                ai_models=[AIModelType.BASIC, AIModelType.WARREN_BUFFET, AIModelType.PETER_LYNCH]
            ),
            SubscriptionTier.EXPERT: SubscriptionLimits(
                max_stocks=20,
                ai_models=[AIModelType.BASIC, AIModelType.WARREN_BUFFET, AIModelType.PETER_LYNCH, AIModelType.DCF_MATH]
            )
        }
        return limits.get(subscription_tier, limits[SubscriptionTier.FREE])
    
    async def analyze_stock_multi_ai(self, stock_data: StockData, subscription_tier: SubscriptionTier) -> MultiAIAnalysis:
        """Analyze stock using multiple AI models based on subscription tier."""
        limits = self.get_subscription_limits(subscription_tier)
        analyses = []
        
        for ai_model in limits.ai_models:
            if ai_model in self.ai_models and self.ai_models[ai_model].is_active:
                try:
                    analysis = await self._analyze_with_model(stock_data, ai_model)
                    if analysis:
                        analyses.append(analysis)
                except Exception as e:
                    logger.error(f"Error analyzing with {ai_model}: {e}")
                    # Continue with other models
        
        # Calculate average score
        if analyses:
            average_score = sum(analysis.score for analysis in analyses) / len(analyses)
        else:
            # Fallback to basic analysis
            basic_analysis = self.basic_ai_service.analyze_stock(stock_data)
            analyses = [AIAnalysis(
                ai_model=AIModelType.BASIC,
                score=basic_analysis.score,
                reason=basic_analysis.reason
            )]
            average_score = basic_analysis.score
        
        return MultiAIAnalysis(
            analyses=analyses,
            average_score=round(average_score, 1),
            timestamp=datetime.utcnow()
        )
    
    async def _analyze_with_model(self, stock_data: StockData, ai_model: AIModelType) -> Optional[AIAnalysis]:
        """Analyze stock with specific AI model."""
        if ai_model == AIModelType.BASIC:
            basic_analysis = self.basic_ai_service.analyze_stock(stock_data)
            return AIAnalysis(
                ai_model=ai_model,
                score=basic_analysis.score,
                reason=basic_analysis.reason
            )
        
        # Use configured prompt for specialized models
        model_config = self.ai_models[ai_model]
        
        if config.DEBUG or not (config.OPENAI_API_KEY or config.GROQ_API_KEY):
            # Use mock analysis in debug mode or when no API keys available
            return self._generate_mock_analysis(stock_data, ai_model)
        
        try:
            # Use real AI analysis
            prompt = model_config.prompt_template.format(
                symbol=stock_data.symbol,
                current_price=stock_data.current_price,
                previous_close=stock_data.previous_close,
                change_percent=stock_data.change_percent,
                volume=stock_data.volume,
                market_cap=stock_data.market_cap or "N/A"
            )
            
            if config.GROQ_API_KEY:
                return await self._get_analysis_groq(prompt, ai_model)
            else:
                return await self._get_analysis_openai(prompt, ai_model)
                
        except Exception as e:
            logger.error(f"Error in AI analysis for {ai_model}: {e}")
            # Fallback to mock analysis
            return self._generate_mock_analysis(stock_data, ai_model)
    
    async def _get_analysis_openai(self, prompt: str, ai_model: AIModelType) -> Optional[AIAnalysis]:
        """Get analysis from OpenAI."""
        try:
            openai.api_key = config.OPENAI_API_KEY
            
            response = openai.ChatCompletion.create(
                model=config.get_ai_model(),
                messages=[
                    {"role": "system", "content": f"You are a {ai_model.value} style stock analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            analysis_data = json.loads(result)
            
            return AIAnalysis(
                ai_model=ai_model,
                score=int(analysis_data["score"]),
                reason=analysis_data["reason"]
            )
            
        except Exception as e:
            logger.error(f"OpenAI analysis error for {ai_model}: {e}")
            return None
    
    async def _get_analysis_groq(self, prompt: str, ai_model: AIModelType) -> Optional[AIAnalysis]:
        """Get analysis from Groq."""
        try:
            client = Groq(api_key=config.GROQ_API_KEY)
            
            response = client.chat.completions.create(
                model=config.get_ai_model(),
                messages=[
                    {"role": "system", "content": f"You are a {ai_model.value} style stock analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            analysis_data = json.loads(result)
            
            return AIAnalysis(
                ai_model=ai_model,
                score=int(analysis_data["score"]),
                reason=analysis_data["reason"]
            )
            
        except Exception as e:
            logger.error(f"Groq analysis error for {ai_model}: {e}")
            return None
    
    def _generate_mock_analysis(self, stock_data: StockData, ai_model: AIModelType) -> AIAnalysis:
        """Generate mock analysis for development/testing."""
        symbol = stock_data.symbol
        change_percent = stock_data.change_percent
        
        # Base scoring with model-specific adjustments
        base_score = 50
        
        # Model-specific scoring logic
        if ai_model == AIModelType.WARREN_BUFFET:
            # Value-focused scoring
            if change_percent < -5:  # Potential value opportunity
                base_score += 15
            elif change_percent > 5:  # May be overvalued
                base_score -= 10
            base_score += random.randint(-10, 10)
            
        elif ai_model == AIModelType.PETER_LYNCH:
            # Growth-focused scoring
            if change_percent > 2:  # Growth momentum
                base_score += 20
            elif change_percent < -2:  # Growth concerns
                base_score -= 15
            base_score += random.randint(-15, 15)
            
        elif ai_model == AIModelType.DCF_MATH:
            # Math-based scoring
            if stock_data.market_cap and stock_data.market_cap > 100000000000:  # Large cap stability
                base_score += 10
            base_score += int(change_percent * 2)  # Direct correlation with performance
            base_score += random.randint(-5, 5)
            
        else:  # BASIC
            if change_percent > 0:
                base_score += 10
            else:
                base_score -= 10
            base_score += random.randint(-10, 10)
        
        # Ensure score is within bounds
        score = max(0, min(100, base_score))
        
        # Generate model-specific reasoning
        reason = self._generate_model_specific_reasoning(symbol, score, change_percent, ai_model, stock_data)
        
        return AIAnalysis(
            ai_model=ai_model,
            score=score,
            reason=reason
        )
    
    def _generate_model_specific_reasoning(self, symbol: str, score: int, change_percent: float, ai_model: AIModelType, stock_data: StockData) -> str:
        """Generate model-specific reasoning."""
        if ai_model == AIModelType.WARREN_BUFFET:
            if score >= 70:
                return f"{symbol} shows strong value characteristics with a {change_percent:.1f}% daily change. The company demonstrates solid fundamentals and long-term growth potential at current valuations."
            elif score >= 40:
                return f"{symbol} presents mixed value signals. While the {change_percent:.1f}% performance is noteworthy, more analysis of intrinsic value and competitive moats is needed."
            else:
                return f"{symbol} appears overvalued based on current metrics. The {change_percent:.1f}% change suggests market sentiment may be disconnected from fundamental value."
        
        elif ai_model == AIModelType.PETER_LYNCH:
            if score >= 70:
                return f"{symbol} exhibits strong growth momentum with {change_percent:.1f}% daily performance. The company shows promising earnings growth potential at reasonable valuations (GARP strategy)."
            elif score >= 40:
                return f"{symbol} shows moderate growth prospects. The {change_percent:.1f}% change indicates some momentum, but growth sustainability needs closer examination."
            else:
                return f"{symbol} lacks compelling growth characteristics. The {change_percent:.1f}% performance suggests limited near-term growth catalysts."
        
        elif ai_model == AIModelType.DCF_MATH:
            if score >= 70:
                return f"{symbol} demonstrates strong quantitative metrics. Mathematical models suggest fair value above current price based on discounted cash flow analysis and {change_percent:.1f}% performance indicators."
            elif score >= 40:
                return f"{symbol} shows mixed quantitative signals. DCF models indicate neutral valuation with {change_percent:.1f}% performance within expected volatility ranges."
            else:
                return f"{symbol} exhibits concerning mathematical indicators. DCF analysis suggests potential overvaluation with {change_percent:.1f}% performance below model expectations."
        
        else:  # BASIC
            if score >= 70:
                return f"{symbol} shows positive technical and fundamental indicators with {change_percent:.1f}% daily performance suggesting bullish momentum."
            elif score >= 40:
                return f"{symbol} presents mixed signals with {change_percent:.1f}% change. Market conditions appear neutral for this position."
            else:
                return f"{symbol} shows concerning patterns with {change_percent:.1f}% performance indicating potential downside risks."
    
    def _get_warren_buffet_prompt(self) -> str:
        """Get Warren Buffet style analysis prompt."""
        return """
        As Warren Buffet, analyze this stock using value investing principles:
        
        Focus on:
        - Intrinsic value vs market price
        - Competitive moats and market position
        - Long-term growth sustainability
        - Management quality indicators
        - Financial strength and debt levels
        
        Stock Data:
        Symbol: {symbol}
        Current Price: ${current_price}
        Previous Close: ${previous_close}
        Daily Change: {change_percent}%
        Volume: {volume}
        Market Cap: ${market_cap}
        
        Provide a score 0-100 and reasoning focusing on long-term value.
        
        Respond in JSON format:
        {{"score": <number>, "reason": "<value investing perspective>"}}
        """
    
    def _get_peter_lynch_prompt(self) -> str:
        """Get Peter Lynch style analysis prompt."""
        return """
        As Peter Lynch, analyze this stock using GARP (Growth at Reasonable Price) principles:
        
        Focus on:
        - Earnings growth potential
        - PEG ratio considerations
        - Market opportunity size
        - Company story and catalysts
        - Reasonable valuation for growth
        
        Stock Data:
        Symbol: {symbol}
        Current Price: ${current_price}
        Previous Close: ${previous_close}
        Daily Change: {change_percent}%
        Volume: {volume}
        Market Cap: ${market_cap}
        
        Provide a score 0-100 and reasoning focusing on growth at reasonable price.
        
        Respond in JSON format:
        {{"score": <number>, "reason": "<GARP investment perspective>"}}
        """
    
    def _get_dcf_math_prompt(self) -> str:
        """Get DCF mathematical analysis prompt."""
        return """
        As a quantitative analyst, analyze this stock using mathematical models:
        
        Focus on:
        - Discounted Cash Flow (DCF) indicators
        - Statistical valuation metrics
        - Risk-adjusted returns
        - Volatility analysis
        - Mathematical probability models
        
        Stock Data:
        Symbol: {symbol}
        Current Price: ${current_price}
        Previous Close: ${previous_close}
        Daily Change: {change_percent}%
        Volume: {volume}
        Market Cap: ${market_cap}
        
        Provide a score 0-100 and reasoning based on mathematical analysis.
        
        Respond in JSON format:
        {{"score": <number>, "reason": "<mathematical analysis perspective>"}}
        """
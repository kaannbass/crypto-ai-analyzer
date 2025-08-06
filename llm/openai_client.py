"""
OpenAI API client for crypto analysis and trading signals.
Real API integration implemented.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

import config

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = config.OPENAI_API_KEY
        self.timeout = config.AI_TIMEOUT
        self.max_retries = config.AI_MAX_RETRIES
        self.available = bool(self.api_key)
        
        if self.is_available() and OPENAI_AVAILABLE:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.logger.info("OpenAI client initialized successfully")
        else:
            self.client = None
            if not OPENAI_AVAILABLE:
                self.logger.warning("OpenAI package not available")
            else:
                self.logger.warning("OpenAI API key not available")
        
    async def analyze_market_data(self, market_data: Dict, prompt_template: str) -> Optional[Dict]:
        """Analyze market data using OpenAI API."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("OpenAI API not available")
                return None
                
            # Prepare market data for analysis
            market_summary = self.prepare_market_data(market_data)
            
            # Create the analysis prompt
            system_prompt = """You are an expert cryptocurrency trader and analyst. Analyze the provided market data and generate precise trading signals. 

Return ONLY a valid JSON response in this exact format:
{
    "signals": [
        {
            "symbol": "BTCUSDT",
            "action": "BUY/SELL/WAIT",
            "confidence": 0.75,
            "reasoning": "Detailed explanation",
            "entry_price": 50000.0,
            "stop_loss": 48000.0,
            "take_profit": 52000.0
        }
    ],
    "market_sentiment": "Bullish/Bearish/Neutral",
    "risk_level": "Low/Medium/High",
    "summary": "Overall market analysis summary"
}"""

            user_prompt = f"{prompt_template}\n\n### Current Market Data:\n{market_summary}\n\nProvide trading signals for each symbol with confidence scores and specific entry/exit levels."

            # Make API call
            response = await self._make_api_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4o",
                temperature=0.3,
                max_tokens=2000
            )
            
            if response:
                # Parse and validate response
                try:
                    content = response.choices[0].message.content
                    # Clean the response if it has markdown code blocks
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    self.logger.info(f"OpenAI analysis completed successfully with {len(analysis.get('signals', []))} signals")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse OpenAI response: {e}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"OpenAI analysis failed: {e}")
            return None  # Return None instead of mock data
            
    async def analyze_macro_sentiment(self, enhanced_context: Dict, prompt_template: str) -> Optional[Dict]:
        """Analyze market data with macro sentiment and global events using OpenAI API."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("OpenAI API key not available for macro analysis")
                return None # Return None instead of mock data
                
            # Prepare enhanced context
            context_data = json.dumps(enhanced_context, indent=2)
            
            system_prompt = """You are an expert cryptocurrency macro analyst specializing in global economic factors affecting crypto markets. Analyze market conditions, news sentiment, and macro factors.

Return ONLY a valid JSON response in this exact format:
{
    "market_sentiment": {
        "short_term": "Bullish/Bearish/Neutral",
        "medium_term": "Bullish/Bearish/Neutral", 
        "confidence": "High/Medium/Low"
    },
    "signals": [
        {
            "symbol": "BTCUSDT",
            "action": "BUY/SELL/WAIT",
            "confidence": 0.75,
            "reasoning": "Macro-based reasoning"
        }
    ],
    "volatility": "Low/Moderate/High",
    "macro_factors": {
        "primary_risk": "Main risk factor",
        "opportunities": ["opportunity1", "opportunity2"],
        "global_events": ["event1", "event2"]
    },
    "risk_assessment": {
        "market_risk": "Low/Medium/High",
        "liquidity_risk": "Low/Medium/High",
        "regulatory_risk": "Low/Medium/High"
    },
    "summary": "Comprehensive macro analysis summary"
}"""

            user_prompt = f"{prompt_template}\n\n### Current Market Context:\n{context_data}\n\nProvide macro sentiment analysis considering global economic factors, news sentiment, and regulatory environment."

            # Make API call
            response = await self._make_api_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4o",
                temperature=0.2,
                max_tokens=2500
            )
            
            if response:
                try:
                    content = response.choices[0].message.content
                    # Clean the response if it has markdown code blocks
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    analysis['model'] = 'gpt-4-real'
                    self.logger.info("OpenAI macro sentiment analysis completed successfully")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse OpenAI macro response: {e}")
                    return None # Return None instead of mock data
            
            return None
            
        except Exception as e:
            self.logger.error(f"OpenAI macro sentiment analysis failed: {e}")
            return None # Return None instead of mock data

    async def evaluate_news_sentiment(self, news_data: List[Dict]) -> Optional[Dict]:
        """Evaluate news sentiment impact on crypto markets."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("OpenAI API not available for news analysis")
                return None
                
            # Prepare news data
            news_summary = self.prepare_news_data(news_data)
            
            system_prompt = """You are a crypto news sentiment analyst. Analyze the provided news articles and determine their impact on cryptocurrency markets.

Return ONLY a valid JSON response:
{
    "overall_sentiment": "Bullish/Bearish/Neutral",
    "sentiment_strength": 0.75,
    "key_themes": ["theme1", "theme2"],
    "market_impact": "High/Medium/Low",
    "affected_coins": ["BTC", "ETH"],
    "summary": "News sentiment summary"
}"""

            user_prompt = f"Analyze these crypto news articles:\n\n{news_summary}\n\nDetermine overall market sentiment and potential price impact."

            response = await self._make_api_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4o",
                temperature=0.3,
                max_tokens=1000
            )
            
            if response:
                try:
                    content = response.choices[0].message.content
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    self.logger.info("OpenAI news sentiment analysis completed")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse news sentiment response: {e}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"News sentiment analysis failed: {e}")
            return None
            
    async def analyze_pump_sustainability(self, pump_data: Dict) -> Optional[Dict]:
        """Analyze if a detected pump is sustainable or a fakeout."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("OpenAI API not available for pump analysis")
                return None
                
            pump_info = json.dumps(pump_data, indent=2)
            
            system_prompt = """You are a crypto pump/dump detection expert. Analyze the provided pump data to determine if it's sustainable or a fakeout.

Return ONLY a valid JSON response:
{
    "sustainability": "Sustainable/Fakeout/Uncertain",
    "confidence": 0.75,
    "reasoning": "Detailed analysis",
    "recommended_action": "BUY/SELL/WAIT",
    "risk_level": "Low/Medium/High"
}"""

            user_prompt = f"Analyze this pump data:\n\n{pump_info}\n\nDetermine if this pump is sustainable or likely a fakeout."

            response = await self._make_api_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4o",
                temperature=0.3,
                max_tokens=800
            )
            
            if response:
                try:
                    content = response.choices[0].message.content
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    self.logger.info("OpenAI pump sustainability analysis completed")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse pump analysis response: {e}")
                    return None
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Pump analysis failed: {e}")
            return None
            
    async def get_daily_market_overview(self, market_data: Dict) -> Optional[Dict]:
        """Get comprehensive daily market overview."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("OpenAI API not available for market overview")
                return None
                
            market_summary = self.prepare_market_data(market_data)
            
            system_prompt = """You are a crypto market analyst providing daily market overviews. Analyze the market data and provide comprehensive insights.

Return ONLY a valid JSON response:
{
    "market_phase": "Bull/Bear/Sideways",
    "dominant_trend": "Bullish/Bearish/Neutral",
    "key_movers": ["BTC", "ETH"],
    "sector_rotation": "Description of sector movements",
    "support_resistance": {
        "BTCUSDT": {"support": 45000, "resistance": 50000}
    },
    "outlook": "24h market outlook",
    "recommended_strategy": "Trend/Range/Breakout trading"
}"""

            user_prompt = f"Provide daily market overview:\n\n{market_summary}\n\nAnalyze current market phase, trends, and provide trading recommendations."

            response = await self._make_api_call(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-4o",
                temperature=0.4,
                max_tokens=1500
            )
            
            if response:
                try:
                    content = response.choices[0].message.content
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    self.logger.info("OpenAI daily market overview completed")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse market overview response: {e}")
                    return None
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Daily overview analysis failed: {e}")
            return None

    async def get_completion(self, prompt: str, model: str = "gpt-4o", max_tokens: int = 500) -> Optional[str]:
        """Get a simple text completion from OpenAI."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("OpenAI API not available for completion")
                return None
                
            response = await self._make_api_call(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=model,
                temperature=0.3,
                max_tokens=max_tokens
            )
            
            if response and response.choices:
                content = response.choices[0].message.content
                self.logger.info("OpenAI completion successful")
                return content.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"OpenAI completion failed: {e}")
            return None

    async def _make_api_call(self, messages: List[Dict], model: str = "gpt-4o", 
                           temperature: float = 0.3, max_tokens: int = 2000) -> Optional[object]:
        """Make an API call to OpenAI with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=self.timeout
                    ),
                    timeout=self.timeout + 5
                )
                return response
                
            except asyncio.TimeoutError:
                self.logger.warning(f"OpenAI API timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                self.logger.error(f"OpenAI API call failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    
        return None

    def prepare_market_data(self, market_data: Dict) -> str:
        """Prepare market data for AI analysis."""
        summary = "Current Market Data:\n"
        for symbol, data in market_data.items():
            price = data.get('price', 0)
            change_24h = data.get('change_24h', 0) * 100
            volume = data.get('volume', 0)
            
            summary += f"\n{symbol}:"
            summary += f"\n  Price: ${price:,.2f}"
            summary += f"\n  24h Change: {change_24h:+.2f}%"
            summary += f"\n  Volume: ${volume:,.0f}"
            
        return summary

    def prepare_news_data(self, news_data: List[Dict]) -> str:
        """Prepare news data for AI analysis."""
        summary = "Recent Crypto News:\n"
        for i, article in enumerate(news_data[:10], 1):  # Top 10 articles
            title = article.get('title', 'No title')
            source = article.get('source', 'Unknown')
            summary += f"\n{i}. {title} (Source: {source})"
            
        return summary
            
    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        return self.available

    def _disable(self, reason: str):
        """Disable client after critical errors."""
        self.available = False
        self.logger.error(f"OpenAI client disabled: {reason}")
        
    async def test_connection(self) -> bool:
        """Test connection to OpenAI API."""
        try:
            if not self.is_available() or not self.client:
                return False
                
            # Test with a simple API call
            response = await self._make_api_call(
                messages=[
                    {"role": "user", "content": "Hello, this is a connection test. Please respond with 'Connected'."}
                ],
                model="gpt-3.5-turbo",  # Use cheaper model for testing
                temperature=0.1,
                max_tokens=10
            )
            
            if response and response.choices:
                self.logger.info("OpenAI API connection test successful")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"OpenAI connection test failed: {e}")
            return False 
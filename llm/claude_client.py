"""
Claude API client for crypto analysis and trading signals.
Real API integration implemented.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

import config

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False


class ClaudeClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = config.CLAUDE_API_KEY
        self.timeout = config.AI_TIMEOUT
        self.max_retries = config.AI_MAX_RETRIES
        
        if self.is_available() and CLAUDE_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.logger.info("Claude client initialized successfully")
        else:
            self.client = None
            if not CLAUDE_AVAILABLE:
                self.logger.warning("Anthropic package not available")
            else:
                self.logger.warning("Claude API key not available")
        
    async def analyze_market_data(self, market_data: Dict, prompt_template: str) -> Optional[Dict]:
        """Analyze market data using Claude API."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("Claude API not available")
                return self.generate_mock_analysis(market_data)
                
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
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2000
            )
            
            if response:
                # Parse and validate response
                try:
                    content = response.content[0].text if response.content else ""
                    # Clean the response if it has markdown code blocks
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    analysis['model'] = 'claude-3-real'
                    self.logger.info(f"Claude analysis completed successfully with {len(analysis.get('signals', []))} signals")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse Claude response: {e}")
                    return self.generate_mock_analysis(market_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Claude analysis failed: {e}")
            return self.generate_mock_analysis(market_data)
        
    async def analyze_macro_sentiment(self, enhanced_context: Dict, prompt_template: str) -> Optional[Dict]:
        """Analyze market data with macro sentiment and global events using Claude API."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("Claude API key not available for macro analysis")
                market_data = enhanced_context.get('market_data', {})
                return self.generate_mock_macro_analysis(market_data, enhanced_context)
                
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
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=2500
            )
            
            if response:
                try:
                    content = response.content[0].text if response.content else ""
                    # Clean the response if it has markdown code blocks
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    analysis['model'] = 'claude-3-real'
                    self.logger.info("Claude macro sentiment analysis completed successfully")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse Claude macro response: {e}")
                    market_data = enhanced_context.get('market_data', {})
                    return self.generate_mock_macro_analysis(market_data, enhanced_context)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Claude macro sentiment analysis failed: {e}")
            market_data = enhanced_context.get('market_data', {})
            return self.generate_mock_macro_analysis(market_data, enhanced_context)

    def generate_mock_macro_analysis(self, market_data: Dict, context: Dict) -> Dict:
        """Generate mock macro sentiment analysis for testing (Claude perspective)."""
        signals = []
        abnormal_coins = []
        
        for symbol, data in market_data.items():
            price_change = data.get('change_24h', 0)
            volume_change = data.get('volume_change_24h', 0)
            current_price = data.get('price', 0)
            
            # Claude's more conservative approach
            if price_change > 0.07 and volume_change > 0.3:  # Higher threshold for BUY
                action = 'BUY'
                confidence = 0.7
                reason = f"Strong bullish confirmation with significant volume (+{volume_change*100:.1f}%)"
            elif price_change < -0.07 and volume_change > 0.3:  # Higher threshold for SELL
                action = 'SELL'
                confidence = 0.65
                reason = f"Bearish breakdown confirmed by volume spike"
            elif abs(price_change) > 0.1:  # Very extreme moves
                action = 'WAIT'
                confidence = 0.5
                reason = f"Extreme volatility ({price_change*100:.1f}%) requires caution"
                
                # Add to abnormal coins with more detailed analysis
                movement_type = 'pump' if price_change > 0.1 else 'dump' if price_change < -0.1 else 'wave'
                abnormal_coins.append({
                    'symbol': symbol,
                    'movement': movement_type,
                    'magnitude': f"{price_change*100:+.1f}%",
                    'reason': f'Unusual {movement_type} pattern with {volume_change*100:+.1f}% volume change'
                })
            else:
                action = 'WAIT'
                confidence = 0.25
                reason = "Insufficient signal strength for confident directional bias"
            
            # More conservative stop losses
            if action == 'BUY':
                stop_loss = current_price * 0.96  # 4% stop loss
                take_profit = current_price * 1.05  # 5% take profit
            elif action == 'SELL':
                stop_loss = current_price * 1.04  # 4% stop loss for short
                take_profit = current_price * 0.95  # 5% take profit for short
            else:
                stop_loss = current_price
                take_profit = current_price
            
            signals.append({
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'reason': reason,
                'confidence_level': 'High' if confidence > 0.65 else 'Medium' if confidence > 0.4 else 'Low',
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit
            })
        
        # More nuanced sentiment analysis
        positive_changes = sum(1 for symbol, data in market_data.items() if data.get('change_24h', 0) > 0)
        strong_positive = sum(1 for symbol, data in market_data.items() if data.get('change_24h', 0) > 0.05)
        total_coins = len(market_data)
        
        if strong_positive / total_coins > 0.5:
            short_term = 'Bullish'
            medium_term = 'Bullish'
            volatility = 'High'
        elif positive_changes / total_coins < 0.3:
            short_term = 'Bearish'
            medium_term = 'Bearish'
            volatility = 'High'
        else:
            short_term = 'Neutral'
            medium_term = 'Neutral'
            volatility = 'Moderate'
        
        return {
            'model': 'claude-3-mock',
            'summary': f"Market analysis reveals {short_term.lower()} bias with {strong_positive} coins showing strong momentum. Risk-adjusted positioning recommended given current volatility environment.",
            'market_sentiment': {
                'short_term': short_term,
                'medium_term': medium_term,
                'confidence': 'Medium'
            },
            'signals': signals,
            'volatility': volatility,
            'abnormal_coins': abnormal_coins[:3],  # Top 3 abnormal movements
            'macro_factors': {
                'primary_risk': 'Central bank policy divergence creating cross-asset volatility',
                'opportunities': ['Layer 2 scaling adoption', 'Corporate treasury diversification'],
                'global_events': ['ECB policy meeting', 'Regulatory framework developments']
            },
            'risk_assessment': {
                'market_risk': 'Medium',
                'liquidity_risk': 'Low',
                'regulatory_risk': 'High'
            }
        }
        
    async def evaluate_risk_factors(self, market_data: Dict, external_factors: Dict = None) -> Optional[Dict]:
        """Evaluate comprehensive risk factors."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("Claude API not available for risk analysis")
                return None
                
            # Prepare risk analysis data
            market_summary = self.prepare_market_data(market_data)
            external_summary = json.dumps(external_factors or {}, indent=2)
            
            system_prompt = """You are a cryptocurrency risk assessment expert. Analyze market conditions and external factors to provide comprehensive risk evaluation.

Return ONLY a valid JSON response:
{
    "overall_risk": "Low/Medium/High",
    "risk_factors": [
        {
            "factor": "Risk factor name",
            "impact": "Low/Medium/High",
            "description": "Detailed description"
        }
    ],
    "recommendations": [
        "Risk management recommendation 1",
        "Risk management recommendation 2"
    ],
    "position_sizing": "Conservative/Moderate/Aggressive",
    "max_exposure": 0.20,
    "stop_loss_tight": true
}"""

            user_prompt = f"Analyze risk factors:\n\nMarket Data:\n{market_summary}\n\nExternal Factors:\n{external_summary}\n\nProvide comprehensive risk assessment."

            response = await self._make_api_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1500
            )
            
            if response:
                try:
                    content = response.content[0].text if response.content else ""
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    self.logger.info("Claude risk factor analysis completed")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse risk analysis response: {e}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Risk evaluation failed: {e}")
            return None
            
    async def analyze_anomalies(self, anomalies: List[Dict]) -> Optional[Dict]:
        """Analyze detected market anomalies."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("Claude API not available for anomaly analysis")
                return None
                
            if not anomalies:
                return {'analysis': 'No anomalies to analyze'}
                
            anomaly_data = json.dumps(anomalies, indent=2)
            
            system_prompt = """You are a cryptocurrency anomaly detection expert. Analyze unusual market movements and determine their significance.

Return ONLY a valid JSON response:
{
    "anomaly_significance": "Low/Medium/High",
    "pattern_type": "Pump/Dump/Whale Activity/Manipulation",
    "sustainability": "Likely Sustainable/Likely Reversal/Uncertain",
    "recommended_action": "BUY/SELL/WAIT/MONITOR",
    "confidence": 0.75,
    "reasoning": "Detailed analysis of the anomaly"
}"""

            user_prompt = f"Analyze these market anomalies:\n\n{anomaly_data}\n\nDetermine significance and provide trading recommendations."

            response = await self._make_api_call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1000
            )
            
            if response:
                try:
                    content = response.content[0].text if response.content else ""
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    
                    analysis = json.loads(content.strip())
                    self.logger.info("Claude anomaly analysis completed")
                    return analysis
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse anomaly analysis response: {e}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.error(f"Anomaly analysis failed: {e}")
            return None

    async def _make_api_call(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> Optional[object]:
        """Make an API call to Claude with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.messages.create,
                        model="claude-3-haiku-20240307",  # Using Haiku for faster responses
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=max_tokens,
                        timeout=self.timeout
                    ),
                    timeout=self.timeout + 5
                )
                return response
                
            except asyncio.TimeoutError:
                self.logger.warning(f"Claude API timeout (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
            except Exception as e:
                self.logger.error(f"Claude API call failed (attempt {attempt + 1}): {e}")
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

    def generate_mock_analysis(self, market_data: Dict) -> Dict:
        """Generate mock analysis for market data."""
        signals = []
        
        for symbol, data in market_data.items():
            price_change = data.get('change_24h', 0)
            current_price = data.get('price', 0)
            
            # Claude tends to be more conservative
            if price_change > 0.03:  # 3% threshold
                action = 'BUY'
                confidence = min(0.7, 0.5 + abs(price_change))
                reason = f"Positive momentum (+{price_change*100:.1f}%) with controlled risk"
            elif price_change < -0.03:
                action = 'SELL'
                confidence = min(0.65, 0.5 + abs(price_change))
                reason = f"Bearish trend ({price_change*100:.1f}%) suggests downside"
            else:
                action = 'WAIT'
                confidence = 0.4
                reason = "Sideways action - waiting for clearer directional signal"
            
            signals.append({
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'reasoning': reason,
                'entry_price': current_price,
                'stop_loss': current_price * (0.98 if action == 'BUY' else 1.02),
                'take_profit': current_price * (1.03 if action == 'BUY' else 0.97)
            })
        
        return {
            'model': 'claude-3-mock',
            'signals': signals,
            'market_sentiment': 'Neutral',
            'risk_level': 'Medium',
            'summary': 'Conservative analysis focusing on risk management and clear signals only.'
        }

    def generate_mock_macro_analysis(self, market_data: Dict, context: Dict) -> Dict:
        """Generate mock macro sentiment analysis for testing."""
        signals = []
        
        # Claude's conservative approach to macro analysis
        for symbol, data in market_data.items():
            price_change = data.get('change_24h', 0)
            current_price = data.get('price', 0)
            
            # More conservative thresholds for macro analysis
            if price_change > 0.04:  # 4% threshold for macro signals
                action = 'BUY'
                confidence = min(0.65, 0.4 + abs(price_change))
                reason = f"Macro factors support upside with {price_change*100:.1f}% momentum"
            elif price_change < -0.04:
                action = 'SELL'
                confidence = min(0.6, 0.4 + abs(price_change))
                reason = f"Macro headwinds suggest caution with {price_change*100:.1f}% decline"
            else:
                action = 'WAIT'
                confidence = 0.3
                reason = "Macro environment mixed - waiting for clearer catalyst"
            
            signals.append({
                'symbol': symbol,
                'action': action,
                'confidence': confidence,
                'reasoning': reason
            })
        
        # Conservative macro assessment
        positive_changes = sum(1 for symbol, data in market_data.items() if data.get('change_24h', 0) > 0)
        total_coins = len(market_data) if market_data else 1
        
        if positive_changes / total_coins > 0.65:
            short_term = 'Bullish'
            medium_term = 'Neutral'
            confidence = 'Medium'
        elif positive_changes / total_coins < 0.35:
            short_term = 'Bearish'
            medium_term = 'Neutral'
            confidence = 'Medium'
        else:
            short_term = 'Neutral'
            medium_term = 'Neutral'
            confidence = 'Low'
        
        return {
            'model': 'claude-3-mock',
            'summary': f"Conservative macro analysis shows {short_term.lower()} short-term sentiment. Risk management remains paramount in current environment.",
            'market_sentiment': {
                'short_term': short_term,
                'medium_term': medium_term,
                'confidence': confidence
            },
            'signals': signals,
            'volatility': 'Moderate',
            'macro_factors': {
                'primary_risk': 'Global economic uncertainty affecting crypto adoption',
                'opportunities': ['Institutional infrastructure development', 'Regulatory clarity improvements'],
                'global_events': ['Central bank policy decisions', 'Regulatory developments']
            },
            'risk_assessment': {
                'market_risk': 'Medium',
                'liquidity_risk': 'Low',
                'regulatory_risk': 'Medium'
            }
        }
        
    def is_available(self) -> bool:
        """Check if Claude API is available."""
        return bool(self.api_key and self.api_key.strip())
        
    async def test_connection(self) -> bool:
        """Test connection to Claude API."""
        try:
            if not self.is_available() or not self.client:
                return False
                
            # Test with a simple API call
            response = await self._make_api_call(
                system_prompt="You are a helpful assistant.",
                user_prompt="Hello, this is a connection test. Please respond with 'Connected'.",
                max_tokens=10
            )
            
            if response and response.content:
                self.logger.info("Claude API connection test successful")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Claude connection test failed: {e}")
            return False 

    async def get_completion(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Get a simple text completion from Claude."""
        try:
            if not self.is_available() or not self.client:
                self.logger.warning("Claude API not available for completion")
                return None
                
            response = await self._make_api_call(
                system_prompt="You are a helpful cryptocurrency analyst. Provide concise, accurate responses in Turkish.",
                user_prompt=prompt,
                max_tokens=max_tokens
            )
            
            if response and response.content:
                content = response.content[0].text if response.content else ""
                self.logger.info("Claude completion successful")
                return content.strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Claude completion failed: {e}")
            return None 
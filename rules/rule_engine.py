"""
Rule-based trading engine with technical indicators.
Provides fallback logic when AI is unavailable.
"""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import config


class RuleEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.price_history = {}
        
    def calculate_rsi(self, prices: List[float], period: int = None) -> float:
        """Calculate RSI (Relative Strength Index)."""
        if period is None:
            period = config.RSI_PERIOD
            
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if insufficient data
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < config.MACD_SLOW + config.MACD_SIGNAL:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
            
        # Calculate EMAs
        ema_fast = self.calculate_ema(prices, config.MACD_FAST)
        ema_slow = self.calculate_ema(prices, config.MACD_SLOW)
        
        macd_line = ema_fast - ema_slow
        
        # Calculate MACD signal line (EMA of MACD line)
        macd_history = [macd_line] * config.MACD_SIGNAL  # Simplified
        signal_line = self.calculate_ema(macd_history, config.MACD_SIGNAL)
        
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
        
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return sum(prices) / len(prices) if prices else 0
            
        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # Start with SMA
        
        for price in prices[period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
            
        return ema
        
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            avg_price = sum(prices) / len(prices) if prices else 0
            return {'upper': avg_price, 'middle': avg_price, 'lower': avg_price}
            
        recent_prices = prices[-period:]
        sma = sum(recent_prices) / period
        
        variance = sum((price - sma) ** 2 for price in recent_prices) / period
        std_deviation = math.sqrt(variance)
        
        upper_band = sma + (std_deviation * std_dev)
        lower_band = sma - (std_deviation * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
        
    def analyze_volume(self, current_volume: float, volume_history: List[float]) -> Dict[str, float]:
        """Analyze volume patterns."""
        if not volume_history:
            return {'volume_ratio': 1.0, 'volume_trend': 'neutral'}
            
        avg_volume = sum(volume_history) / len(volume_history)
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Determine volume trend
        if volume_ratio > config.VOLUME_THRESHOLD:
            trend = 'high'
        elif volume_ratio < 0.7:
            trend = 'low'
        else:
            trend = 'normal'
            
        return {
            'volume_ratio': volume_ratio,
            'volume_trend': trend,
            'avg_volume': avg_volume
        }
        
    async def generate_signal(self, symbol: str, market_data: Dict) -> Optional[Dict]:
        """Generate trading signal based on technical analysis."""
        try:
            # Get real historical price data
            prices = await self.get_price_history(symbol, market_data)
            
            if len(prices) < 50:  # Need sufficient data
                self.logger.warning(f"Insufficient historical data for {symbol} ({len(prices)} prices)")
                return None
                
            current_price = prices[-1]
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(prices)
            macd_data = self.calculate_macd(prices)
            bb_data = self.calculate_bollinger_bands(prices)
            
            # Get real volume data from market data
            current_volume = market_data.get('volume', 0)
            if current_volume <= 0:
                self.logger.warning(f"No volume data available for {symbol}")
                return None
                
            volume_data = self.analyze_volume(
                current_volume,
                [current_volume]  # Single volume point - real volume analysis would need historical volume
            )
            
            # Generate signal based on indicators
            signal = self.evaluate_indicators(
                symbol, current_price, rsi, macd_data, bb_data, volume_data
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {e}")
            return None
            
    async def get_price_history(self, symbol: str, market_data: Dict) -> List[float]:
        """Get price history for symbol using real data sources."""
        try:
            # Import data manager for real historical data
            from data_sources.data_manager import DataManager
            
            data_manager = DataManager()
            historical_data = await data_manager.get_historical_data(symbol, interval='1h', limit=100)
            
            if historical_data:
                # Extract close prices from historical data
                prices = [float(candle['close']) for candle in historical_data]
                self.logger.info(f"Retrieved {len(prices)} historical prices for {symbol}")
                return prices
            else:
                self.logger.warning(f"No historical data available for {symbol}")
                # Return just current price if no historical data
                current_price = market_data.get('price', 0)
                if current_price > 0:
                    return [current_price]
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting price history for {symbol}: {e}")
            return []
        
    def evaluate_indicators(self, symbol: str, current_price: float, rsi: float, 
                          macd_data: Dict, bb_data: Dict, volume_data: Dict) -> Dict:
        """Evaluate all indicators to generate final signal."""
        signals = []
        confidence = 0.0
        reasoning_parts = []
        
        # RSI Analysis
        if rsi < config.RSI_OVERSOLD:
            signals.append('BUY')
            confidence += 0.3
            reasoning_parts.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > config.RSI_OVERBOUGHT:
            signals.append('SELL')
            confidence += 0.3
            reasoning_parts.append(f"RSI overbought ({rsi:.1f})")
            
        # MACD Analysis
        if macd_data['histogram'] > 0 and macd_data['macd'] > macd_data['signal']:
            signals.append('BUY')
            confidence += 0.25
            reasoning_parts.append("MACD bullish crossover")
        elif macd_data['histogram'] < 0 and macd_data['macd'] < macd_data['signal']:
            signals.append('SELL')
            confidence += 0.25
            reasoning_parts.append("MACD bearish crossover")
            
        # Bollinger Bands Analysis
        if current_price <= bb_data['lower']:
            signals.append('BUY')
            confidence += 0.2
            reasoning_parts.append("Price at lower Bollinger Band")
        elif current_price >= bb_data['upper']:
            signals.append('SELL')
            confidence += 0.2
            reasoning_parts.append("Price at upper Bollinger Band")
            
        # Volume Analysis
        if volume_data['volume_trend'] == 'high':
            confidence += 0.15
            reasoning_parts.append(f"High volume ({volume_data['volume_ratio']:.1f}x avg)")
        elif volume_data['volume_trend'] == 'low':
            confidence -= 0.1
            reasoning_parts.append("Low volume concern")
            
        # Determine final action
        buy_signals = signals.count('BUY')
        sell_signals = signals.count('SELL')
        
        if buy_signals > sell_signals:
            action = 'BUY'
        elif sell_signals > buy_signals:
            action = 'SELL'
        else:
            action = 'WAIT'
            confidence *= 0.5  # Reduce confidence for conflicting signals
            
        # Ensure minimum confidence threshold
        if confidence < 0.3:
            action = 'WAIT'
            
        return {
            'symbol': symbol,
            'action': action,
            'confidence': min(confidence, 1.0),
            'reasoning': '; '.join(reasoning_parts) if reasoning_parts else 'No clear signal',
            'indicators': {
                'rsi': rsi,
                'macd': macd_data,
                'bollinger_bands': bb_data,
                'volume': volume_data
            },
            'current_price': current_price,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    def detect_anomaly(self, symbol: str, market_data: Dict) -> Optional[Dict]:
        """Detect market anomalies for hourly scanning."""
        try:
            current_price = market_data.get('price', 0)
            volume = market_data.get('volume', 0)
            change_24h = market_data.get('change_24h', 0)
            
            if current_price <= 0 or volume <= 0:
                self.logger.warning(f"Invalid market data for {symbol}")
                return None
            
            anomalies = []
            
            # Price anomaly detection
            if abs(change_24h) > 0.15:  # 15% change
                anomalies.append(f"Large 24h price change: {change_24h:.1%}")
                
            # Volume anomaly detection - requires historical volume data for proper analysis
            # For now, detect if volume is significantly high compared to a baseline
            # In a real implementation, this should use historical volume averages
            
            if anomalies:
                return {
                    'symbol': symbol,
                    'anomalies': anomalies,
                    'severity': 'high' if len(anomalies) > 1 else 'medium',
                    'suggested_action': 'BUY' if change_24h > 0 else 'SELL',
                    'confidence': min(len(anomalies) * 0.3, 0.8),
                    'reasoning': '; '.join(anomalies),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting anomaly for {symbol}: {e}")
            return None 
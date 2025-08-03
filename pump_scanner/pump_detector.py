"""
Pump detection engine for identifying significant price movements with volume confirmation.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import config


class PumpDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.price_history = {}
        self.volume_history = {}
        self.detected_pumps = []
        
    async def detect_anomaly(self, symbol: str, market_data: Dict) -> Optional[Dict]:
        """Detect market anomalies for a specific symbol."""
        try:
            price_change = market_data.get('change_24h', 0)
            volume = market_data.get('volume', 0)
            current_price = market_data.get('price', 0)
            
            # Define anomaly thresholds
            pump_threshold = config.PUMP_PRICE_THRESHOLD  # 5% by default
            volume_threshold = config.PUMP_VOLUME_THRESHOLD  # 3x by default
            
            # Check for price pump
            if price_change > pump_threshold:
                volume_ratio = self.calculate_volume_ratio(symbol, volume)
                
                if volume_ratio > volume_threshold:
                    anomaly = {
                        'symbol': symbol,
                        'type': 'pump',
                        'price_change': price_change,
                        'volume_ratio': volume_ratio,
                        'current_price': current_price,
                        'timestamp': datetime.utcnow().isoformat(),
                        'confidence': min(0.9, (price_change / pump_threshold + volume_ratio / volume_threshold) / 2)
                    }
                    self.logger.info(f"Anomaly detected for {symbol}: {price_change*100:.1f}% price change with {volume_ratio:.1f}x volume")
                    return anomaly
            
            # Check for dump
            elif price_change < -pump_threshold:
                volume_ratio = self.calculate_volume_ratio(symbol, volume)
                
                if volume_ratio > volume_threshold:
                    anomaly = {
                        'symbol': symbol,
                        'type': 'dump',
                        'price_change': price_change,
                        'volume_ratio': volume_ratio,
                        'current_price': current_price,
                        'timestamp': datetime.utcnow().isoformat(),
                        'confidence': min(0.9, (abs(price_change) / pump_threshold + volume_ratio / volume_threshold) / 2)
                    }
                    self.logger.info(f"Anomaly detected for {symbol}: {price_change*100:.1f}% price drop with {volume_ratio:.1f}x volume")
                    return anomaly
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting anomaly for {symbol}: {e}")
            return None

    def calculate_volume_ratio(self, symbol: str, current_volume: float) -> float:
        """Calculate volume ratio compared to historical average."""
        try:
            # Get historical volume for this symbol
            if symbol not in self.volume_history:
                self.volume_history[symbol] = []
            
            # Add current volume to history
            self.volume_history[symbol].append(current_volume)
            
            # Keep only last 24 volume readings
            if len(self.volume_history[symbol]) > 24:
                self.volume_history[symbol] = self.volume_history[symbol][-24:]
            
            # Calculate average
            if len(self.volume_history[symbol]) < 2:
                return 1.0  # No historical data, assume normal
            
            avg_volume = sum(self.volume_history[symbol][:-1]) / (len(self.volume_history[symbol]) - 1)
            
            if avg_volume > 0:
                return current_volume / avg_volume
            else:
                return 1.0
                
        except Exception as e:
            self.logger.error(f"Error calculating volume ratio for {symbol}: {e}")
            return 1.0
        
    async def scan_for_pumps(self) -> List[Dict]:
        """Scan all configured symbols for pump opportunities."""
        try:
            pumps_detected = []
            
            # Get current market data
            market_data = await self.get_current_market_data()
            
            for symbol in config.SYMBOLS:
                if symbol in market_data:
                    pump = await self.analyze_symbol_for_pump(symbol, market_data[symbol])
                    if pump:
                        pumps_detected.append(pump)
                        
            # Filter out recently detected pumps to avoid duplicates
            new_pumps = self.filter_recent_pumps(pumps_detected)
            
            # Update detected pumps history
            self.detected_pumps.extend(new_pumps)
            
            # Clean old pump records
            self.cleanup_old_pumps()
            
            if new_pumps:
                self.logger.info(f"Detected {len(new_pumps)} new pumps: {[p['symbol'] for p in new_pumps]}")
                
            return new_pumps
            
        except Exception as e:
            self.logger.error(f"Pump scanning failed: {e}")
            return []
            
    async def analyze_symbol_for_pump(self, symbol: str, current_data: Dict) -> Optional[Dict]:
        """Analyze a single symbol for pump characteristics."""
        try:
            current_price = current_data.get('price', 0)
            current_volume = current_data.get('volume', 0)
            change_24h = current_data.get('change_24h', 0)
            
            if current_price <= 0:
                return None
                
            # Get historical data for comparison
            historical_data = await self.get_historical_data(symbol)
            
            if not historical_data:
                return None
                
            # Calculate price change metrics
            price_metrics = self.calculate_price_metrics(
                current_price, historical_data['prices']
            )
            
            # Calculate volume metrics
            volume_metrics = self.calculate_volume_metrics(
                current_volume, historical_data['volumes']
            )
            
            # Determine if this qualifies as a pump
            pump_signal = self.evaluate_pump_criteria(
                symbol, price_metrics, volume_metrics, change_24h
            )
            
            return pump_signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol} for pump: {e}")
            return None
            
    def calculate_price_metrics(self, current_price: float, price_history: List[float]) -> Dict:
        """Calculate price-based pump metrics."""
        if not price_history:
            return {'price_change_1h': 0, 'price_change_15m': 0, 'avg_price_1h': current_price}
            
        # Use actual time-series data for calculation
        recent_prices = price_history[-12:]  # Last 12 data points (assuming 5min intervals)
        avg_price_1h = sum(recent_prices) / len(recent_prices) if recent_prices else current_price
        
        # Calculate short-term changes
        price_change_1h = (current_price - avg_price_1h) / avg_price_1h if avg_price_1h > 0 else 0
        
        # Approximate 15-minute change
        if len(recent_prices) >= 3:
            price_15m_ago = recent_prices[-3]
            price_change_15m = (current_price - price_15m_ago) / price_15m_ago if price_15m_ago > 0 else 0
        else:
            price_change_15m = price_change_1h
            
        return {
            'price_change_1h': price_change_1h,
            'price_change_15m': price_change_15m,
            'avg_price_1h': avg_price_1h,
            'current_price': current_price
        }
        
    def calculate_volume_metrics(self, current_volume: float, volume_history: List[float]) -> Dict:
        """Calculate volume-based pump metrics."""
        if not volume_history:
            return {'volume_ratio': 1.0, 'avg_volume': current_volume}
            
        # Calculate average volume
        recent_volumes = volume_history[-24:]  # Last 24 periods (approximately 2 hours)
        avg_volume = sum(recent_volumes) / len(recent_volumes) if recent_volumes else current_volume
        
        # Volume ratio
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Volume trend (increasing vs decreasing)
        if len(recent_volumes) >= 6:
            recent_avg = sum(recent_volumes[-6:]) / 6
            older_avg = sum(recent_volumes[-12:-6]) / 6 if len(recent_volumes) >= 12 else recent_avg
            volume_trend = 'increasing' if recent_avg > older_avg * 1.2 else 'stable'
        else:
            volume_trend = 'unknown'
            
        return {
            'volume_ratio': volume_ratio,
            'avg_volume': avg_volume,
            'current_volume': current_volume,
            'volume_trend': volume_trend
        }
        
    def evaluate_pump_criteria(self, symbol: str, price_metrics: Dict, 
                             volume_metrics: Dict, change_24h: float) -> Optional[Dict]:
        """Evaluate if the symbol meets pump criteria."""
        price_change_15m = price_metrics.get('price_change_15m', 0)
        price_change_1h = price_metrics.get('price_change_1h', 0)
        volume_ratio = volume_metrics.get('volume_ratio', 1.0)
        
        # Primary pump criteria
        meets_price_threshold = price_change_15m >= config.PUMP_PRICE_THRESHOLD
        meets_volume_threshold = volume_ratio >= config.PUMP_VOLUME_THRESHOLD
        
        # Additional quality filters
        reasonable_24h_change = abs(change_24h) <= 0.5  # Not more than 50% in 24h (to avoid outliers)
        volume_trend_positive = volume_metrics.get('volume_trend') in ['increasing', 'unknown']
        
        # Score the pump quality
        pump_score = 0.0
        
        if meets_price_threshold:
            pump_score += 0.4
            
        if meets_volume_threshold:
            pump_score += 0.3
            
        if price_change_1h > price_change_15m * 0.5:  # Sustained movement
            pump_score += 0.2
            
        if volume_trend_positive:
            pump_score += 0.1
            
        # Determine pump classification
        if pump_score >= 0.6 and meets_price_threshold and meets_volume_threshold:
            pump_type = 'strong'
            confidence = min(pump_score, 0.9)
        elif pump_score >= 0.4 and (meets_price_threshold or volume_ratio > 2.0):
            pump_type = 'moderate'
            confidence = min(pump_score, 0.7)
        else:
            return None  # Not a valid pump
            
        # Calculate risk factors
        risk_factors = self.assess_pump_risks(price_metrics, volume_metrics, change_24h)
        
        return {
            'symbol': symbol,
            'pump_type': pump_type,
            'confidence': confidence,
            'pump_score': pump_score,
            'price_change': price_change_15m,
            'price_change_1h': price_change_1h,
            'volume_ratio': volume_ratio,
            'volume_trend': volume_metrics.get('volume_trend'),
            'risk_factors': risk_factors,
            'detected_at': datetime.utcnow().isoformat(),
            'criteria_met': {
                'price_threshold': meets_price_threshold,
                'volume_threshold': meets_volume_threshold,
                'reasonable_24h': reasonable_24h_change,
                'volume_trend_ok': volume_trend_positive
            }
        }
        
    def assess_pump_risks(self, price_metrics: Dict, volume_metrics: Dict, change_24h: float) -> List[str]:
        """Assess risk factors for the detected pump."""
        risks = []
        
        price_change_15m = price_metrics.get('price_change_15m', 0)
        price_change_1h = price_metrics.get('price_change_1h', 0)
        volume_ratio = volume_metrics.get('volume_ratio', 1.0)
        
        # Price-based risks
        if price_change_15m > 0.20:  # >20% in 15 minutes
            risks.append('Extreme price movement - high retracement risk')
            
        if price_change_1h > price_change_15m * 2:  # Accelerating too fast
            risks.append('Accelerating pump - may be unsustainable')
            
        if abs(change_24h) > 0.30:  # Already moved significantly in 24h
            risks.append('Already large 24h move - limited upside potential')
            
        # Volume-based risks
        if volume_ratio > 10:  # Extremely high volume
            risks.append('Extreme volume spike - may indicate whale manipulation')
            
        if volume_metrics.get('volume_trend') == 'decreasing':
            risks.append('Decreasing volume trend - momentum may be fading')
            
        # Time-based risks
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Low activity hours
            risks.append('Low activity hours - pump may lack follow-through')
            
        return risks
        
    def filter_recent_pumps(self, new_pumps: List[Dict]) -> List[Dict]:
        """Filter out pumps that were recently detected for the same symbol."""
        filtered_pumps = []
        current_time = datetime.utcnow()
        
        for pump in new_pumps:
            symbol = pump.get('symbol')
            
            # Check if we've detected a pump for this symbol recently (within 2 hours)
            recent_pump_exists = False
            for existing_pump in self.detected_pumps:
                if existing_pump.get('symbol') == symbol:
                    pump_time = datetime.fromisoformat(existing_pump.get('detected_at'))
                    time_diff = (current_time - pump_time).total_seconds() / 3600  # Hours
                    
                    if time_diff < 2:  # Within 2 hours
                        recent_pump_exists = True
                        break
                        
            if not recent_pump_exists:
                filtered_pumps.append(pump)
                
        return filtered_pumps
        
    def cleanup_old_pumps(self):
        """Remove pump records older than 24 hours."""
        current_time = datetime.utcnow()
        cutoff_time = current_time - timedelta(hours=24)
        
        self.detected_pumps = [
            pump for pump in self.detected_pumps
            if datetime.fromisoformat(pump.get('detected_at', current_time.isoformat())) > cutoff_time
        ]
        
    async def get_current_market_data(self) -> Dict:
        """Get current market data from real sources."""
        try:
            # Import data manager for real market data
            from data_sources.data_manager import DataManager
            
            data_manager = DataManager()
            market_data = await data_manager.get_market_data(config.SYMBOLS)
            
            if market_data:
                self.logger.info(f"Retrieved market data for {len(market_data)} symbols")
                return market_data
            else:
                self.logger.error("No market data available for pump scanning")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting market data for pump scan: {e}")
            return {}
        
    async def get_historical_data(self, symbol: str) -> Optional[Dict]:
        """Get historical price and volume data for symbol."""
        try:
            # Import data manager for real historical data
            from data_sources.data_manager import DataManager
            
            data_manager = DataManager()
            historical_data = await data_manager.get_historical_data(symbol, interval='5m', limit=48)
            
            if historical_data:
                # Extract prices and volumes
                prices = [float(candle['close']) for candle in historical_data]
                volumes = [float(candle['volume']) for candle in historical_data]
                
                return {
                    'prices': prices,
                    'volumes': volumes,
                    'symbol': symbol,
                    'timeframe': '5m',
                    'data_points': len(historical_data)
                }
            else:
                self.logger.warning(f"No historical data available for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return None
        
    def get_pump_statistics(self) -> Dict:
        """Get statistics about detected pumps."""
        if not self.detected_pumps:
            return {
                'total_pumps': 0,
                'avg_confidence': 0,
                'pump_types': {},
                'most_active_symbols': []
            }
            
        total_pumps = len(self.detected_pumps)
        avg_confidence = sum(p.get('confidence', 0) for p in self.detected_pumps) / total_pumps
        
        # Count pump types
        pump_types = {}
        for pump in self.detected_pumps:
            pump_type = pump.get('pump_type', 'unknown')
            pump_types[pump_type] = pump_types.get(pump_type, 0) + 1
            
        # Count symbols
        symbol_counts = {}
        for pump in self.detected_pumps:
            symbol = pump.get('symbol', 'unknown')
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
        most_active = sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'total_pumps': total_pumps,
            'avg_confidence': avg_confidence,
            'pump_types': pump_types,
            'most_active_symbols': most_active,
            'last_24h_pumps': len(self.detected_pumps)  # Since we clean old ones
        }
        
    def save_pump_history(self):
        """Save pump detection history to file."""
        try:
            history_file = f"{config.DATA_DIR}/pump_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.detected_pumps, f, indent=2)
            self.logger.info(f"Pump history saved to {history_file}")
        except Exception as e:
            self.logger.error(f"Failed to save pump history: {e}")
            
    def load_pump_history(self):
        """Load pump detection history from file."""
        try:
            history_file = f"{config.DATA_DIR}/pump_history.json"
            with open(history_file, 'r') as f:
                self.detected_pumps = json.load(f)
            self.logger.info(f"Loaded {len(self.detected_pumps)} pumps from history")
        except FileNotFoundError:
            self.detected_pumps = []
        except Exception as e:
            self.logger.error(f"Failed to load pump history: {e}")
            self.detected_pumps = [] 
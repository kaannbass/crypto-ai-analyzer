"""
Data manager for handling multiple crypto data sources with fallbacks.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import config
from data_sources.binance_api import get_binance_market_data

# Import CoinGecko with fallback
try:
    from data_sources.coingecko_api import get_coingecko_market_data
except ImportError:
    async def get_coingecko_market_data(symbols):
        return {}


class DataManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = 60  # Cache data for 60 seconds
        
        # Adjust CoinGecko cache duration based on Pro API availability
        coingecko_pro_enabled = getattr(config, 'COINGECKO_PRO_ENABLED', False)
        if coingecko_pro_enabled:
            self.coingecko_cache_duration = 1800  # 30 minutes for Pro API (more reliable)
            self.logger.info("🔑 CoinGecko Pro API detected - using shorter cache duration")
        else:
            self.coingecko_cache_duration = 3600  # 1 hour for free API (conserve calls)
            self.logger.info("🆓 Using CoinGecko Free API - using longer cache duration")
            
        self.preferred_source = 'binance'  # Primary data source
        
    async def get_market_data(self, symbols: List[str], force_refresh: bool = False) -> Dict:
        """Get market data with caching and multiple source fallback."""
        try:
            cache_key = f"market_data_{'-'.join(sorted(symbols))}"
            
            # Check cache first
            if not force_refresh and self._is_cache_valid(cache_key):
                self.logger.debug("Using cached market data")
                return self.cache[cache_key]['data']
                
            # Try to get data from sources
            market_data = await self._fetch_from_sources(symbols)
            
            if market_data:
                # Cache the data
                self.cache[cache_key] = {
                    'data': market_data,
                    'timestamp': datetime.utcnow(),
                    'symbols': symbols
                }
                
                # Save to file as backup
                await self._save_to_file(market_data)
                return market_data
            else:
                # If no fresh data, try fallback mechanisms
                self.logger.warning("🔄 No fresh data available, trying fallback mechanisms...")
                
                # Try extended cache (older cached data)
                fallback_data = await self._try_extended_cache(cache_key, symbols)
                if fallback_data:
                    return fallback_data
                
                # Try file backup
                fallback_data = await self._load_from_file()
                if fallback_data:
                    self.logger.info("📁 Using backup data from file")
                    return fallback_data
                
                # Last resort: try partial data with missing symbols filled with defaults
                fallback_data = await self._create_fallback_data(symbols)
                if fallback_data:
                    self.logger.warning("⚠️ Using fallback data with default values")
                    return fallback_data
                
                self.logger.error("🚫 All fallback mechanisms failed")
                return {}
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            # Try file backup on error
            return await self._load_from_file() or {}
            
    async def _fetch_from_sources(self, symbols: List[str]) -> Dict:
        """Fetch data from multiple sources with intelligent prioritization."""
        
        # Check if we have Pro CoinGecko access
        coingecko_pro_enabled = getattr(config, 'COINGECKO_PRO_ENABLED', False)
        
        # Strategy 1: Try Binance first (fastest and most comprehensive)
        try:
            self.logger.info("🔄 Trying Binance API...")
            market_data = await asyncio.wait_for(
                get_binance_market_data(symbols), 
                timeout=15.0
            )
            
            if market_data and self._validate_data(market_data, symbols):
                self.logger.info("✅ Successfully fetched data from Binance")
                return market_data
            else:
                self.logger.warning("❌ Invalid or empty data from Binance")
                
        except asyncio.TimeoutError:
            self.logger.warning("⏱️ Timeout fetching data from Binance")
        except Exception as e:
            self.logger.error(f"❌ Error fetching from Binance: {e}")
        
        # Strategy 2: Fallback to CoinGecko with smart caching
        try:
            coingecko_cache_key = f"coingecko_data_{'-'.join(sorted(symbols))}"
            
            # Check if CoinGecko cache is valid
            cache_valid_duration = self.coingecko_cache_duration
            if self._is_coingecko_cache_valid(coingecko_cache_key):
                cache_age = self._get_cache_age(coingecko_cache_key)
                self.logger.info(f"✅ Using CoinGecko cache (age: {cache_age/60:.1f} minutes)")
                return self.cache[coingecko_cache_key]['data']
            
            # Fetch fresh CoinGecko data
            api_type = "Pro" if coingecko_pro_enabled else "Free"
            self.logger.info(f"🔄 Fetching fresh data from CoinGecko {api_type} API")
            market_data = await asyncio.wait_for(
                get_coingecko_market_data(symbols), 
                timeout=12.0
            )
            
            if market_data and self._validate_data(market_data, symbols):
                # Cache CoinGecko data
                self.cache[coingecko_cache_key] = {
                    'data': market_data,
                    'timestamp': datetime.utcnow(),
                    'symbols': symbols
                }
                cache_duration_min = cache_valid_duration / 60
                self.logger.info(f"✅ Successfully fetched and cached CoinGecko data for {cache_duration_min:.0f} minutes")
                return market_data
            else:
                self.logger.warning("❌ Invalid or empty data from CoinGecko")
                
        except asyncio.TimeoutError:
            self.logger.warning("⏱️ Timeout fetching data from CoinGecko")
        except Exception as e:
            self.logger.error(f"❌ Error fetching from CoinGecko: {e}")
                
        self.logger.error("🚫 All data sources failed")
        return {}
        
    def _validate_data(self, data: Dict, expected_symbols: List[str]) -> bool:
        """Validate that the data contains required fields."""
        if not data:
            return False
            
        required_fields = ['price', 'volume', 'change_24h']
        
        for symbol in expected_symbols:
            if symbol not in data:
                self.logger.warning(f"Missing data for symbol: {symbol}")
                return False
                
            symbol_data = data[symbol]
            for field in required_fields:
                if field not in symbol_data:
                    self.logger.warning(f"Missing field {field} for {symbol}")
                    return False
                    
                if not isinstance(symbol_data[field], (int, float)):
                    self.logger.warning(f"Invalid data type for {field} in {symbol}")
                    return False
                    
        return True
        
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self.cache:
            return False
            
        cached_time = self.cache[cache_key]['timestamp']
        age = (datetime.utcnow() - cached_time).total_seconds()
        
        return age < self.cache_duration
    
    def _get_cache_age(self, cache_key: str) -> float:
        """Get the age of cached data in seconds."""
        if cache_key in self.cache:
            cached_time = self.cache[cache_key]['timestamp']
            return (datetime.utcnow() - cached_time).total_seconds()
        return float('inf')
    
    def _is_coingecko_cache_valid(self, cache_key: str) -> bool:
        """Check if CoinGecko cached data is still valid (1 hour limit)."""
        if cache_key not in self.cache:
            return False
            
        cached_time = self.cache[cache_key]['timestamp']
        age = (datetime.utcnow() - cached_time).total_seconds()
        
        # CoinGecko data is cached for 1 hour
        return age < self.coingecko_cache_duration
        
    async def _save_to_file(self, data: Dict):
        """Save market data to file as backup."""
        try:
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'data': data
            }
            
            with open(config.PRICES_FILE, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save market data backup: {e}")
            
    async def _load_from_file(self) -> Optional[Dict]:
        """Load market data from backup file."""
        try:
            with open(config.PRICES_FILE, 'r') as f:
                backup_data = json.load(f)
                
            # Check if backup is recent (more lenient now)
            timestamp = datetime.fromisoformat(backup_data['timestamp'])
            age = (datetime.utcnow() - timestamp).total_seconds()
            
            if age < 3600:  # 1 hour - recent data
                self.logger.info("📁 Using fresh backup market data from file")
                return backup_data['data']
            elif age < 7200:  # 2 hours - acceptable data
                self.logger.info(f"📁 Using backup market data from file (age: {age/3600:.1f} hours)")
                return backup_data['data']
            elif age < 86400:  # 24 hours - emergency fallback
                self.logger.warning(f"⚠️ Using old backup data from file (age: {age/3600:.1f} hours)")
                return backup_data['data']
            else:
                self.logger.warning(f"❌ Backup data is too old ({age/3600:.1f} hours)")
                return None
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Could not load backup data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error loading backup data: {e}")
            return None
            
    async def get_historical_data(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Get historical price data for technical analysis."""
        try:
            # Try Binance first for historical data
            from data_sources.binance_api import BinanceAPI
            
            async with BinanceAPI() as binance:
                klines = await binance.get_klines(symbol, interval, limit)
                
                if klines:
                    return klines
                    
            self.logger.error(f"Could not get historical data for {symbol} from any source")
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return []
            
    async def test_all_sources(self) -> Dict[str, bool]:
        """Test connectivity to all data sources."""
        results = {}
        
        try:
            from data_sources.binance_api import BinanceAPI
            async with BinanceAPI() as binance:
                results['binance'] = await binance.test_connection()
        except Exception:
            results['binance'] = False
            
        try:
            from data_sources.coingecko_api import CoinGeckoAPI
            async with CoinGeckoAPI() as coingecko:
                results['coingecko'] = await coingecko.test_connection()
        except Exception:
            results['coingecko'] = False
            
        return results
        
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.logger.info("Data cache cleared")
        
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        total_entries = len(self.cache)
        total_size = sum(len(str(entry)) for entry in self.cache.values())
        
        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'cache_duration_seconds': self.cache_duration
        } 

    async def _create_fallback_data(self, symbols: List[str]) -> Dict:
        """Create fallback data with reasonable default values when all sources fail."""
        try:
            self.logger.info("🔧 Creating fallback data with default values")
            
            # Try to get at least partial data from any available source
            partial_data = {}
            
            # Quick attempt at Binance without full retry logic
            try:
                from data_sources.binance_api import BinanceAPI
                async with BinanceAPI() as binance:
                    # Quick ping test
                    if await asyncio.wait_for(binance.test_connection(), timeout=5.0):
                        # Try to get at least ticker data for major symbols
                        major_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
                        for symbol in major_symbols:
                            if symbol in symbols:
                                try:
                                    ticker = await asyncio.wait_for(binance.get_ticker_24h(symbol), timeout=3.0)
                                    if ticker and 'lastPrice' in ticker:
                                        partial_data[symbol] = {
                                            'price': float(ticker['lastPrice']),
                                            'volume': float(ticker.get('volume', 0)),
                                            'volume_change_24h': 0.1,
                                            'high_24h': float(ticker.get('highPrice', 0)),
                                            'low_24h': float(ticker.get('lowPrice', 0)),
                                            'change_24h': float(ticker.get('priceChangePercent', 0)) / 100,
                                            'timestamp': datetime.utcnow().isoformat(),
                                            'source': 'binance_partial'
                                        }
                                except Exception:
                                    continue
            except Exception:
                pass
            
            # If we got some partial data, return it
            if partial_data:
                self.logger.info(f"✅ Retrieved partial data for {len(partial_data)} symbols")
                return partial_data
            
            # Last resort: create minimal data structure for critical functionality
            fallback_data = {}
            for symbol in symbols[:3]:  # Only create data for first 3 symbols to avoid overwhelming
                fallback_data[symbol] = {
                    'price': 0.0,
                    'volume': 0.0,
                    'volume_change_24h': 0.0,
                    'high_24h': 0.0,
                    'low_24h': 0.0,
                    'change_24h': 0.0,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'fallback'
                }
            
            return fallback_data
            
        except Exception as e:
            self.logger.error(f"Error creating fallback data: {e}")
            return {}
    
    async def _try_extended_cache(self, cache_key: str, symbols: List[str]) -> Optional[Dict]:
        """Try to use older cached data as fallback."""
        try:
            if cache_key in self.cache:
                cached_time = self.cache[cache_key]['timestamp']
                age = (datetime.utcnow() - cached_time).total_seconds()
                
                # Allow up to 4 hours old data in emergency
                if age < 14400:  # 4 hours
                    self.logger.info(f"📦 Using extended cache (age: {age/3600:.1f} hours)")
                    return self.cache[cache_key]['data']
            
            # Check CoinGecko extended cache
            coingecko_cache_key = f"coingecko_data_{'-'.join(sorted(symbols))}"
            if coingecko_cache_key in self.cache:
                cached_time = self.cache[coingecko_cache_key]['timestamp']
                age = (datetime.utcnow() - cached_time).total_seconds()
                
                # Allow up to 6 hours old CoinGecko data
                if age < 21600:  # 6 hours
                    self.logger.info(f"📦 Using extended CoinGecko cache (age: {age/3600:.1f} hours)")
                    return self.cache[coingecko_cache_key]['data']
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error trying extended cache: {e}")
            return None 
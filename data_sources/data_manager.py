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
        """Get market data from live sources ONLY - NO FALLBACK DATA EVER."""
        try:
            self.logger.info("🔄 Fetching LIVE data from multiple sources...")
            
            # Try CoinGecko Simple API first (working and reliable)
            self.logger.info("🔄 Trying CoinGecko Simple API...")
            try:
                from .coingecko_api import CoinGeckoAPI
                async with CoinGeckoAPI() as coingecko:
                    coingecko_data = await coingecko.get_market_data(symbols)
                    
                    if coingecko_data and len(coingecko_data) >= len(symbols) * 0.8:  # At least 80% success
                        self.logger.info(f"✅ CoinGecko Simple API success: {len(coingecko_data)}/{len(symbols)} symbols")
                        return coingecko_data
            except Exception as e:
                self.logger.warning(f"CoinGecko Simple API failed: {e}")
            
            # Try Binance if CoinGecko fails
            self.logger.info("🔄 Trying Binance API...")
            try:
                from .binance_api import BinanceAPI
                async with BinanceAPI() as binance:
                    binance_data = await binance.get_market_data(symbols)
                    
                    if binance_data and len(binance_data) >= len(symbols) * 0.8:  # At least 80% success
                        self.logger.info(f"✅ Binance API success: {len(binance_data)}/{len(symbols)} symbols")
                        return binance_data
            except Exception as e:
                self.logger.warning(f"Binance API failed: {e}")
            
            # Try alternative APIs (Bybit, KuCoin, etc.)
            self.logger.info("🔄 Trying Alternative APIs...")
            try:
                from .alternative_apis import AlternativeAPIs
                async with AlternativeAPIs() as alt_apis:
                    alt_data = await alt_apis.get_all_alternative_data(symbols)
                    
                    if alt_data and len(alt_data) >= len(symbols) * 0.5:  # At least 50% success
                        self.logger.info(f"✅ Alternative APIs success: {len(alt_data)}/{len(symbols)} symbols")
                        return alt_data
            except Exception as e:
                self.logger.warning(f"Alternative APIs failed: {e}")
            
            # If all sources fail completely, return empty dict (NO FALLBACK)
            self.logger.error("🚫 ALL LIVE DATA SOURCES FAILED - No data will be returned")
            self.logger.error("📍 System will wait for next cycle - no fake data generated")
            
            # Check if we have ANY cached data that's not too old (max 1 hour)
            cached_data = await self._get_cached_data(symbols, max_age=3600)  # 1 hour max
            if cached_data:
                self.logger.info(f"📦 Using recent cached data: {len(cached_data)} symbols")
                return cached_data
            
            return {}  # Return empty instead of any fake data
            
        except Exception as e:
            self.logger.error(f"Error in get_market_data: {e}")
            return {}  # Return empty instead of any fake data
            
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

    async def _get_cached_data(self, symbols: List[str], max_age: int) -> Optional[Dict]:
        """
        Attempt to retrieve cached data for a list of symbols.
        Returns the most recent valid data if available, otherwise None.
        """
        try:
            # Sort symbols for consistent cache key
            sorted_symbols = sorted(symbols)
            cache_key = f"market_data_{'-'.join(sorted_symbols)}"
            
            if cache_key in self.cache:
                cached_time = self.cache[cache_key]['timestamp']
                age = (datetime.utcnow() - cached_time).total_seconds()
                
                if age < max_age:
                    cached_data = self.cache[cache_key]['data']
                    # Verify cached data is not fallback/mock data
                    real_data_count = sum(1 for data in cached_data.values() 
                                        if data.get('source') not in ['fallback', 'mock', 'default'])
                    
                    if real_data_count > 0:
                        self.logger.info(f"📦 Using recent cached REAL data for {real_data_count}/{len(symbols)} symbols (age: {age/60:.1f} minutes)")
                        return cached_data
                    else:
                        self.logger.warning("⚠️ Cached data contains only fallback/mock data - rejecting")
                        return None
                else:
                    self.logger.warning(f"⚠️ Cached data for {len(symbols)} symbols is too old ({age/60:.1f} minutes)")
                    return None
            return None
        except Exception as e:
            self.logger.error(f"Error checking cached data: {e}")
            return None 
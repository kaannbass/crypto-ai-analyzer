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
        self.coingecko_cache_duration = 3600  # CoinGecko cache for 1 hour (3600 seconds)
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
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return await self._load_from_file() or {}
            
    async def _fetch_from_sources(self, symbols: List[str]) -> Dict:
        """Fetch data from multiple sources with hourly CoinGecko rate limiting."""
        
        # Try Binance first (primary source)
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
        
        # Fallback to CoinGecko with hourly cache
        try:
            coingecko_cache_key = f"coingecko_data_{'-'.join(sorted(symbols))}"
            
            # Check if CoinGecko cache is valid (1 hour)
            if self._is_coingecko_cache_valid(coingecko_cache_key):
                self.logger.info("✅ Using CoinGecko hourly cache")
                return self.cache[coingecko_cache_key]['data']
            
            # Fetch fresh CoinGecko data (once per hour)
            self.logger.info("🔄 Fetching fresh data from CoinGecko (hourly limit)")
            market_data = await asyncio.wait_for(
                get_coingecko_market_data(symbols), 
                timeout=10.0
            )
            
            if market_data and self._validate_data(market_data, symbols):
                # Cache CoinGecko data for 1 hour
                self.cache[coingecko_cache_key] = {
                    'data': market_data,
                    'timestamp': datetime.utcnow(),
                    'symbols': symbols
                }
                self.logger.info("✅ Successfully fetched and cached CoinGecko data for 1 hour")
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
                
            # Check if backup is recent (within 1 hour)
            timestamp = datetime.fromisoformat(backup_data['timestamp'])
            age = (datetime.utcnow() - timestamp).total_seconds()
            
            if age < 3600:  # 1 hour
                self.logger.info("Using backup market data from file")
                return backup_data['data']
            else:
                self.logger.warning("Backup data is too old")
                return None
                
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Could not load backup data: {e}")
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
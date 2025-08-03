"""
Binance API client for real-time cryptocurrency data.
Enhanced with SSL handling, retry logic, and rate limiting.
"""

import asyncio
import aiohttp
import json
import logging
import ssl
from datetime import datetime
from typing import Dict, List, Optional
import config


class BinanceAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = "https://api.binance.com/api/v3"
        self.backup_urls = [
            "https://api1.binance.com/api/v3",
            "https://api2.binance.com/api/v3",
            "https://api3.binance.com/api/v3"
        ]
        self.session = None
        self.current_url = self.base_url
        self.max_retries = 3
        self.request_delay = 0.1  # Rate limiting delay
        
    async def __aenter__(self):
        # Create SSL context that's more permissive
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connection timeout and retry settings
        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=10
        )
        
        # Connection pool settings
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,
            limit_per_host=5,
            enable_cleanup_closed=True,
            force_close=False  # Fixed: Cannot use keepalive_timeout with force_close=True
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'crypto-ai-analyzer/1.0',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            # Give time for connections to close properly
            await asyncio.sleep(0.1)

    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a request with retry logic and URL fallback."""
        urls_to_try = [self.current_url] + [url for url in self.backup_urls if url != self.current_url]
        
        for url_index, base_url in enumerate(urls_to_try):
            full_url = f"{base_url}{endpoint.replace(self.base_url, '')}"
            
            for attempt in range(self.max_retries):
                try:
                    # Rate limiting
                    await asyncio.sleep(self.request_delay)
                    
                    async with self.session.get(full_url, params=params or {}) as response:
                        if response.status == 200:
                            data = await response.json()
                            # If successful with backup URL, update current URL
                            if url_index > 0:
                                self.current_url = base_url
                                self.logger.info(f"Switched to backup Binance URL: {base_url}")
                            return data
                        elif response.status == 429:  # Rate limit
                            self.logger.warning(f"Rate limited by Binance (attempt {attempt + 1})")
                            await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                            continue
                        elif response.status >= 500:  # Server error
                            self.logger.warning(f"Binance server error {response.status} (attempt {attempt + 1})")
                            await asyncio.sleep(0.5 * (attempt + 1))
                            continue
                        else:
                            self.logger.error(f"Binance API error: {response.status}")
                            break
                            
                except asyncio.TimeoutError:
                    self.logger.warning(f"Timeout connecting to {base_url} (attempt {attempt + 1})")
                    await asyncio.sleep(1 * (attempt + 1))
                    
                except aiohttp.ClientConnectionError as e:
                    self.logger.warning(f"Connection error to {base_url} (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(1 * (attempt + 1))
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error with {base_url} (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(1 * (attempt + 1))
        
        # All URLs and retries failed
        self.logger.error("All Binance API endpoints failed")
        return {}

    async def get_ticker_24h(self, symbol: str = None) -> Dict:
        """Get 24hr ticker price change statistics."""
        try:
            endpoint = "/ticker/24hr"
            params = {}
            
            if symbol:
                params['symbol'] = symbol
                
            data = await self._make_request(endpoint, params)
            return data
                    
        except Exception as e:
            self.logger.error(f"Error fetching ticker data: {e}")
            return {}
            
    async def get_current_prices(self, symbols: List[str]) -> Dict:
        """Get current prices for multiple symbols."""
        try:
            endpoint = "/ticker/price"
            data = await self._make_request(endpoint)
            
            if data:
                # Filter for requested symbols
                price_data = {}
                for item in data:
                    symbol = item['symbol']
                    if symbol in symbols:
                        price_data[symbol] = float(item['price'])
                        
                return price_data
            
            return {}
                    
        except Exception as e:
            self.logger.error(f"Error fetching price data: {e}")
            return {}
            
    async def get_market_data(self, symbols: List[str]) -> Dict:
        """Get comprehensive market data for symbols."""
        try:
            # Get 24hr ticker data for all symbols
            ticker_data = await self.get_ticker_24h()
            
            if not isinstance(ticker_data, list):
                self.logger.warning("Invalid ticker data format received")
                return {}
                
            market_data = {}
            
            for ticker in ticker_data:
                try:
                    symbol = ticker['symbol']
                    
                    if symbol in symbols:
                        # Add volume change calculation
                        volume_24h = float(ticker['volume'])
                        quote_volume_24h = float(ticker['quoteVolume'])
                        
                        # Estimate volume change (simplified calculation)
                        # In a real implementation, you'd compare with previous period
                        volume_change_24h = 0.1  # Default 10% change estimate
                        
                        market_data[symbol] = {
                            'price': float(ticker['lastPrice']),
                            'volume': volume_24h,
                            'volume_change_24h': volume_change_24h,
                            'high_24h': float(ticker['highPrice']),
                            'low_24h': float(ticker['lowPrice']),
                            'change_24h': float(ticker['priceChangePercent']) / 100,  # Convert to decimal
                            'quote_volume': quote_volume_24h,
                            'bid_price': float(ticker['bidPrice']),
                            'ask_price': float(ticker['askPrice']),
                            'open_price': float(ticker['openPrice']),
                            'close_price': float(ticker['lastPrice']),
                            'count': int(ticker['count']),  # Number of trades
                            'timestamp': datetime.utcnow().isoformat(),
                            'source': 'binance'
                        }
                except (KeyError, ValueError) as e:
                    self.logger.warning(f"Error parsing ticker data for {ticker.get('symbol', 'unknown')}: {e}")
                    continue
                    
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error fetching market data: {e}")
            return {}
            
    async def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Get kline/candlestick data."""
        try:
            endpoint = "/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            data = await self._make_request(endpoint, params)
            
            if data and isinstance(data, list):
                klines = []
                for kline in data:
                    try:
                        klines.append({
                            'open_time': int(kline[0]),
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5]),
                            'close_time': int(kline[6]),
                            'quote_volume': float(kline[7]),
                            'trades_count': int(kline[8]),
                            'buy_base_volume': float(kline[9]),
                            'buy_quote_volume': float(kline[10])
                        })
                    except (IndexError, ValueError) as e:
                        self.logger.warning(f"Error parsing kline data: {e}")
                        continue
                        
                return klines
            
            return []
                    
        except Exception as e:
            self.logger.error(f"Error fetching klines: {e}")
            return []
            
    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict:
        """Get order book depth."""
        try:
            endpoint = "/depth"
            params = {
                'symbol': symbol,
                'limit': limit
            }
            
            data = await self._make_request(endpoint, params)
            
            if data and 'bids' in data and 'asks' in data:
                return {
                    'symbol': symbol,
                    'bids': [[float(bid[0]), float(bid[1])] for bid in data['bids']],
                    'asks': [[float(ask[0]), float(ask[1])] for ask in data['asks']],
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return {}
                    
        except Exception as e:
            self.logger.error(f"Error fetching order book: {e}")
            return {}
            
    async def test_connection(self) -> bool:
        """Test connection to Binance API."""
        try:
            endpoint = "/ping"
            data = await self._make_request(endpoint)
            success = bool(data)  # Ping returns empty dict if successful
            
            if success:
                self.logger.info(f"Binance API connection successful via {self.current_url}")
            else:
                self.logger.warning("Binance API connection failed")
                
            return success
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    async def get_exchange_info(self) -> Dict:
        """Get exchange information including trading rules and symbol information."""
        try:
            endpoint = "/exchangeInfo"
            data = await self._make_request(endpoint)
            return data or {}
        except Exception as e:
            self.logger.error(f"Error fetching exchange info: {e}")
            return {}

    async def get_server_time(self) -> Dict:
        """Get server time."""
        try:
            endpoint = "/time"
            data = await self._make_request(endpoint)
            return data or {}
        except Exception as e:
            self.logger.error(f"Error fetching server time: {e}")
            return {}


# Convenience function for getting market data
async def get_binance_market_data(symbols: List[str]) -> Dict:
    """Get market data from Binance API."""
    try:
        async with BinanceAPI() as binance:
            # Test connection first
            if await binance.test_connection():
                return await binance.get_market_data(symbols)
            else:
                logging.error("Binance connection test failed")
                return {}
    except Exception as e:
        logging.error(f"Failed to get Binance market data: {e}")
        return {}

# Convenience function for testing API
async def test_binance_connection() -> bool:
    """Test Binance API connection."""
    try:
        async with BinanceAPI() as binance:
            return await binance.test_connection()
    except Exception as e:
        logging.error(f"Binance connection test failed: {e}")
        return False 
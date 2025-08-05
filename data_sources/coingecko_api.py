"""
CoinGecko API client for cryptocurrency data (free tier available).
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import config


class CoinGeckoAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Check if Pro API is available
        self.api_key = getattr(config, 'COINGECKO_API_KEY', '')
        self.pro_enabled = getattr(config, 'COINGECKO_PRO_ENABLED', False)
        
        if self.pro_enabled:
            self.base_url = "https://pro-api.coingecko.com/api/v3"
            self.logger.info("🔑 Using CoinGecko Pro API with authentication")
        else:
        self.base_url = "https://api.coingecko.com/api/v3"
            self.logger.info("🆓 Using CoinGecko Free API (limited)")
            
        self.session = None
        
        # Symbol mapping from Binance format to CoinGecko IDs - Updated for production
        self.symbol_mapping = {
            'BTCUSDT': 'bitcoin',
            'ETHUSDT': 'ethereum', 
            'BNBUSDT': 'binancecoin',
            'ADAUSDT': 'cardano',
            'PEPEUSDT': 'pepe',  # Fixed: pepecoin -> pepe
            'SOLUSDT': 'solana',
            'XRPUSDT': 'ripple',
            'DOGEUSDT': 'dogecoin',
            'TRXUSDT': 'tron',
            'LINKUSDT': 'chainlink',
            'XLMUSDT': 'stellar',
            'XMRUSDT': 'monero',
            'ZECUSDT': 'zcash',
        }
        
    async def __aenter__(self):
        # Add timeout and headers for better API handling
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        headers = {
            'User-Agent': 'crypto-ai-analyzer/1.0',
            'Accept': 'application/json'
        }
        
        # Add API key for Pro API
        if self.pro_enabled and self.api_key:
            headers['x-cg-pro-api-key'] = self.api_key
            self.logger.debug("🔐 Added Pro API authentication header")
            
        self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.1)  # Small delay for cleanup
            
    async def get_current_prices(self, symbols: List[str]) -> Dict:
        """Get current prices for symbols."""
        try:
            # Convert symbols to CoinGecko IDs
            coin_ids = []
            for symbol in symbols:
                if symbol in self.symbol_mapping:
                    coin_ids.append(self.symbol_mapping[symbol])
                    
            if not coin_ids:
                return {}
                
            endpoint = f"{self.base_url}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }
            
            # Enhanced retry logic for rate limiting with exponential backoff
            # Pro API has better rate limits (30/min vs ~10-50/min for free)
            max_attempts = 4 if self.pro_enabled else 3
            base_delay = 1 if self.pro_enabled else 2  # Shorter delays for Pro API
            
            for attempt in range(max_attempts):
                try:
                    self.logger.debug(f"CoinGecko request attempt {attempt + 1}/{max_attempts}")
                    
                    async with self.session.get(endpoint, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Convert back to our symbol format
                            price_data = {}
                            reverse_mapping = {v: k for k, v in self.symbol_mapping.items()}
                            
                            for coin_id, coin_data in data.items():
                                if coin_id in reverse_mapping:
                                    symbol = reverse_mapping[coin_id]
                                    price_data[symbol] = {
                                        'price': coin_data.get('usd', 0),
                                        'change_24h': coin_data.get('usd_24h_change', 0) / 100 if coin_data.get('usd_24h_change') else 0,
                                        'volume_24h': coin_data.get('usd_24h_vol', 0),
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'source': 'coingecko_pro' if self.pro_enabled else 'coingecko'
                                    }
                                    
                            self.logger.info(f"✅ CoinGecko: Successfully fetched {len(price_data)} prices")
                            return price_data
                            
                        elif response.status == 429:  # Rate limited
                            # Different backoff strategies for Pro vs Free
                            if self.pro_enabled:
                                # Pro API: shorter delays since limits are higher
                                delay = base_delay * (1.5 ** attempt)
                            else:
                                # Free API: longer delays
                                delay = base_delay * (2 ** attempt) + (attempt * 0.5)
                                
                            self.logger.warning(f"CoinGecko rate limited (attempt {attempt + 1}/{max_attempts}). Waiting {delay:.1f}s")
                            
                            if attempt < max_attempts - 1:  # Don't wait on last attempt
                                await asyncio.sleep(delay)
                                continue
                        elif response.status == 401:
                            self.logger.error(f"CoinGecko API authentication failed (401) - check API key")
                            return {}
                        elif response.status == 404:
                            self.logger.error(f"CoinGecko API endpoint not found (404)")
                            return {}
                        elif response.status >= 500:
                            self.logger.warning(f"CoinGecko server error {response.status} (attempt {attempt + 1})")
                            if attempt < max_attempts - 1:
                                await asyncio.sleep(base_delay * (attempt + 1))
                                continue
                        else:
                            error_text = await response.text()
                            self.logger.error(f"CoinGecko API error: {response.status} - {error_text}")
                            return {}
                            
                except asyncio.TimeoutError:
                    self.logger.warning(f"CoinGecko timeout (attempt {attempt + 1})")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(base_delay)
                        continue
                except Exception as e:
                    self.logger.error(f"CoinGecko request error (attempt {attempt + 1}): {type(e).__name__}: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(base_delay)
                        continue
                    
            self.logger.error("CoinGecko: All attempts failed")
            return {}  # All attempts failed
                    
        except Exception as e:
            self.logger.error(f"Error fetching CoinGecko prices: {e}")
            return {}
            
    async def get_market_data(self, symbols: List[str]) -> Dict:
        """Get comprehensive market data."""
        try:
            # Convert symbols to CoinGecko IDs
            coin_ids = []
            for symbol in symbols:
                if symbol in self.symbol_mapping:
                    coin_ids.append(self.symbol_mapping[symbol])
                    
            if not coin_ids:
                return {}
                
            endpoint = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': ','.join(coin_ids),
                'order': 'market_cap_desc',
                'per_page': len(coin_ids),
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            # Enhanced retry logic for rate limiting
            # Pro API has better rate limits
            max_attempts = 3 if self.pro_enabled else 2
            base_delay = 2 if self.pro_enabled else 3
            
            for attempt in range(max_attempts):
                try:
                    self.logger.debug(f"CoinGecko market data attempt {attempt + 1}/{max_attempts}")
            
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    market_data = {}
                    reverse_mapping = {v: k for k, v in self.symbol_mapping.items()}
                    
                    for coin in data:
                        coin_id = coin['id']
                        if coin_id in reverse_mapping:
                            symbol = reverse_mapping[coin_id]
                            
                            market_data[symbol] = {
                                'price': coin.get('current_price', 0),
                                'volume': coin.get('total_volume', 0),
                                'high_24h': coin.get('high_24h', 0),
                                'low_24h': coin.get('low_24h', 0),
                                'change_24h': coin.get('price_change_percentage_24h', 0) / 100 if coin.get('price_change_percentage_24h') else 0,
                                'market_cap': coin.get('market_cap', 0),
                                'market_cap_rank': coin.get('market_cap_rank', 0),
                                'circulating_supply': coin.get('circulating_supply', 0),
                                'total_supply': coin.get('total_supply', 0),
                                'timestamp': datetime.utcnow().isoformat(),
                                        'source': 'coingecko_pro' if self.pro_enabled else 'coingecko'
                            }
                            
                            self.logger.info(f"✅ CoinGecko: Successfully fetched market data for {len(market_data)} symbols")
                            return market_data
                            
                        elif response.status == 429:  # Rate limited
                            delay = base_delay * (1.5 ** attempt) if self.pro_enabled else base_delay * (2 ** attempt)
                            self.logger.warning(f"CoinGecko market data rate limited (attempt {attempt + 1}/{max_attempts}). Waiting {delay}s")
                            
                            if attempt < max_attempts - 1:
                                await asyncio.sleep(delay)
                                continue
                        elif response.status == 401:
                            self.logger.error(f"CoinGecko API authentication failed (401) - check API key")
                            return {}
                else:
                            error_text = await response.text()
                            self.logger.error(f"CoinGecko market data API error: {response.status} - {error_text}")
                            return {}
                            
                except asyncio.TimeoutError:
                    self.logger.warning(f"CoinGecko market data timeout (attempt {attempt + 1})")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(base_delay)
                        continue
                except Exception as e:
                    self.logger.error(f"CoinGecko market data error (attempt {attempt + 1}): {type(e).__name__}: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(base_delay)
                        continue
                        
            self.logger.error("CoinGecko market data: All attempts failed")
                    return {}
                    
        except Exception as e:
            self.logger.error(f"Error fetching CoinGecko market data: {e}")
            return {}
            
    async def get_trending_coins(self) -> List[Dict]:
        """Get trending coins."""
        try:
            endpoint = f"{self.base_url}/search/trending"
            
            async with self.session.get(endpoint) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('coins', [])
                else:
                    self.logger.error(f"CoinGecko API error: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error fetching trending coins: {e}")
            return []
            
    async def test_connection(self) -> bool:
        """Test connection to CoinGecko API."""
        try:
            endpoint = f"{self.base_url}/ping"
            
            async with self.session.get(endpoint) as response:
                return response.status == 200
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


# Convenience function for getting market data
async def get_coingecko_market_data(symbols: List[str]) -> Dict:
    """Get market data from CoinGecko API."""
    try:
        async with CoinGeckoAPI() as coingecko:
            return await coingecko.get_market_data(symbols)
    except Exception as e:
        logging.error(f"Failed to get CoinGecko market data: {e}")
        return {} 
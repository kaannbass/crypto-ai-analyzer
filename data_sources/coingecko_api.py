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
        self.base_url = "https://api.coingecko.com/api/v3"
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
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
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
                                'source': 'coingecko'
                            }
                            
                    return price_data
                else:
                    self.logger.error(f"CoinGecko API error: {response.status}")
                    return {}
                    
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
                                'source': 'coingecko'
                            }
                            
                    return market_data
                else:
                    self.logger.error(f"CoinGecko API error: {response.status}")
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
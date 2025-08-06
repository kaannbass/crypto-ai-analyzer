"""
Alternative crypto data sources that are accessible from Turkey.
Includes CoinCap, Kraken, KuCoin, and other APIs.
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from datetime import datetime
import json

class AlternativeAPIs:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = None
        
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': 'crypto-analyzer/1.0'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_coincap_data(self, symbols: List[str]) -> Dict:
        """Get data from CoinCap API (free, no API key needed)."""
        try:
            self.logger.info("🔄 Trying CoinCap API...")
            
            # CoinCap uses different symbol format
            coincap_symbols = {
                'BTCUSDT': 'bitcoin',
                'ETHUSDT': 'ethereum', 
                'BNBUSDT': 'binance-coin',
                'ADAUSDT': 'cardano',
                'SOLUSDT': 'solana',
                'PEPEUSDT': 'pepe',
                'XRPUSDT': 'xrp',
                'DOGEUSDT': 'dogecoin',
                'TRXUSDT': 'tron',
                'LINKUSDT': 'chainlink',
                'XLMUSDT': 'stellar',
                'XMRUSDT': 'monero',
                'ZECUSDT': 'zcash'
            }
            
            result = {}
            
            # Get top assets
            async with self.session.get('https://api.coincap.io/v2/assets?limit=50') as response:
                if response.status == 200:
                    data = await response.json()
                    assets = data.get('data', [])
                    
                    for symbol in symbols:
                        if symbol in coincap_symbols:
                            coincap_id = coincap_symbols[symbol]
                            
                            # Find asset in response
                            for asset in assets:
                                if asset.get('id') == coincap_id:
                                    price = float(asset.get('priceUsd', 0))
                                    change_24h = float(asset.get('changePercent24Hr', 0)) / 100
                                    volume = float(asset.get('volumeUsd24Hr', 0))
                                    
                                    result[symbol] = {
                                        'price': price,
                                        'change_24h': change_24h,
                                        'volume': volume,
                                        'volume_change_24h': 0.1,  # Not available
                                        'high_24h': price * 1.05,
                                        'low_24h': price * 0.95,
                                        'timestamp': datetime.utcnow().isoformat(),
                                        'source': 'coincap'
                                    }
                                    break
                    
                    self.logger.info(f"✅ CoinCap API: {len(result)} symbols retrieved")
                    return result
                else:
                    self.logger.error(f"CoinCap API error: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"CoinCap API failed: {e}")
            
        return {}

    async def get_kraken_data(self, symbols: List[str]) -> Dict:
        """Get data from Kraken API (free, reliable)."""
        try:
            self.logger.info("🔄 Trying Kraken API...")
            
            # Kraken symbol mapping
            kraken_symbols = {
                'BTCUSDT': 'XXBTZUSD',
                'ETHUSDT': 'XETHZUSD',
                'ADAUSDT': 'ADAUSD',
                'SOLUSDT': 'SOLUSD',
                'XRPUSDT': 'XXRPZUSD',
                'DOGEUSDT': 'XDGZUSD',
                'LINKUSDT': 'LINKUSD'
            }
            
            result = {}
            kraken_pairs = []
            
            for symbol in symbols:
                if symbol in kraken_symbols:
                    kraken_pairs.append(kraken_symbols[symbol])
            
            if kraken_pairs:
                pairs_str = ','.join(kraken_pairs)
                url = f'https://api.kraken.com/0/public/Ticker?pair={pairs_str}'
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('error') == []:
                            ticker_data = data.get('result', {})
                            
                            for symbol in symbols:
                                if symbol in kraken_symbols:
                                    kraken_pair = kraken_symbols[symbol]
                                    
                                    # Find matching pair in response
                                    for pair_key, pair_data in ticker_data.items():
                                        if kraken_pair in pair_key or pair_key in kraken_pair:
                                            price = float(pair_data.get('c', [0])[0])  # Last trade price
                                            high = float(pair_data.get('h', [0])[0])   # High 24h
                                            low = float(pair_data.get('l', [0])[0])    # Low 24h
                                            volume = float(pair_data.get('v', [0])[0]) # Volume 24h
                                            
                                            if price > 0:
                                                change_24h = ((price - low) / low) if low > 0 else 0
                                                
                                                result[symbol] = {
                                                    'price': price,
                                                    'change_24h': change_24h,
                                                    'volume': volume,
                                                    'volume_change_24h': 0.1,
                                                    'high_24h': high,
                                                    'low_24h': low,
                                                    'timestamp': datetime.utcnow().isoformat(),
                                                    'source': 'kraken'
                                                }
                                            break
                            
                            self.logger.info(f"✅ Kraken API: {len(result)} symbols retrieved")
                            return result
                        else:
                            self.logger.error(f"Kraken API error: {data.get('error')}")
                    else:
                        self.logger.error(f"Kraken API HTTP error: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Kraken API failed: {e}")
            
        return {}

    async def get_kucoin_data(self, symbols: List[str]) -> Dict:
        """Get data from KuCoin API (free, good coverage)."""
        try:
            self.logger.info("🔄 Trying KuCoin API...")
            
            # KuCoin uses standard symbols
            result = {}
            
            # Get all tickers
            async with self.session.get('https://api.kucoin.com/api/v1/market/allTickers') as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('code') == '200000':
                        tickers = data.get('data', {}).get('ticker', [])
                        
                        for symbol in symbols:
                            # KuCoin uses BTC-USDT format
                            kucoin_symbol = symbol.replace('USDT', '-USDT')
                            
                            for ticker in tickers:
                                if ticker.get('symbol') == kucoin_symbol:
                                    price = float(ticker.get('last', 0))
                                    change_24h = float(ticker.get('changeRate', 0))
                                    volume = float(ticker.get('volValue', 0))  # Volume in USDT
                                    high = float(ticker.get('high', 0))
                                    low = float(ticker.get('low', 0))
                                    
                                    if price > 0:
                                        result[symbol] = {
                                            'price': price,
                                            'change_24h': change_24h,
                                            'volume': volume,
                                            'volume_change_24h': 0.1,
                                            'high_24h': high,
                                            'low_24h': low,
                                            'timestamp': datetime.utcnow().isoformat(),
                                            'source': 'kucoin'
                                        }
                                    break
                        
                        self.logger.info(f"✅ KuCoin API: {len(result)} symbols retrieved")
                        return result
                    else:
                        self.logger.error(f"KuCoin API error: {data.get('msg')}")
                else:
                    self.logger.error(f"KuCoin API HTTP error: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"KuCoin API failed: {e}")
            
        return {}

    async def get_bybit_data(self, symbols: List[str]) -> Dict:
        """Get data from Bybit API (free, reliable)."""
        try:
            self.logger.info("🔄 Trying Bybit API...")
            
            result = {}
            
            # Get tickers for spot trading
            async with self.session.get('https://api.bybit.com/v5/market/tickers?category=spot') as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('retCode') == 0:
                        tickers = data.get('result', {}).get('list', [])
                        
                        for symbol in symbols:
                            for ticker in tickers:
                                if ticker.get('symbol') == symbol:
                                    price = float(ticker.get('lastPrice', 0))
                                    change_24h = float(ticker.get('price24hPcnt', 0))
                                    volume = float(ticker.get('volume24h', 0))
                                    high = float(ticker.get('highPrice24h', 0))
                                    low = float(ticker.get('lowPrice24h', 0))
                                    
                                    if price > 0:
                                        result[symbol] = {
                                            'price': price,
                                            'change_24h': change_24h,
                                            'volume': volume,
                                            'volume_change_24h': 0.1,
                                            'high_24h': high,
                                            'low_24h': low,
                                            'timestamp': datetime.utcnow().isoformat(),
                                            'source': 'bybit'
                                        }
                                    break
                        
                        self.logger.info(f"✅ Bybit API: {len(result)} symbols retrieved")
                        return result
                    else:
                        self.logger.error(f"Bybit API error: {data.get('retMsg')}")
                else:
                    self.logger.error(f"Bybit API HTTP error: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Bybit API failed: {e}")
            
        return {}

    async def get_all_alternative_data(self, symbols: List[str]) -> Dict:
        """Try all alternative APIs and return the best available data."""
        try:
            self.logger.info("🔄 Trying all alternative APIs...")
            
            # Try APIs in parallel for speed
            tasks = [
                self.get_coincap_data(symbols),
                self.get_kraken_data(symbols),
                self.get_kucoin_data(symbols),
                self.get_bybit_data(symbols)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results, preferring more complete datasets
            combined_result = {}
            source_priority = ['bybit', 'kucoin', 'kraken', 'coincap']  # Preferred order
            
            # First pass: collect all data
            all_data = {}
            for result in results:
                if isinstance(result, dict) and result:
                    for symbol, data in result.items():
                        if symbol not in all_data:
                            all_data[symbol] = []
                        all_data[symbol].append(data)
            
            # Second pass: select best source for each symbol
            for symbol in symbols:
                if symbol in all_data:
                    # Prefer by source priority
                    best_data = None
                    for priority_source in source_priority:
                        for data in all_data[symbol]:
                            if data.get('source') == priority_source:
                                best_data = data
                                break
                        if best_data:
                            break
                    
                    # If no priority source, take the first available
                    if not best_data and all_data[symbol]:
                        best_data = all_data[symbol][0]
                    
                    if best_data:
                        combined_result[symbol] = best_data
            
            if combined_result:
                sources_used = list(set(data.get('source') for data in combined_result.values()))
                self.logger.info(f"✅ Alternative APIs: {len(combined_result)} symbols from {sources_used}")
                return combined_result
            else:
                self.logger.error("❌ All alternative APIs failed")
                return {}
                
        except Exception as e:
            self.logger.error(f"Alternative APIs error: {e}")
            return {} 
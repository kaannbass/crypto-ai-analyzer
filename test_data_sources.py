#!/usr/bin/env python3
"""
Enhanced data source testing with comprehensive diagnostics.
"""

import asyncio
import logging
import sys
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_binance_connection():
    """Comprehensive Binance API testing."""
    logger.info("=" * 60)
    logger.info("🔍 BINANCE API COMPREHENSIVE TEST")
    logger.info("=" * 60)
    
    try:
        from data_sources.binance_api import BinanceAPI, test_binance_connection
        
        # Test 1: Basic connection test
        logger.info("Test 1: Basic connection test...")
        start_time = time.time()
        connection_ok = await test_binance_connection()
        elapsed = time.time() - start_time
        
        if connection_ok:
            logger.info(f"✅ Basic connection test PASSED ({elapsed:.2f}s)")
        else:
            logger.error(f"❌ Basic connection test FAILED ({elapsed:.2f}s)")
        
        # Test 2: Detailed API tests
        logger.info("\nTest 2: Detailed API tests...")
        async with BinanceAPI() as binance:
            # Test ping
            logger.info("  - Testing ping endpoint...")
            ping_result = await binance.test_connection()
            logger.info(f"    Ping result: {'✅ SUCCESS' if ping_result else '❌ FAILED'}")
            
            # Test server time
            logger.info("  - Testing server time endpoint...")
            time_data = await binance.get_server_time()
            if time_data and 'serverTime' in time_data:
                server_time = datetime.fromtimestamp(time_data['serverTime'] / 1000)
                logger.info(f"    ✅ Server time: {server_time}")
            else:
                logger.error(f"    ❌ Server time failed: {time_data}")
            
            # Test exchange info
            logger.info("  - Testing exchange info endpoint...")
            exchange_info = await binance.get_exchange_info()
            if exchange_info and 'symbols' in exchange_info:
                symbol_count = len(exchange_info['symbols'])
                logger.info(f"    ✅ Exchange info: {symbol_count} symbols available")
            else:
                logger.error(f"    ❌ Exchange info failed")
    
            # Test market data for key symbols
            logger.info("  - Testing market data for key symbols...")
            test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            market_data = await binance.get_market_data(test_symbols)
    
    if market_data:
                logger.info(f"    ✅ Market data: Retrieved data for {len(market_data)} symbols")
                for symbol, data in market_data.items():
                    price = data.get('price', 0)
                    logger.info(f"      {symbol}: ${price:,.2f}")
            else:
                logger.error(f"    ❌ Market data failed")
        
        return connection_ok
        
    except Exception as e:
        logger.error(f"❌ Binance test failed with exception: {type(e).__name__}: {e}")
        return False

async def test_coingecko_connection():
    """Comprehensive CoinGecko API testing."""
    logger.info("=" * 60)
    logger.info("🔍 COINGECKO API COMPREHENSIVE TEST")
    logger.info("=" * 60)
    
    try:
        from data_sources.coingecko_api import CoinGeckoAPI
        
        async with CoinGeckoAPI() as coingecko:
            # Test 1: Basic connection test
            logger.info("Test 1: Basic connection test...")
            start_time = time.time()
            connection_ok = await coingecko.test_connection()
            elapsed = time.time() - start_time
            
            if connection_ok:
                logger.info(f"✅ Basic connection test PASSED ({elapsed:.2f}s)")
            else:
                logger.error(f"❌ Basic connection test FAILED ({elapsed:.2f}s)")
            
            # Test 2: Price data test
            logger.info("\nTest 2: Price data test...")
            test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            price_data = await coingecko.get_current_prices(test_symbols)
            
            if price_data:
                logger.info(f"✅ Price data: Retrieved data for {len(price_data)} symbols")
                for symbol, data in price_data.items():
            price = data.get('price', 0)
                    change = data.get('change_24h', 0)
                    logger.info(f"    {symbol}: ${price:,.2f} ({change:+.2%})")
            else:
                logger.error("❌ Price data failed")
            
            # Test 3: Market data test
            logger.info("\nTest 3: Market data test...")
            market_data = await coingecko.get_market_data(test_symbols)
            
            if market_data:
                logger.info(f"✅ Market data: Retrieved data for {len(market_data)} symbols")
            else:
                logger.error("❌ Market data failed")
            
            # Test 4: Trending coins test
            logger.info("\nTest 4: Trending coins test...")
            trending = await coingecko.get_trending_coins()
            
            if trending:
                logger.info(f"✅ Trending coins: Retrieved {len(trending)} trending coins")
            else:
                logger.warning("⚠️ Trending coins failed (might be rate limited)")
        
        return connection_ok
        
    except Exception as e:
        logger.error(f"❌ CoinGecko test failed with exception: {type(e).__name__}: {e}")
        return False

async def test_data_manager():
    """Test the data manager with fallback mechanisms."""
    logger.info("=" * 60)
    logger.info("🔍 DATA MANAGER COMPREHENSIVE TEST")
    logger.info("=" * 60)
    
    try:
        from data_sources.data_manager import DataManager
        import config
        
        data_manager = DataManager()
                  
        # Test 1: Get market data with force refresh
        logger.info("Test 1: Get market data with force refresh...")
        start_time = time.time()
        market_data = await data_manager.get_market_data(config.SYMBOLS, force_refresh=True)
        elapsed = time.time() - start_time
        
        if market_data:
            logger.info(f"✅ Market data retrieved ({elapsed:.2f}s)")
            logger.info(f"    Symbols: {len(market_data)}/{len(config.SYMBOLS)}")
            
            # Check data sources
            sources = {}
            for symbol, data in market_data.items():
                source = data.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            logger.info("    Data sources breakdown:")
            for source, count in sources.items():
                logger.info(f"      {source}: {count} symbols")
        else:
            logger.error(f"❌ Market data failed ({elapsed:.2f}s)")
        
        # Test 2: Test individual source connectivity
        logger.info("\nTest 2: Test individual source connectivity...")
        source_results = await data_manager.test_all_sources()
        
        for source, result in source_results.items():
            status = "✅ ONLINE" if result else "❌ OFFLINE"
            logger.info(f"    {source}: {status}")
        
        # Test 3: Cache statistics
        logger.info("\nTest 3: Cache statistics...")
    cache_stats = data_manager.get_cache_stats()
        logger.info(f"    Cache entries: {cache_stats['total_entries']}")
        logger.info(f"    Cache size: {cache_stats['total_size_bytes']} bytes")
        logger.info(f"    Cache duration: {cache_stats['cache_duration_seconds']}s")
    
        return bool(market_data)
        
    except Exception as e:
        logger.error(f"❌ Data manager test failed: {type(e).__name__}: {e}")
        return False

async def run_network_diagnostics():
    """Run network diagnostics."""
    logger.info("=" * 60)
    logger.info("🔍 NETWORK DIAGNOSTICS")
    logger.info("=" * 60)
    
    import aiohttp
    import ssl
    
    # Test basic HTTP connectivity
    test_urls = [
        "https://api.binance.com/api/v3/ping",
        "https://api.coingecko.com/api/v3/ping",
        "https://httpbin.org/get"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in test_urls:
            try:
                start_time = time.time()
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    elapsed = time.time() - start_time
                    status = "✅ SUCCESS" if response.status == 200 else f"❌ HTTP {response.status}"
                    logger.info(f"    {url}: {status} ({elapsed:.2f}s)")
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"    {url}: ❌ FAILED - {type(e).__name__}: {e} ({elapsed:.2f}s)")

async def main():
    """Run comprehensive data source diagnostics."""
    logger.info("🚀 Starting comprehensive data source diagnostics...")
    logger.info(f"📅 Test started at: {datetime.now()}")
    
    # Run network diagnostics first
    await run_network_diagnostics()
    
    # Test individual APIs
    binance_ok = await test_binance_connection()
    coingecko_ok = await test_coingecko_connection()
    
    # Test data manager
    data_manager_ok = await test_data_manager()
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 DIAGNOSTIC SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Binance API: {'✅ WORKING' if binance_ok else '❌ FAILING'}")
    logger.info(f"CoinGecko API: {'✅ WORKING' if coingecko_ok else '❌ FAILING'}")
    logger.info(f"Data Manager: {'✅ WORKING' if data_manager_ok else '❌ FAILING'}")
    
    if binance_ok or coingecko_ok:
        logger.info("🎉 At least one data source is working!")
    else:
        logger.error("💥 All data sources are failing!")

    return binance_ok or coingecko_ok

if __name__ == "__main__":
    asyncio.run(main()) 
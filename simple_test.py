#!/usr/bin/env python3
"""
Basit test scripti - macOS uyumluluğu için.
"""

import asyncio
import sys
import os
from datetime import datetime

def test_basic_imports():
    """Temel importları test et."""
    print("🔍 Testing basic imports...")
    
    try:
        import config
        print("✅ Config import: OK")
        
        # Check CoinGecko API key
        api_key = getattr(config, 'COINGECKO_API_KEY', '')
        if api_key:
            print(f"✅ CoinGecko API key: Configured ({len(api_key)} chars)")
        else:
            print("⚠️ CoinGecko API key: Not configured")
        
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from data_sources.binance_api import BinanceAPI
        print("✅ Binance API import: OK")
    except Exception as e:
        print(f"❌ Binance API import failed: {e}")
        return False
    
    try:
        from data_sources.coingecko_api import CoinGeckoAPI
        print("✅ CoinGecko API import: OK")
    except Exception as e:
        print(f"❌ CoinGecko API import failed: {e}")
        return False
    
    try:
        from data_sources.data_manager import DataManager
        print("✅ Data Manager import: OK")
    except Exception as e:
        print(f"❌ Data Manager import failed: {e}")
        return False
    
    return True

async def test_basic_connectivity():
    """Temel bağlantıları test et."""
    print("\n🌐 Testing basic connectivity...")
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # Test basic internet connectivity
            async with session.get('https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status == 200:
                    print("✅ Internet connectivity: OK")
                else:
                    print(f"⚠️ Internet connectivity: HTTP {response.status}")
    except Exception as e:
        print(f"❌ Internet connectivity failed: {e}")
        return False
    
    return True

async def test_data_sources():
    """Data source'ları test et."""
    print("\n💰 Testing data sources...")
    
    try:
        from data_sources.data_manager import DataManager
        data_manager = DataManager()
        
        # Test with a small number of symbols
        test_symbols = ['BTCUSDT', 'ETHUSDT']
        
        print(f"Testing with symbols: {test_symbols}")
        market_data = await data_manager.get_market_data(test_symbols, force_refresh=True)
        
        if market_data:
            print(f"✅ Market data: Retrieved {len(market_data)} symbols")
            for symbol, data in market_data.items():
                price = data.get('price', 0)
                source = data.get('source', 'unknown')
                print(f"  {symbol}: ${price:,.2f} from {source}")
            return True
        else:
            print("❌ Market data: No data retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Data sources test failed: {e}")
        return False

async def test_flask_app():
    """Flask app'i test et."""
    print("\n🌐 Testing Flask app...")
    
    try:
        from main import app
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Flask app: OK")
                return True
            else:
                print(f"❌ Flask app: HTTP {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def main():
    """Ana test fonksiyonu."""
    print("🚀 Simple Test Script for Crypto AI Analyzer")
    print("=" * 50)
    print(f"📅 Test time: {datetime.now()}")
    print(f"🖥️ Platform: {sys.platform}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 50)
    
    # Test 1: Basic imports
    imports_ok = test_basic_imports()
    
    if not imports_ok:
        print("\n❌ Basic imports failed. Check your environment setup.")
        return False
    
    # Test 2: Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test connectivity
        connectivity_ok = loop.run_until_complete(test_basic_connectivity())
        
        if connectivity_ok:
            # Test data sources
            data_ok = loop.run_until_complete(test_data_sources())
        else:
            data_ok = False
        
        # Test Flask app
        flask_ok = loop.run_until_complete(test_flask_app())
        
    finally:
        loop.close()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Basic imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"Connectivity: {'✅ PASS' if connectivity_ok else '❌ FAIL'}")
    print(f"Data sources: {'✅ PASS' if data_ok else '❌ FAIL'}")
    print(f"Flask app: {'✅ PASS' if flask_ok else '❌ FAIL'}")
    
    all_ok = imports_ok and connectivity_ok and data_ok and flask_ok
    
    if all_ok:
        print("\n🎉 All tests passed! The system is ready for deployment.")
    else:
        print("\n⚠️ Some tests failed. Check the issues above before deploying.")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
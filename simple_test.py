#!/usr/bin/env python3
"""
Simple test script to verify data connectivity and API functionality.
"""

import asyncio
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append('.')

from data_sources.data_manager import DataManager
from data_sources.binance_api import BinanceAPI
import config

async def test_internet_connectivity():
    """Test basic internet connectivity."""
    print("🌐 Testing Internet Connectivity...")
    
    api = BinanceAPI()
    has_internet = api.check_internet_connectivity()
    
    if has_internet:
        print("✅ Internet connectivity: OK")
        return True
    else:
        print("❌ Internet connectivity: FAILED")
        return False

async def test_binance_api():
    """Test Binance API connectivity."""
    print("\n🔗 Testing Binance API...")
    
    try:
        async with BinanceAPI() as api:
            # Test simple ping
            result = await api.ping()
            if result:
                print("✅ Binance API ping: OK")
                
                # Test getting price for BTC
                price_data = await api.get_symbol_price("BTCUSDT")
                if price_data:
                    print(f"✅ BTC Price: ${price_data.get('price', 'N/A')}")
                    return True
                else:
                    print("❌ Failed to get BTC price")
                    return False
            else:
                print("❌ Binance API ping: FAILED")
                return False
                
    except Exception as e:
        print(f"❌ Binance API error: {e}")
        return False

async def test_data_manager():
    """Test data manager functionality."""
    print("\n📊 Testing Data Manager...")
    
    try:
        data_manager = DataManager()
        
        # Test getting market data for a few symbols
        test_symbols = ['BTCUSDT', 'ETHUSDT']
        market_data = await data_manager.get_market_data(test_symbols)
        
        if market_data:
            print(f"✅ Market data retrieved for {len(market_data)} symbols")
            
            # Check if data is live or fallback
            live_count = sum(1 for data in market_data.values() 
                           if data.get('source') not in ['fallback', 'mock'])
            
            if live_count > 0:
                print(f"✅ Live data sources: {live_count}/{len(market_data)}")
                
                # Show sample data
                for symbol, data in list(market_data.items())[:2]:
                    price = data.get('price', 0)
                    source = data.get('source', 'unknown')
                    print(f"   {symbol}: ${price:.2f} (source: {source})")
                
                return True
            else:
                print("⚠️ Only fallback data available - no live sources working")
                return False
        else:
            print("❌ No market data retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Data Manager error: {e}")
        return False

async def test_ai_clients():
    """Test AI client availability."""
    print("\n🤖 Testing AI Clients...")
    
    try:
        from llm.openai_client import OpenAIClient
        from llm.claude_client import ClaudeClient
        
        openai_client = OpenAIClient()
        claude_client = ClaudeClient()
        
        openai_available = openai_client.is_available()
        claude_available = claude_client.is_available()
        
        print(f"OpenAI: {'✅ Available' if openai_available else '❌ Not available'}")
        print(f"Claude: {'✅ Available' if claude_available else '❌ Not available'}")
        
        if openai_available or claude_available:
            print("✅ At least one AI client is available")
            return True
        else:
            print("⚠️ No AI clients available - set API keys for full functionality")
            return False
            
    except Exception as e:
        print(f"❌ AI Client test error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Crypto AI Analyzer - System Test")
    print("=" * 50)
    
    results = []
    
    # Test internet connectivity
    results.append(await test_internet_connectivity())
    
    # Test Binance API
    results.append(await test_binance_api())
    
    # Test data manager
    results.append(await test_data_manager())
    
    # Test AI clients
    results.append(await test_ai_clients())
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        print("🎉 System is ready to run!")
    elif passed >= 2:  # At least internet and one data source
        print(f"⚠️ Partial success ({passed}/{total} tests passed)")
        print("🔧 System can run with limited functionality")
    else:
        print(f"❌ Major issues detected ({passed}/{total} tests passed)")
        print("🚫 System needs troubleshooting before running")
    
    return passed >= 2

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
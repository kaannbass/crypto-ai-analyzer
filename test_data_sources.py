#!/usr/bin/env python3
"""
Test script for crypto data sources.
Run this to verify that real crypto APIs are working.
"""

import asyncio
import json
from datetime import datetime

import config
from data_sources.data_manager import DataManager


async def test_data_sources():
    """Test all crypto data sources."""
    print("🔍 Testing Crypto Data Sources...")
    print("=" * 50)
    
    data_manager = DataManager()
    
    # Test connectivity to all sources
    print("📡 Testing API connectivity...")
    connectivity = await data_manager.test_all_sources()
    
    for source, status in connectivity.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {source.title()}: {'Connected' if status else 'Failed'}")
    
    print("\n📊 Fetching real market data...")
    
    # Get real market data
    market_data = await data_manager.get_market_data(config.SYMBOLS)
    
    if market_data:
        print(f"✅ Successfully retrieved data for {len(market_data)} symbols")
        print("\n💰 Current Prices:")
        
        for symbol, data in market_data.items():
            price = data.get('price', 0)
            change_24h = data.get('change_24h', 0)
            volume = data.get('volume', 0)
            source = data.get('source', 'unknown')
            
            change_icon = "🔺" if change_24h > 0 else "🔻" if change_24h < 0 else "➖"
            
            print(f"{change_icon} {symbol}: ${price:,.2f} ({change_24h:+.2%}) "
                  f"Vol: ${volume:,.0f} [{source}]")
                  
        # Test historical data
        print(f"\n📈 Testing historical data for {config.SYMBOLS[0]}...")
        historical = await data_manager.get_historical_data(config.SYMBOLS[0], '1h', 24)
        
        if historical:
            print(f"✅ Retrieved {len(historical)} historical data points")
            
            # Show recent price action
            if len(historical) >= 3:
                latest = historical[-1]
                prev = historical[-2]
                price_change = (latest['close'] - prev['close']) / prev['close']
                
                print(f"📊 Recent action: ${latest['close']:,.2f} ({price_change:+.2%} from previous hour)")
        else:
            print("❌ Could not retrieve historical data")
            
    else:
        print("❌ No market data retrieved - check your internet connection")
        
    # Cache statistics
    cache_stats = data_manager.get_cache_stats()
    print(f"\n💾 Cache: {cache_stats['total_entries']} entries, "
          f"{cache_stats['total_size_bytes']} bytes")
    
    print("\n" + "=" * 50)
    print("📝 Test completed!")
    
    return market_data


async def test_pump_detection():
    """Test pump detection with real data."""
    print("\n🚀 Testing Pump Detection...")
    
    from pump_scanner.pump_detector import PumpDetector
    
    pump_detector = PumpDetector()
    pumps = await pump_detector.scan_for_pumps()
    
    if pumps:
        print(f"🔥 Detected {len(pumps)} potential pumps:")
        for pump in pumps:
            symbol = pump.get('symbol')
            pump_type = pump.get('pump_type')
            confidence = pump.get('confidence', 0)
            price_change = pump.get('price_change', 0)
            
            print(f"  • {symbol}: {pump_type} pump ({confidence:.2f} confidence, "
                  f"{price_change:+.2%} price change)")
    else:
        print("📊 No pumps detected at this time")


if __name__ == "__main__":
    print("🔐 Crypto AI Analyzer - Data Source Test")
    print("========================================\n")
    
    # Run the tests
    market_data = asyncio.run(test_data_sources())
    
    if market_data:
        asyncio.run(test_pump_detection())
        
        print("\n🎯 Next steps:")
        print("1. Set OPENAI_API_KEY or CLAUDE_API_KEY environment variables for AI analysis")
        print("2. Run 'python3 main.py' to start the full trading system")
        print("3. Monitor signals in data/signals.json")
    else:
        print("\n⚠️  Fix connectivity issues before running the main system") 
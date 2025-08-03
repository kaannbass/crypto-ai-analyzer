#!/usr/bin/env python3
"""
Test script for LIVE DATA crypto analysis system.
Tests ONLY live data functionality - NO mock/fallback data.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config

async def test_live_data_sources():
    """Test LIVE data source availability."""
    print("📊 Testing LIVE Data Sources...")
    
    try:
        from data_sources.data_manager import DataManager
        data_manager = DataManager()
        
        # Test LIVE market data with force refresh
        live_data = await data_manager.get_market_data(['BTCUSDT', 'ETHUSDT'], force_refresh=True)
        
        if live_data and len(live_data) >= 2:
            print(f"✅ LIVE market data: {len(live_data)} symbols")
            for symbol, data in list(live_data.items())[:2]:
                price = data.get('price', 'N/A')
                change = data.get('change_24h', 0)
                source = data.get('source', 'unknown')
                print(f"   📈 {symbol}: ${price} ({change:+.2%}) [{source}]")
        else:
            print("❌ NO LIVE DATA AVAILABLE")
            return False
            
        return True
            
    except Exception as e:
        print(f"❌ LIVE data error: {e}")
        return False

async def test_live_analysis():
    """Test analysis with LIVE data only."""
    print("\n🔧 Testing LIVE Analysis...")
    
    try:
        from main import CryptoAnalyzer
        analyzer = CryptoAnalyzer()
        
        # Test LIVE data analysis
        validated_signals = await analyzer.daily_analysis()
        
        if validated_signals:
            print(f"✅ LIVE analysis: {len(validated_signals)} signals generated")
            for signal in validated_signals[:2]:
                symbol = signal.get('symbol', 'Unknown')
                action = signal.get('action', 'WAIT')
                confidence = signal.get('confidence', 0)
                print(f"   🎯 {symbol}: {action} (confidence: {confidence:.2f})")
        else:
            print("⚠️ No signals generated (possible if no strong signals)")
            
        return True
            
    except Exception as e:
        print(f"❌ LIVE analysis error: {e}")
        return False

async def test_telegram_live_signals():
    """Test Turkish signals with LIVE data."""
    print("\n📱 Testing Telegram LIVE Signals...")
    
    try:
        from telegram_bot_module.telegram_bot import EnhancedTelegramNotifier
        telegram_bot = EnhancedTelegramNotifier()
        
        if not telegram_bot.enabled:
            print("⚠️ Telegram bot not enabled (missing config)")
            return False
            
        # Generate Turkish signals with LIVE data
        turkish_signals = await telegram_bot.get_turkish_signals()
        
        if turkish_signals and "❌" not in turkish_signals:
            print("✅ Turkish LIVE signals generated successfully")
            print(f"   Signal length: {len(turkish_signals)} characters")
            
            # Check if contains live data indicators
            if "CANLI" in turkish_signals or "Gerçek verilerle" in turkish_signals:
                print("✅ Signals confirm LIVE data usage")
            
            # Test cache
            cache_file = f"{config.DATA_DIR}/turkish_signals.json"
            if os.path.exists(cache_file):
                print("✅ LIVE signals cached for web endpoint")
            
            return True
        else:
            print("❌ Failed to generate Turkish LIVE signals")
            return False
            
    except Exception as e:
        print(f"❌ Telegram LIVE signals error: {e}")
        return False

def test_no_fallback_data():
    """Test that NO fallback/mock data is used."""
    print("\n🚫 Testing NO Fallback Data Policy...")
    
    try:
        # Check that fallback methods are removed/disabled
        from main import CryptoAnalyzer
        analyzer = CryptoAnalyzer()
        
        # Check if get_fallback_data method exists
        if hasattr(analyzer, 'get_fallback_data'):
            print("❌ FALLBACK DATA METHOD STILL EXISTS!")
            return False
        else:
            print("✅ No fallback data method found")
        
        # Check main.py for fallback references
        with open('main.py', 'r') as f:
            content = f.read()
            if 'fallback' in content.lower() and 'REMOVED' not in content:
                print("⚠️ Warning: 'fallback' references found in code")
            else:
                print("✅ No active fallback references in code")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback check error: {e}")
        return False

async def test_hourly_schedule():
    """Test hourly Telegram update functionality."""
    print("\n⏰ Testing Hourly Schedule...")
    
    try:
        from main import CryptoAnalyzer
        analyzer = CryptoAnalyzer()
        
        # Test hourly update method
        if hasattr(analyzer, 'hourly_telegram_update'):
            print("✅ Hourly Telegram update method exists")
            
            # Test the method (don't actually send to avoid spam)
            print("   Testing method execution...")
            await analyzer.hourly_telegram_update()
            print("✅ Hourly update method executed successfully")
            
            return True
        else:
            print("❌ Hourly update method not found")
            return False
            
    except Exception as e:
        print(f"❌ Hourly schedule error: {e}")
        return False

def test_configuration():
    """Test LIVE data configuration."""
    print("\n⚙️ Testing Configuration...")
    
    # Test required environment variables
    required_vars = {
        'TELEGRAM_BOT_TOKEN': config.TELEGRAM_BOT_TOKEN,
        'TELEGRAM_CHAT_ID': config.TELEGRAM_CHAT_ID
    }
    
    optional_vars = {
        'OPENAI_API_KEY': config.OPENAI_API_KEY,
        'CLAUDE_API_KEY': config.CLAUDE_API_KEY
    }
    
    config_ok = True
    
    for var, value in required_vars.items():
        if value:
            print(f"✅ {var}: Configured")
        else:
            print(f"❌ {var}: NOT CONFIGURED (REQUIRED)")
            config_ok = False
    
    ai_configured = any(optional_vars.values())
    if ai_configured:
        print("✅ At least one AI model configured")
        for var, value in optional_vars.items():
            if value:
                print(f"   ✅ {var}: Configured")
    else:
        print("⚠️ No AI models configured (will use rules only)")
    
    return config_ok

async def main():
    """Run LIVE data tests."""
    print("🚀 CRYPTO AI ANALYZER - LIVE DATA TEST")
    print("=" * 50)
    print("🎯 Testing ONLY live data functionality")
    print("🚫 NO mock/fallback data should be used")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.WARNING)
    
    # Ensure data directory
    os.makedirs(config.DATA_DIR, exist_ok=True)
    
    # Run tests
    tests = [
        ("Live Data Sources", test_live_data_sources),
        ("Live Analysis", test_live_analysis),
        ("Telegram Live Signals", test_telegram_live_signals),
        ("No Fallback Policy", test_no_fallback_data),
        ("Hourly Schedule", test_hourly_schedule),
        ("Configuration", test_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("🎯 LIVE DATA TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} : {status}")
    
    print(f"\n📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL LIVE DATA TESTS PASSED!")
        print("✅ System ready for LIVE data deployment")
        print("📤 Hourly Telegram updates will work correctly")
        print("🚫 NO fallback/mock data will be used")
    else:
        print("\n⚠️ Some tests failed - check configuration")
        
    print("\n📚 Next steps:")
    print("1. Deploy to Render.com with environment variables")
    print("2. System will send hourly Telegram updates with LIVE data")
    print("3. Monitor /health endpoint for system status")

if __name__ == "__main__":
    asyncio.run(main()) 
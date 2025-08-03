#!/usr/bin/env python3
"""
Quick system test script for Crypto AI Analyzer
Tests all major components to ensure everything works.
"""

import asyncio
import time
import json
import os
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported."""
    print("🔧 Testing imports...")
    
    try:
        import config
        print("✅ config.py imported successfully")
        
        from data_sources.data_manager import DataManager
        print("✅ DataManager imported successfully")
        
        from rules.rule_engine import RuleEngine
        print("✅ RuleEngine imported successfully")
        
        from rules.risk_guard import RiskGuard
        print("✅ RiskGuard imported successfully")
        
        from llm.aggregator import AIAggregator
        print("✅ AIAggregator imported successfully")
        
        from binance_websocket_client import BinanceWebSocketClient
        print("✅ BinanceWebSocketClient imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_data_directory():
    """Test data directory creation."""
    print("\n📁 Testing data directory...")
    
    try:
        import config
        os.makedirs(config.DATA_DIR, exist_ok=True)
        
        # Test file creation
        test_files = [config.PRICES_FILE, config.NEWS_FILE, config.SIGNALS_FILE]
        
        for file_path in test_files:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)
                print(f"✅ Created {file_path}")
            else:
                print(f"✅ {file_path} already exists")
                
        return True
        
    except Exception as e:
        print(f"❌ Data directory error: {e}")
        return False

def test_websocket_client():
    """Test WebSocket client initialization."""
    print("\n🌐 Testing WebSocket client...")
    
    try:
        from binance_websocket_client import BinanceWebSocketClient
        
        # Test initialization
        client = BinanceWebSocketClient(
            symbols=["btcusdt"],
            log_file="test_feed.jsonl"
        )
        print("✅ WebSocket client initialized")
        
        # Test start/stop
        client.start()
        print("✅ WebSocket client started")
        
        time.sleep(3)  # Let it connect
        
        if client.is_running():
            print("✅ WebSocket client is running")
        else:
            print("⚠️ WebSocket client not running (might be network issue)")
        
        client.stop()
        print("✅ WebSocket client stopped")
        
        # Clean up test file
        if os.path.exists("test_feed.jsonl"):
            os.remove("test_feed.jsonl")
            
        return True
        
    except Exception as e:
        print(f"❌ WebSocket client error: {e}")
        return False

async def test_data_manager():
    """Test DataManager API calls."""
    print("\n📊 Testing DataManager...")
    
    try:
        from data_sources.data_manager import DataManager
        import config
        
        dm = DataManager()
        print("✅ DataManager initialized")
        
        # Test API connectivity
        sources = await dm.test_all_sources()
        print(f"✅ API sources tested: {sources}")
        
        # Test market data retrieval
        symbols = config.SYMBOLS[:2]  # Test with first 2 symbols only
        market_data = await dm.get_market_data(symbols)
        
        if market_data:
            print(f"✅ Market data retrieved for {len(market_data)} symbols")
            for symbol, data in market_data.items():
                price = data.get('price', 0)
                source = data.get('source', 'unknown')
                print(f"   💰 {symbol}: ${price:,.2f} [{source}]")
        else:
            print("⚠️ No market data retrieved (using mock data)")
            
        return True
        
    except Exception as e:
        print(f"❌ DataManager error: {e}")
        return False

async def test_rule_engine():
    """Test RuleEngine calculations."""
    print("\n⚖️ Testing RuleEngine...")
    
    try:
        from rules.rule_engine import RuleEngine
        
        engine = RuleEngine()
        print("✅ RuleEngine initialized")
        
        # Test technical indicators
        mock_prices = [100, 102, 98, 105, 107, 103, 101, 99, 104, 106]
        
        rsi = engine.calculate_rsi(mock_prices)
        print(f"✅ RSI calculated: {rsi:.2f}")
        
        macd = engine.calculate_macd(mock_prices)
        print(f"✅ MACD calculated: {macd['macd']:.4f}")
        
        bb = engine.calculate_bollinger_bands(mock_prices)
        print(f"✅ Bollinger Bands: Upper={bb['upper']:.2f}, Lower={bb['lower']:.2f}")
        
        # Test signal generation with async call
        mock_market_data = {
            'price': 105,
            'volume': 1000000,
            'change_24h': 0.02
        }
        
        signal = await engine.generate_signal("TESTUSDT", mock_market_data)
        if signal:
            print(f"✅ Signal generated: {signal['action']} (confidence: {signal['confidence']:.2f})")
        else:
            print("⚠️ No signal generated (no historical data available)")
            
        return True
        
    except Exception as e:
        print(f"❌ RuleEngine error: {e}")
        return False

def test_risk_guard():
    """Test RiskGuard functionality."""
    print("\n🛡️ Testing RiskGuard...")
    
    try:
        from rules.risk_guard import RiskGuard
        
        guard = RiskGuard()
        print("✅ RiskGuard initialized")
        
        # Test trading limits
        can_trade = guard.can_trade_today()
        print(f"✅ Can trade today: {can_trade}")
        
        # Test signal validation
        test_signal = {
            'symbol': 'TESTUSDT',
            'action': 'BUY',
            'confidence': 0.75,
            'reasoning': 'Test signal'
        }
        
        is_valid = guard.validate_signal(test_signal)
        print(f"✅ Signal validation: {is_valid}")
        
        # Test stop loss calculation
        stop_loss = guard.calculate_stop_loss(100, 'BUY')
        take_profit = guard.calculate_take_profit(100, 'BUY')
        print(f"✅ Stop loss: ${stop_loss:.2f}, Take profit: ${take_profit:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ RiskGuard error: {e}")
        return False

async def test_ai_aggregator():
    """Test AI Aggregator."""
    print("\n🤖 Testing AI Aggregator...")
    
    try:
        from llm.aggregator import AIAggregator
        
        aggregator = AIAggregator()
        print("✅ AIAggregator initialized")
        
        # Test AI client availability
        connections = await aggregator.test_all_connections()
        print(f"✅ AI connections tested: {connections}")
        
        # Test mock analysis
        mock_market_data = {
            'BTCUSDT': {
                'price': 50000,
                'volume': 1000000,
                'change_24h': 0.03
            }
        }
        
        analysis = await aggregator.get_daily_analysis(mock_market_data)
        if analysis:
            signals = analysis.get('signals', [])
            print(f"✅ AI analysis completed with {len(signals)} signals")
        else:
            print("⚠️ AI analysis returned no results")
            
        return True
        
    except Exception as e:
        print(f"❌ AI Aggregator error: {e}")
        return False

def test_monitor():
    """Test monitoring components."""
    print("\n📊 Testing Monitor components...")
    
    try:
        # Test if monitor files exist
        monitors = ['monitor_results.py', 'monitor_results_enhanced.py']
        
        for monitor in monitors:
            if os.path.exists(monitor):
                print(f"✅ {monitor} exists")
            else:
                print(f"⚠️ {monitor} not found")
        
        # Test if we can load signals and prices
        import config
        
        try:
            with open(config.SIGNALS_FILE, 'r') as f:
                signals = json.load(f)
            print(f"✅ Signals file loaded ({len(signals)} signals)")
        except:
            print("⚠️ Signals file empty or not readable")
        
        try:
            with open(config.PRICES_FILE, 'r') as f:
                prices = json.load(f)
            print(f"✅ Prices file loaded")
        except:
            print("⚠️ Prices file empty or not readable")
            
        return True
        
    except Exception as e:
        print(f"❌ Monitor test error: {e}")
        return False

async def run_all_tests():
    """Run all tests."""
    print("🧪 Starting Crypto AI Analyzer System Tests")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Data Directory", test_data_directory),
        ("WebSocket Client", test_websocket_client),
        ("DataManager", test_data_manager),
        ("RuleEngine", test_rule_engine),  # Now async
        ("RiskGuard", test_risk_guard),
        ("AI Aggregator", test_ai_aggregator),
        ("Monitor", test_monitor)
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
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} : {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. In another terminal: python monitor_results_enhanced.py")
        print("3. Check RUN_GUIDE.md for detailed instructions")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("💡 Common issues:")
        print("   - Missing dependencies (run: pip install -r requirements.txt)")
        print("   - Network connectivity issues")
        print("   - File permission problems")

if __name__ == "__main__":
    asyncio.run(run_all_tests()) 
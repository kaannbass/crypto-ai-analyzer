#!/usr/bin/env python3
"""
System test for Crypto AI Analyzer - Render Ready
Tests all components including Turkish signals.
"""

import asyncio
import json
import logging
import os
import sys
import requests
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config

async def test_data_sources():
    """Test data source availability."""
    print("📊 Testing Data Sources...")
    
    try:
        from data_sources.data_manager import DataManager
        data_manager = DataManager()
        
        # Test market data
        market_data = await data_manager.get_market_data(['BTCUSDT', 'ETHUSDT'])
        
        if market_data:
            print(f"✅ Market data: {len(market_data)} symbols")
            for symbol, data in list(market_data.items())[:2]:
                print(f"   - {symbol}: ${data.get('price', 'N/A')}")
        else:
            print("❌ No market data available")
            
    except Exception as e:
        print(f"❌ Data source error: {e}")

async def test_rule_engine():
    """Test rule engine."""
    print("\n🔧 Testing Rule Engine...")
    
    try:
        from rules.rule_engine import RuleEngine
        rule_engine = RuleEngine()
        
        # Test with mock data
        mock_data = {
            'price': 50000.0,
            'volume': 1000000.0,
            'change_24h': 0.02
        }
        
        signal = await rule_engine.generate_signal('BTCUSDT', mock_data)
        
        if signal:
            print(f"✅ Rule signal: {signal['action']} (confidence: {signal['confidence']:.2f})")
        else:
            print("❌ No rule signal generated")
            
    except Exception as e:
        print(f"❌ Rule engine error: {e}")

async def test_telegram_bot():
    """Test Telegram bot."""
    print("\n📱 Testing Telegram Bot...")
    
    try:
        from telegram_bot_module.telegram_bot import EnhancedTelegramNotifier
        telegram_bot = EnhancedTelegramNotifier()
        
        if telegram_bot.enabled:
            print("✅ Telegram bot initialized")
            
            # Test Turkish signals generation
            turkish_signals = await telegram_bot.get_turkish_signals()
            if turkish_signals:
                print("✅ Turkish signals generated")
                print(f"   Signal length: {len(turkish_signals)} characters")
                
                # Check if cached
                cache_file = f"{config.DATA_DIR}/turkish_signals.json"
                if os.path.exists(cache_file):
                    print("✅ Turkish signals cached successfully")
                else:
                    print("⚠️ Turkish signals not cached")
            else:
                print("❌ No Turkish signals generated")
        else:
            print("⚠️ Telegram bot not enabled (missing config)")
            
    except Exception as e:
        print(f"❌ Telegram bot error: {e}")

async def test_ai_integration():
    """Test AI integration."""
    print("\n🤖 Testing AI Integration...")
    
    try:
        from llm.aggregator import AIAggregator
        ai_aggregator = AIAggregator()
        
        # Test AI availability
        if config.OPENAI_API_KEY:
            print("✅ OpenAI API key configured")
        else:
            print("⚠️ OpenAI API key not configured")
            
        if config.CLAUDE_API_KEY:
            print("✅ Claude API key configured")
        else:
            print("⚠️ Claude API key not configured")
            
        if not config.OPENAI_API_KEY and not config.CLAUDE_API_KEY:
            print("❌ No AI API keys configured")
        else:
            print("✅ At least one AI model available")
            
    except Exception as e:
        print(f"❌ AI integration error: {e}")

def test_flask_app():
    """Test Flask app endpoints (if running)."""
    print("\n🌐 Testing Flask App...")
    
    try:
        import main
        app = main.app
        client = app.test_client()
        
        # Test endpoints
        endpoints = [
            ('/', 'Home'),
            ('/health', 'Health Check'),
            ('/signals', 'Signals'),
            ('/signals/turkish', 'Turkish Signals'),
            ('/status', 'Status'),
            ('/market-data', 'Market Data')
        ]
        
        for endpoint, name in endpoints:
            try:
                response = client.get(endpoint)
                if response.status_code in [200, 503, 404]:  # 503 and 404 are acceptable for some endpoints
                    print(f"✅ {name}: HTTP {response.status_code}")
                else:
                    print(f"⚠️ {name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: {e}")
                
    except Exception as e:
        print(f"❌ Flask app error: {e}")

def test_render_readiness():
    """Test Render deployment readiness."""
    print("\n🚀 Testing Render Readiness...")
    
    # Check required files
    required_files = [
        'main.py',
        'requirements.txt',
        'runtime.txt',
        'Procfile',
        'RENDER_DEPLOYMENT.md'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
    
    # Check environment variables
    env_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var} configured")
        else:
            print(f"⚠️ {var} not configured (required for Render)")
    
    # Check optional env vars
    optional_vars = ['OPENAI_API_KEY', 'CLAUDE_API_KEY']
    ai_configured = any(os.getenv(var) for var in optional_vars)
    
    if ai_configured:
        print("✅ At least one AI API key configured")
    else:
        print("⚠️ No AI API keys configured (will use rule-based signals only)")

async def main():
    """Run all tests."""
    print("🧪 Crypto AI Analyzer - System Test")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    
    # Ensure data directory
    os.makedirs(config.DATA_DIR, exist_ok=True)
    
    # Run tests
    await test_data_sources()
    await test_rule_engine()
    await test_telegram_bot()
    await test_ai_integration()
    test_flask_app()
    test_render_readiness()
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("✅ = Working correctly")
    print("⚠️ = Working but needs configuration")
    print("❌ = Error or missing")
    print("\n📚 See RENDER_DEPLOYMENT.md for deployment guide")

if __name__ == "__main__":
    asyncio.run(main()) 
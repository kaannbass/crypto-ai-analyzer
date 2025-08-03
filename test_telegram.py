"""
Test script for Telegram bot integration.
Tests all notification types and bot functionality.
"""

import asyncio
import logging
from datetime import datetime
from telegram_bot_module.telegram_bot import test_telegram, send_signal, send_news, send_macro_analysis, send_anomaly, send_daily_summary, send_startup

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_telegram_bot():
    """Test all Telegram bot functionality."""
    print("🤖 Testing Telegram Bot Integration...")
    print("=" * 60)
    
    # Test 1: Connection test
    print("1️⃣ Testing connection...")
    try:
        success = await test_telegram()
        if success:
            print("✅ Connection test successful!")
        else:
            print("❌ Connection test failed - check token and configuration")
            return
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return
    
    await asyncio.sleep(2)
    
    # Test 2: Startup notification
    print("\n2️⃣ Testing startup notification...")
    try:
        await send_startup()
        print("✅ Startup notification sent!")
    except Exception as e:
        print(f"❌ Startup notification failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 3: Trading signal
    print("\n3️⃣ Testing trading signal...")
    try:
        test_signal = {
            'symbol': 'BTCUSDT',
            'action': 'BUY',
            'confidence': 0.85,
            'reasoning': 'Strong bullish momentum with volume confirmation',
            'rule_analysis': {
                'indicators': {
                    'rsi': 65.5,
                },
                'current_price': 114282.00
            },
            'ai_analysis': {'enhanced': True}
        }
        await send_signal(test_signal)
        print("✅ Trading signal sent!")
    except Exception as e:
        print(f"❌ Trading signal failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 4: News update
    print("\n4️⃣ Testing news update...")
    try:
        test_news = [
            {
                'title': 'Bitcoin Reaches New All-Time High',
                'source': 'CoinDesk',
                'sentiment': 'bullish'
            },
            {
                'title': 'Fed Announces Rate Cut Decision',
                'source': 'Reuters',
                'sentiment': 'neutral'
            },
            {
                'title': 'DeFi Protocol Hack Causes Market Concern',
                'source': 'CryptoNews',
                'sentiment': 'bearish'
            }
        ]
        await send_news(test_news)
        print("✅ News update sent!")
    except Exception as e:
        print(f"❌ News update failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 5: Macro analysis
    print("\n5️⃣ Testing macro analysis...")
    try:
        test_macro = {
            'market_sentiment': {
                'short_term': 'Bullish',
                'medium_term': 'Neutral',
                'confidence': 'High'
            },
            'volatility': 'Moderate',
            'signals': [
                {'symbol': 'BTCUSDT', 'action': 'BUY', 'confidence': 0.8},
                {'symbol': 'ETHUSDT', 'action': 'WAIT', 'confidence': 0.5}
            ],
            'macro_factors': {
                'primary_risk': 'Federal Reserve policy uncertainty',
                'opportunities': ['DeFi adoption', 'Institutional inflows']
            }
        }
        await send_macro_analysis(test_macro)
        print("✅ Macro analysis sent!")
    except Exception as e:
        print(f"❌ Macro analysis failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 6: Anomaly alert
    print("\n6️⃣ Testing anomaly alert...")
    try:
        test_anomaly = {
            'symbol': 'SOLUSDT',
            'type': 'pump',
            'price_change': 0.087,  # +8.7%
            'volume_ratio': 4.2,
            'confidence': 0.92
        }
        await send_anomaly(test_anomaly)
        print("✅ Anomaly alert sent!")
    except Exception as e:
        print(f"❌ Anomaly alert failed: {e}")
    
    await asyncio.sleep(2)
    
    # Test 7: Daily summary
    print("\n7️⃣ Testing daily summary...")
    try:
        test_stats = {
            'total_signals': 12,
            'buy_signals': 4,
            'sell_signals': 2,
            'wait_signals': 6,
            'avg_confidence': 0.64
        }
        await send_daily_summary(test_stats)
        print("✅ Daily summary sent!")
    except Exception as e:
        print(f"❌ Daily summary failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Telegram bot test completed!")
    print("\n💡 If all tests passed, your Telegram bot is ready!")
    print("📱 Check your Telegram chat for all the test messages.")
    print("\n🔧 Configuration:")
    print("   • Make sure TELEGRAM_BOT_TOKEN is set")
    print("   • Make sure TELEGRAM_CHAT_ID is set (optional)")
    print("   • Bot should be added to your chat/channel")

if __name__ == "__main__":
    asyncio.run(test_telegram_bot()) 
#!/usr/bin/env python3
"""
Test script for Turkish trading signals format.
"""

import asyncio
import logging
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_bot_module.telegram_bot import EnhancedTelegramNotifier
import config

async def test_turkish_signals():
    """Test Turkish signals generation."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🇹🇷 Türkçe Sinyal Formatı Test Ediliyor...")
    print("=" * 50)
    
    try:
        # Initialize telegram notifier
        telegram_bot = EnhancedTelegramNotifier()
        
        # Test Turkish signals generation
        print("📊 Gerçek verilerle sinyal oluşturuluyor...")
        
        turkish_signals = await telegram_bot.get_turkish_signals()
        
        print("\n" + "="*50)
        print("🎯 OLUŞTURULAN SİNYALLER:")
        print("="*50)
        print(turkish_signals)
        print("="*50)
        
        # If telegram is configured, send the signal
        if config.TELEGRAM_ENABLED and config.TELEGRAM_CHAT_ID:
            print("\n📤 Telegram'a gönderiliyor...")
            success = await telegram_bot.send_message(turkish_signals)
            if success:
                print("✅ Telegram gönderimi başarılı!")
            else:
                print("❌ Telegram gönderimi başarısız!")
        else:
            print("📱 Telegram yapılandırılmamış - sadece yerel test")
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Crypto AI Analyzer - Türkçe Sinyal Test")
    asyncio.run(test_turkish_signals()) 
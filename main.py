"""
Main orchestrator for crypto analysis and trading signal system.
Coordinates all system components with Flask web server.
"""

import asyncio
import json
import logging
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, jsonify, request

import config
from rules.rule_engine import RuleEngine
from rules.risk_guard import RiskGuard
from rules.stats_engine import StatsEngine
from llm.aggregator import AIAggregator
from scheduler.time_trigger import TimeTrigger
from pump_scanner.pump_detector import PumpDetector
from binance_websocket_client import BinanceWebSocketClient
from data_sources.news_processor import NewsProcessor, NEWS_API_AVAILABLE

# Telegram Bot
try:
    from telegram_bot_module.telegram_bot import EnhancedTelegramNotifier
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

# Flask app for deployment
app = Flask(__name__)
analyzer_instance = None

# Global analyzer instance for telegram bot access
analyzer = None

@app.route('/')
def home():
    """Home endpoint."""
    return jsonify({
        "status": "running",
        "service": "Crypto AI Analyzer",
        "version": "2.0.0",
        "endpoints": ["/health", "/signals", "/signals/turkish", "/status", "/market-data"]
    })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    global analyzer_instance
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "analyzer": analyzer_instance is not None and analyzer_instance.running,
            "telegram": TELEGRAM_AVAILABLE and config.TELEGRAM_ENABLED,
            "news_api": NEWS_API_AVAILABLE,
            "ai_models": bool(config.OPENAI_API_KEY or config.CLAUDE_API_KEY)
        }
    }
    
    if not status["components"]["analyzer"]:
        status["status"] = "degraded"
        return jsonify(status), 503
    return jsonify(status), 200

def _get_signals_from_file(count: int = 5) -> List[Dict]:
    """Helper function to get signals from file."""
    if not os.path.exists(config.SIGNALS_FILE):
        return []
    
    try:
        with open(config.SIGNALS_FILE, 'r') as f:
            all_signals = json.load(f)
            return all_signals[-count:] if all_signals else []
    except Exception:
        return []

@app.route('/signals')
def get_signals():
    """Get latest trading signals."""
    try:
        signals = _get_signals_from_file()
        return jsonify({
            "signals": signals,
            "count": len(signals),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/signals/turkish')
def get_turkish_signals():
    """Get Turkish format signals."""
    try:
        signals = _get_signals_from_file()
        # Convert to Turkish format
        turkish_signals = []
        for signal in signals:
            turkish_signal = {
                "sembol": signal.get("symbol", ""),
                "sinyal": signal.get("signal", ""),
                "fiyat": signal.get("price", 0),
                "zaman": signal.get("timestamp", ""),
                "güven_seviyesi": signal.get("confidence", 0)
            }
            turkish_signals.append(turkish_signal)
        
        return jsonify({
            "sinyaller": turkish_signals,
            "toplam": len(turkish_signals),
            "zaman": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"hata": str(e)}), 500

@app.route('/status')
def get_status():
    """Get system status."""
    try:
        global analyzer_instance
        if not analyzer_instance:
            return jsonify({"error": "Analyzer not initialized"}), 503
        
        return jsonify({
            "uptime": time.time() - analyzer_instance.start_time,
            "running": analyzer_instance.running,
            "last_analysis": getattr(analyzer_instance, 'last_analysis_time', None),
            "components": {
                "telegram": TELEGRAM_AVAILABLE,
                "news_api": NEWS_API_AVAILABLE,
                "websocket": analyzer_instance.websocket_client is not None
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/market-data')
def get_market_data():
    """Get current market data."""
    try:
        global analyzer_instance
        if not analyzer_instance:
            return jsonify({"error": "Analyzer not initialized"}), 503
        
        # Get recent market data from data manager
        market_data = asyncio.run(analyzer_instance.get_market_data())
        return jsonify({
            "market_data": market_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

class CryptoAnalyzer:
    def __init__(self):
        self.start_time = time.time()
        self.setup_logging()
        self.rule_engine = RuleEngine()
        self.risk_guard = RiskGuard()
        self.stats_engine = StatsEngine()
        self.ai_aggregator = AIAggregator()
        self.time_trigger = TimeTrigger()
        self.pump_detector = PumpDetector()
        
        # WebSocket client for real-time data
        self.websocket_client = None
        self.setup_websocket_client()
        
        # News processor
        self.news_processor = NewsProcessor() if NEWS_API_AVAILABLE else None
        
        # Telegram notifier with Turkish format
        self.telegram_notifier = EnhancedTelegramNotifier() if TELEGRAM_AVAILABLE else None
        
        self.ensure_data_directory()
        self.load_existing_data()
        
        self.running = False
        
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=getattr(logging, config.LOG_LEVEL),
            format=config.LOG_FORMAT,
            handlers=[
                logging.FileHandler(config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_websocket_client(self):
        """Setup WebSocket client for real-time data."""
        try:
            self.websocket_client = BinanceWebSocketClient()
            self.logger.info("WebSocket client initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebSocket client: {e}")
            self.websocket_client = None
        
    def ensure_data_directory(self):
        """Ensure data directory exists."""
        os.makedirs(config.DATA_DIR, exist_ok=True)
        
    def load_existing_data(self):
        """Load existing signal data."""
        try:
            if os.path.exists(config.SIGNALS_FILE):
                with open(config.SIGNALS_FILE, 'r') as f:
                    signals = json.load(f)
                    self.logger.info(f"Loaded {len(signals)} existing signals")
        except Exception as e:
            self.logger.error(f"Error loading existing data: {e}")

    async def get_market_data(self) -> Dict:
        """Get market data with LIVE DATA ONLY - NEVER return fake data."""
        try:
            # Import data manager
            from data_sources.data_manager import DataManager
            data_manager = DataManager()
            
            # Force refresh to get fresh LIVE data only
            live_data = await data_manager.get_market_data(config.SYMBOLS, force_refresh=True)
            
            if not live_data:
                self.logger.error("❌ NO LIVE DATA AVAILABLE - System will NOT proceed")
                self.logger.error("📍 Please check:")
                self.logger.error("   1. Internet connection")
                self.logger.error("   2. VPN if APIs are blocked")
                self.logger.error("   3. API keys configuration")
                return {}
            
            # Verify ALL data is real (not fallback/mock/default)
            real_data_count = sum(1 for data in live_data.values() 
                                if data.get('source') not in ['fallback', 'mock', 'default'])
            
            if real_data_count == 0:
                self.logger.error("❌ ALL DATA IS FAKE/FALLBACK - REJECTING COMPLETELY")
                self.logger.error("📍 System will NOT proceed with fake data")
                return {}
            
            if real_data_count < len(live_data):
                fake_count = len(live_data) - real_data_count
                self.logger.warning(f"⚠️ {fake_count} symbols have fake data - removing them")
                # Remove fake data entries
                filtered_data = {symbol: data for symbol, data in live_data.items() 
                               if data.get('source') not in ['fallback', 'mock', 'default']}
                live_data = filtered_data
            
            self.logger.info(f"✅ Retrieved {len(live_data)} symbols with REAL data only")
            return live_data
            
        except Exception as e:
            self.logger.error(f"Error getting market data: {e}")
            return {}
    
    def _assess_data_quality(self, data: Dict) -> str:
        """Assess the quality of market data."""
        if not data:
            return "NONE"
        
        total_symbols = len(config.SYMBOLS)
        available_symbols = len(data)
        coverage = available_symbols / total_symbols
        
        # Check for fallback or partial data
        fallback_count = sum(1 for symbol_data in data.values() 
                           if symbol_data.get('source') in ['fallback', 'binance_partial'])
        
        if fallback_count > 0:
            return f"PARTIAL ({available_symbols}/{total_symbols} symbols, {fallback_count} fallback)"
        elif coverage >= 0.8:
            return f"GOOD ({available_symbols}/{total_symbols} symbols)"
        elif coverage >= 0.5:
            return f"FAIR ({available_symbols}/{total_symbols} symbols)"
        else:
            return f"POOR ({available_symbols}/{total_symbols} symbols)"

    async def save_market_data(self, market_data: Dict):
        """Save market data to file for web endpoints."""
        try:
            prices_file = f"{config.DATA_DIR}/prices.json"
            market_data_with_timestamp = {
                **market_data,
                "_timestamp": datetime.utcnow().isoformat(),
                "_count": len(market_data)
            }
            
            with open(prices_file, 'w') as f:
                json.dump(market_data_with_timestamp, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving market data: {e}")

    async def get_crypto_news_data(self, limit: int = 20) -> List[Dict]:
        """Get latest crypto news."""
        if not NEWS_API_AVAILABLE or not self.news_processor:
            self.logger.warning("News API not available")
            return []
            
        try:
            news_data = await self.news_processor.get_crypto_news(limit=limit)
            self.logger.info(f"Retrieved {len(news_data)} news articles")
            
            # Save news data
            self.save_news_data(news_data)
            
            return news_data
            
        except Exception as e:
            self.logger.error(f"Error fetching crypto news: {e}")
            return []

    def save_news_data(self, news_data: List[Dict]):
        """Save news data to file."""
        try:
            news_file = f"{config.DATA_DIR}/news.json"
            
            # Load existing news
            existing_news = []
            if os.path.exists(news_file):
                with open(news_file, 'r') as f:
                    existing_news = json.load(f)
            
            # Add new news (avoid duplicates by title)
            existing_titles = {news.get('title', '') for news in existing_news}
            new_articles = [news for news in news_data if news.get('title', '') not in existing_titles]
            
            # Combine and limit to last 100 articles
            all_news = new_articles + existing_news
            all_news = all_news[:100]
            
            # Save back to file
            with open(news_file, 'w') as f:
                json.dump(all_news, f, indent=2)
                
            if new_articles:
                self.logger.info(f"Saved {len(new_articles)} new news articles")
                
        except Exception as e:
            self.logger.error(f"Error saving news data: {e}")
            
    # REMOVED: No fallback/mock data - LIVE DATA ONLY

    def get_live_prices(self) -> Dict:
        """Get live prices from WebSocket if available."""
        if self.websocket_client:
            try:
                return self.websocket_client.get_current_prices()
            except Exception as e:
                self.logger.error(f"Error getting live prices: {e}")

        return {}
            
    async def daily_analysis(self):
        """Perform analysis with LIVE DATA ONLY - skip if no real data."""
        self.logger.info("🔄 Starting daily analysis with LIVE DATA requirement...")
        
        # Check if we can trade today
        if not self.risk_guard.can_trade_today():
            self.logger.info("Daily trading limits reached, skipping analysis")
            return
            
        # Get market data (LIVE ONLY)
        market_data = await self.get_market_data()
        
        # If NO REAL DATA AT ALL, completely abort analysis
        if not market_data:
            self.logger.error("❌ NO REAL DATA AVAILABLE - ABORTING ALL ANALYSIS")
            self.logger.error("📍 System will NOT generate any signals or analysis")
            self.logger.error("📍 Please fix data sources and restart")
            
            # Send notification about data unavailability
            if TELEGRAM_AVAILABLE and self.telegram_notifier:
                try:
                    no_data_msg = (
                        "🚫 <b>GERÇEK VERİ YOK</b>\n\n"
                        "❌ Hiç gerçek piyasa verisi bulunamadı\n"
                        "🔄 Sistem fake veri KULLANMIYOR\n\n"
                        "📍 <b>Çözümler:</b>\n"
                        "• VPN kullanın\n"
                        "• İnternet bağlantısını kontrol edin\n"
                        "• API anahtarlarını doğrulayın\n\n"
                        "<i>Gerçek veriler olmadan işlem yapılmaz.</i>"
                    )
                    await self.telegram_notifier.send_message(no_data_msg)
                except Exception as e:
                    self.logger.error(f"Failed to send no-data notification: {e}")
            
            return
        
        self.logger.info(f"✅ Processing LIVE data for {len(market_data)} symbols")
        
        # Verify all data is real (double-check)
        real_sources = sum(1 for data in market_data.values() 
                          if data.get('source') not in ['fallback', 'mock', 'default'])
        
        if real_sources == 0:
            self.logger.error("❌ All data appears to be fallback - aborting analysis")
            return
        
        self.logger.info(f"✅ Confirmed {real_sources}/{len(market_data)} symbols have real data sources")
        
        # Generate signals using rules with LIVE data ONLY
        rule_signals = []
        for symbol in config.SYMBOLS:
            if symbol in market_data:
                # Only process if data source is real
                data_source = market_data[symbol].get('source', 'unknown')
                if data_source not in ['fallback', 'mock', 'default']:
                    signal = await self.rule_engine.generate_signal(symbol, market_data[symbol])
                    if signal:
                        signal['data_source'] = data_source  # Mark data source
                        rule_signals.append(signal)
                        self.logger.info(f"✅ Generated signal for {symbol} using {data_source} data")
                else:
                    self.logger.warning(f"⚠️ Skipping {symbol} - data source is {data_source}")
                    
        # Get AI analysis if available (with LIVE data ONLY)
        ai_signals = []
        try:
            ai_analysis = await self.ai_aggregator.get_daily_analysis(market_data)
            if ai_analysis:
                ai_signals = ai_analysis.get('signals', [])
                # Mark AI signals as using real data
                for signal in ai_signals:
                    signal['data_source'] = 'live_data_ai_analysis'
        except Exception as e:
            self.logger.warning(f"AI analysis failed: {e}")
            
        # Combine and validate signals
        final_signals = self.combine_signals(rule_signals, ai_signals)
        
        # Apply risk management
        validated_signals = []
        for signal in final_signals:
            if self.risk_guard.validate_signal(signal):
                validated_signals.append(signal)
                self.save_signal(signal)
        
        if validated_signals:
            self.logger.info(f"✅ Daily analysis complete with LIVE data. Generated {len(validated_signals)} validated signals")
            
            # Send success notification
            if TELEGRAM_AVAILABLE and self.telegram_notifier:
                try:
                    success_msg = (
                        f"✅ <b>Günlük Analiz Tamamlandı</b>\n\n"
                        f"📊 {real_sources} coin için canlı veri kullanıldı\n"
                        f"🎯 {len(validated_signals)} sinyal üretildi\n"
                        f"🕐 {datetime.utcnow().strftime('%H:%M:%S')} UTC\n\n"
                        f"<i>Sadece gerçek verilerle analiz yapıldı.</i>"
                    )
                    await self.telegram_notifier.send_message(success_msg)
                except Exception as e:
                    self.logger.error(f"Failed to send success notification: {e}")
        else:
            self.logger.warning("⚠️ No validated signals generated from live data")
        
        return validated_signals

    async def hourly_telegram_update(self):
        """Send consolidated Turkish signals to Telegram every hour - LIVE DATA ONLY."""
        try:
            self.logger.info("📤 Preparing consolidated hourly update with LIVE DATA requirement...")
            
            if not self.telegram_notifier:
                self.logger.warning("Telegram notifier not available")
                return
            
            # Get market data (LIVE ONLY)
            market_data = await self.get_market_data()
            
            if not market_data:
                self.logger.warning("No LIVE market data available for Telegram update")
                
                # Send "no data" notification
                no_data_msg = (
                    "⚠️ <b>Veri Durumu</b>\n\n"
                    "❌ Şu anda canlı piyasa verilerine erişilemiyor\n"
                    "🔄 Sistem gerçek veri bekliyor\n\n"
                    "📍 <b>Durum:</b> VPN gerekebilir\n"
                    "🕐 Sonraki kontrol: 2 saat sonra\n\n"
                    "<i>Sahte verilerle işlem yapılmaz.</i>"
                )
                await self.telegram_notifier.send_message(no_data_msg)
                return
            
            # Verify data is actually real
            real_sources = sum(1 for data in market_data.values() 
                              if data.get('source') not in ['fallback', 'mock', 'default'])
            
            if real_sources == 0:
                self.logger.warning("All data appears to be fallback - sending warning")
                
                fallback_msg = (
                    "⚠️ <b>Veri Kalite Uyarısı</b>\n\n"
                    "❌ Sadece yedek veriler mevcut\n"
                    "🚫 Gerçek piyasa verisi alınamıyor\n\n"
                    "📍 Lütfen VPN kullanın veya bağlantıyı kontrol edin\n"
                    "🔄 Gerçek veriler gelene kadar bekleniyor\n\n"
                    "<i>Yedek verilerle sinyal üretilmez.</i>"
                )
                await self.telegram_notifier.send_message(fallback_msg)
                return
            
            # Prepare consolidated summary message with REAL DATA
            summary_parts = []
            
            # 1. System Status with data source info
            total_symbols = len(market_data)
            data_quality = f"LIVE ({real_sources}/{total_symbols} gerçek veri)"
            summary_parts.append(f"🤖 <b>Sistem Durumu</b>\n📊 Veri Kalitesi: {data_quality}")
            
            # 2. Market Overview (only real data)
            positive_count = sum(1 for symbol, data in market_data.items() 
                               if data.get('change_24h', 0) > 0 and data.get('source') not in ['fallback', 'mock', 'default'])
            negative_count = real_sources - positive_count
            
            summary_parts.append(f"📈 <b>Piyasa Özeti</b> (Canlı Veri)\n"
                                f"• Toplam: {real_sources} coin\n"
                                f"• Yükselişte: {positive_count} 🟢\n"
                                f"• Düşüşte: {negative_count} 🔴")
            
            # 3. Top 3 Signals from REAL data only
            try:
                signals = []
                for symbol in list(market_data.keys())[:5]:  # Check top 5 symbols
                    data = market_data[symbol]
                    # Only process if data source is real
                    if data.get('source') not in ['fallback', 'mock', 'default']:
                        signal = await self.rule_engine.generate_signal(symbol, data)
                        if signal:
                            signal['data_source'] = data.get('source', 'unknown')
                            signals.append(signal)
                
                if signals:
                    signal_text = "🎯 <b>Canlı Sinyaller</b>\n"
                    for i, signal in enumerate(signals[:3], 1):
                        symbol = signal.get('symbol', 'Unknown')
                        action = signal.get('action', 'WAIT')
                        confidence = signal.get('confidence', 0)
                        price = signal.get('current_price', 0)
                        source = signal.get('data_source', 'unknown')
                        
                        action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'WAIT': '🟡'}.get(action, '⚪')
                        confidence_text = f"{confidence:.0%}" if confidence > 0 else "Düşük"
                        
                        signal_text += f"{i}. {symbol} {action_emoji} {action}\n"
                        signal_text += f"   💰 ${price:.2f} | 📊 {confidence_text}\n"
                        signal_text += f"   📡 Kaynak: {source}\n"
                    
                    summary_parts.append(signal_text.strip())
                else:
                    summary_parts.append("🎯 <b>Sinyaller</b>\nCanlı verilerden aktif sinyal yok")
                    
            except Exception as e:
                self.logger.error(f"Error generating live signals summary: {e}")
                summary_parts.append("🎯 <b>Sinyaller</b>\nSinyal analizi yapılamadı")
            
            # 4. AI Status
            ai_status = "🤖 <b>AI Durumu</b>\n"
            if hasattr(self, 'ai_aggregator'):
                openai_available = self.ai_aggregator.openai_client.is_available()
                claude_available = self.ai_aggregator.claude_client.is_available()
                
                ai_status += f"• OpenAI: {'✅' if openai_available else '❌'}\n"
                ai_status += f"• Claude: {'✅' if claude_available else '❌'}"
            else:
                ai_status += "• Durum: Bilinmiyor"
            
            summary_parts.append(ai_status)
            
            # 5. Data source breakdown
            source_breakdown = {}
            for data in market_data.values():
                source = data.get('source', 'unknown')
                if source not in ['fallback', 'mock', 'default']:
                    source_breakdown[source] = source_breakdown.get(source, 0) + 1
            
            if source_breakdown:
                source_text = "📡 <b>Veri Kaynakları</b>\n"
                for source, count in source_breakdown.items():
                    source_text += f"• {source}: {count} coin\n"
                summary_parts.append(source_text.strip())
            
            # 6. Timestamp
            from datetime import datetime
            summary_parts.append(f"🕐 <b>Güncelleme:</b> {datetime.utcnow().strftime('%H:%M:%S')} UTC")
            
            # Combine all parts into single message
            consolidated_message = "\n\n".join(summary_parts)
            
            # Add header
            final_message = "📊 <b>2 SAATLİK CANLI VERİ RAPORU</b>\n" + "=" * 35 + "\n\n" + consolidated_message
            final_message += "\n\n<i>⚡ Sadece gerçek verilerle analiz yapıldı</i>"
            
            # Send single consolidated message
            success = await self.telegram_notifier.send_message(final_message)
            
            if success:
                self.logger.info(f"✅ Consolidated hourly update sent successfully (using {real_sources} live sources)")
            else:
                self.logger.error("❌ Failed to send consolidated Telegram update")
                
        except Exception as e:
            self.logger.error(f"Error in consolidated hourly update: {e}")
            # Send simple error notification
            if self.telegram_notifier:
                try:
                    error_msg = f"⚠️ <b>Sistem Uyarısı</b>\n\nGüncelleme sırasında hata:\n<code>{str(e)[:100]}...</code>"
                    await self.telegram_notifier.send_message(error_msg)
                except:
                    pass

    async def macro_sentiment_analysis(self, news_data: List = None, events_data: List = None):
        """Perform comprehensive macro sentiment analysis."""
        self.logger.info("Starting macro sentiment analysis...")
        
        try:
            # Get market data
            market_data = await self.get_market_data()
            
            # Get latest news if not provided
            if news_data is None:
                news_data = await self.get_crypto_news_data(limit=15)
            
            # Get macro sentiment analysis from AI models
            macro_analysis = await self.ai_aggregator.get_macro_sentiment_analysis(
                market_data, news_data, events_data
            )
            
            if not macro_analysis:
                self.logger.warning("No macro sentiment analysis available")
                return None
                
            # Extract signals and apply risk management
            signals = macro_analysis.get('signals', [])
            validated_signals = []
            
            for signal in signals:
                if self.risk_guard.validate_signal(signal):
                    validated_signals.append(signal)
                    
                    # Save enhanced signal with macro context
                    enhanced_signal = signal.copy()
                    enhanced_signal['analysis_type'] = 'macro_sentiment'
                    enhanced_signal['market_sentiment'] = macro_analysis.get('market_sentiment', {})
                    enhanced_signal['macro_factors'] = macro_analysis.get('macro_factors', {})
                    enhanced_signal['risk_assessment'] = macro_analysis.get('risk_assessment', {})
                    
                    self.save_signal(enhanced_signal)
                    
                    # Send signal to Telegram
                    if TELEGRAM_AVAILABLE:
                        try:
                            await self.telegram_notifier.send_turkish_trading_signal(enhanced_signal)
                        except Exception as e:
                            self.logger.error(f"Failed to send macro signal to Telegram: {e}")
            
            # Log macro insights
            sentiment = macro_analysis.get('market_sentiment', {})
            volatility = macro_analysis.get('volatility', 'Unknown')
            primary_risk = macro_analysis.get('macro_factors', {}).get('primary_risk', 'Unknown')
            
            self.logger.info(f"Macro Analysis Complete:")
            self.logger.info(f"  - Market Sentiment: {sentiment.get('short_term', 'Unknown')}")
            self.logger.info(f"  - Volatility: {volatility}")
            self.logger.info(f"  - Primary Risk: {primary_risk}")
            self.logger.info(f"  - Validated Signals: {len(validated_signals)}")
            self.logger.info(f"  - News Articles Analyzed: {len(news_data) if news_data else 0}")
            
            # Save macro analysis results
            self.save_macro_analysis(macro_analysis)
            
            # Send macro analysis to Telegram
            if TELEGRAM_AVAILABLE:
                try:
                    await self.telegram_notifier.send_macro_analysis(macro_analysis)
                except Exception as e:
                    self.logger.error(f"Failed to send macro analysis to Telegram: {e}")
            
            return macro_analysis
            
        except Exception as e:
            self.logger.error(f"Macro sentiment analysis failed: {e}")
            # Send error to Telegram
            if TELEGRAM_AVAILABLE:
                try:
                    await self.telegram_notifier.send_error_notification(str(e), "Macro Analysis")
                except:
                    pass
            return None

    async def news_based_analysis(self):
        """Analyze crypto news and include in consolidated updates (no separate notifications)."""
        try:
            self.logger.info("Starting news-based analysis...")
            
            # Get crypto news
            news_data = await self.get_crypto_news_data(limit=15)
            
            if not news_data:
                self.logger.warning("No news data available")
                return
                
            # Analyze news sentiment
            news_analysis = await self.analyze_news_sentiment(news_data)
            
            if news_analysis:
                sentiment = news_analysis.get('overall_sentiment', 'neutral')
                impact = news_analysis.get('market_impact', 'low')
                
                self.logger.info("News Analysis Summary:")
                self.logger.info(f"  - Overall Sentiment: {sentiment}")
                self.logger.info(f"  - Impact Level: {impact}")
                self.logger.info(f"  - Key Themes: {', '.join(news_analysis.get('key_themes', []))}")
                self.logger.info(f"  - Articles Processed: {len(news_data)}")
                
                # Store news analysis for next consolidated update (don't send separate notification)
                self._store_news_analysis(news_analysis, news_data)
                
                # Trigger macro analysis if high-impact news
                if impact.lower() in ['high', 'medium'] and sentiment in ['bullish', 'bearish']:
                    self.logger.info("High-impact news detected, triggering macro analysis")
                    await self.macro_sentiment_analysis(news_data)
                    
        except Exception as e:
            self.logger.error(f"News analysis failed: {e}")
            
    def _store_news_analysis(self, analysis: Dict, news_data: List):
        """Store news analysis for inclusion in consolidated updates."""
        try:
            news_summary = {
                'analysis': analysis,
                'articles_count': len(news_data),
                'timestamp': datetime.utcnow().isoformat(),
                'top_headlines': [article.get('title', 'No title')[:100] for article in news_data[:3]]
            }
            
            # Store in data directory for consolidated updates
            news_summary_file = f"{config.DATA_DIR}/latest_news_summary.json"
            with open(news_summary_file, 'w') as f:
                json.dump(news_summary, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error storing news analysis: {e}")
        
    async def hourly_scan(self):
        """Perform anomaly scan with LIVE data only."""
        self.logger.info("🔍 Starting anomaly scan with LIVE data...")
        
        try:
            # Get LIVE market data only
            market_data = await self.get_market_data()
            
            # If NO LIVE DATA, skip scan
            if not market_data:
                self.logger.error("❌ NO LIVE DATA - Skipping anomaly scan")
                return
            
            # Detect pumps and anomalies with LIVE data
            for symbol in config.SYMBOLS[:5]:  # Check top 5 symbols
                if symbol in market_data:
                    anomaly = await self.pump_detector.detect_anomaly(symbol, market_data[symbol])
                    if anomaly:
                        self.logger.info(f"⚠️ LIVE anomaly detected: {anomaly}")
                        
                        # Send anomaly alert to Telegram immediately
                        if self.telegram_notifier:
                            try:
                                await self.telegram_notifier.send_anomaly_alert(anomaly)
                                self.logger.info("📤 Anomaly alert sent to Telegram")
                            except Exception as e:
                                self.logger.error(f"Failed to send anomaly to Telegram: {e}")
                        
                        # Send AI analysis only if available
                        try:
                            ai_analysis = await self.ai_aggregator.get_daily_analysis({symbol: market_data[symbol]})
                            if ai_analysis:
                                signals = ai_analysis.get('signals', [])
                                for signal in signals:
                                    if self.risk_guard.validate_signal(signal):
                                        signal['anomaly_trigger'] = anomaly
                                        self.save_signal(signal)
                        except Exception as e:
                            self.logger.warning(f"AI analysis for anomaly failed: {e}")
                        
                        break  # Only process one anomaly per scan to avoid spam
                            
        except Exception as e:
            self.logger.error(f"LIVE anomaly scan failed: {e}")
            # Send error to Telegram
            if self.telegram_notifier:
                try:
                    await self.telegram_notifier.send_error_notification(str(e), "LIVE Anomaly Scan")
                except:
                    pass

    def calculate_daily_stats(self, signals: List[Dict]) -> Dict:
        """Calculate daily statistics for signals."""
        if not signals:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'wait_signals': 0,
                'avg_confidence': 0
            }
        
        buy_count = sum(1 for s in signals if s.get('action') == 'BUY')
        sell_count = sum(1 for s in signals if s.get('action') == 'SELL')
        wait_count = sum(1 for s in signals if s.get('action') == 'WAIT')
        
        avg_conf = sum(s.get('confidence', 0) for s in signals) / len(signals)
        
        return {
            'total_signals': len(signals),
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'wait_signals': wait_count,
            'avg_confidence': avg_conf
        }

    def combine_signals(self, rule_signals: List, ai_signals: List) -> List:
        """Combine rule-based and AI signals with conflict resolution."""
        combined = {}
        
        # Add rule signals
        for signal in rule_signals:
            symbol = signal.get('symbol')
            combined[symbol] = {
                'symbol': symbol,
                'action': signal.get('action'),
                'confidence': signal.get('confidence', 0),
                'reasoning': signal.get('reasoning', ''),
                'rule_analysis': signal,
                'ai_analysis': {},
                'timestamp': datetime.utcnow().isoformat()
            }
            
        # Merge AI signals
        for signal in ai_signals:
            symbol = signal.get('symbol')
            if symbol in combined:
                # Resolve conflicts between rule and AI signals
                combined[symbol]['ai_analysis'] = signal
                combined[symbol] = self.resolve_signal_conflict(combined[symbol])
            else:
                combined[symbol] = {
                    'symbol': symbol,
                    'action': signal.get('action'),
                    'confidence': signal.get('confidence', 0),
                    'reasoning': signal.get('reasoning', ''),
                    'rule_analysis': {},
                    'ai_analysis': signal,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        return list(combined.values())
        
    def resolve_signal_conflict(self, combined_signal: Dict) -> Dict:
        """Resolve conflicts between rule and AI signals."""
        rule_signal = combined_signal.get('rule_analysis', {})
        ai_signal = combined_signal.get('ai_analysis', {})
        
        rule_action = rule_signal.get('action', 'WAIT')
        ai_action = ai_signal.get('action', 'WAIT')
        rule_confidence = rule_signal.get('confidence', 0)
        ai_confidence = ai_signal.get('confidence', 0)
        
        # If both agree, increase confidence
        if rule_action == ai_action:
            combined_signal['confidence'] = min(0.95, (rule_confidence + ai_confidence) / 2 + 0.2)
            combined_signal['reasoning'] = f"Rule and AI consensus: {rule_signal.get('reasoning', '')}"
        else:
            # If they disagree, use the higher confidence signal but reduce confidence
            if ai_confidence > rule_confidence:
                combined_signal['action'] = ai_action
                combined_signal['confidence'] = max(0.1, ai_confidence - 0.3)
                combined_signal['reasoning'] = f"AI override: {ai_signal.get('reasoning', '')}"
            else:
                combined_signal['action'] = rule_action
                combined_signal['confidence'] = max(0.1, rule_confidence - 0.3)
                combined_signal['reasoning'] = f"Rule override: {rule_signal.get('reasoning', '')}"
                
        return combined_signal

    def save_signal(self, signal: Dict):
        """Save signal to persistent storage."""
        try:
            # Load existing signals
            signals = []
            if os.path.exists(config.SIGNALS_FILE):
                with open(config.SIGNALS_FILE, 'r') as f:
                    signals = json.load(f)
                    
            # Add new signal
            signals.append(signal)
            
            # Keep only the last 100 signals
            if len(signals) > 100:
                signals = signals[-100:]
                
            # Save back to file
            with open(config.SIGNALS_FILE, 'w') as f:
                json.dump(signals, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving signal: {e}")

    def save_macro_analysis(self, analysis: Dict):
        """Save macro analysis results to file."""
        try:
            macro_file = f"{config.DATA_DIR}/macro_analysis.json"
            
            # Load existing analyses
            analyses = []
            if os.path.exists(macro_file):
                with open(macro_file, 'r') as f:
                    analyses = json.load(f)
            
            # Add new analysis
            analyses.append(analysis)
            
            # Keep only the last 50 analyses
            if len(analyses) > 50:
                analyses = analyses[-50:]
            
            # Save back to file
            with open(macro_file, 'w') as f:
                json.dump(analyses, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving macro analysis: {e}")

    async def run_scheduler(self):
        """Enhanced scheduler with LIVE data focus and consolidated notifications."""
        self.running = True
        self.logger.info("🚀 Starting Enhanced Scheduler with LIVE data and consolidated notifications")
        
        # Send startup notification
        if TELEGRAM_AVAILABLE:
            try:
                startup_msg = (
                    "🚀 <b>Crypto AI Analyzer Başlatıldı</b>\n\n"
                    "✅ Sistem aktif\n"
                    "📊 Canlı veri analizi başladı\n"
                    "🔔 2 saatte bir özet rapor gönderilecek\n\n"
                    "<i>Bu bildirimler yatırım tavsiyesi değildir.</i>"
                )
                await self.telegram_notifier.send_message(startup_msg)
            except Exception as e:
                self.logger.error(f"Failed to send startup notification: {e}")
        
        last_hour = -1
        last_telegram_update = datetime.utcnow() - timedelta(hours=3)  # Force first update
        
        try:
            while self.running:
                current_time = datetime.utcnow()
                current_hour = current_time.hour
                current_minute = current_time.minute
                
                # === CONSOLIDATED TELEGRAM UPDATE (Every 2 hours) ===
                time_since_last_update = current_time - last_telegram_update
                
                # Send update every 2 hours or if more than 2 hours have passed
                if (current_minute <= 5 and current_hour % 2 == 0 and current_hour != last_hour) or time_since_last_update.total_seconds() >= 7200:  # 2 hours
                    self.logger.info(f"🕐 Starting 2-hourly consolidated update at {current_hour:02d}:{current_minute:02d} UTC")
                    await self.hourly_telegram_update()
                    last_hour = current_hour
                    last_telegram_update = current_time
                    
                # === DAILY ANALYSIS (08:00 UTC) ===
                if current_hour == 8 and current_minute < 5:
                    await self.daily_analysis()
                    
                # === ANOMALY DETECTION (Every 30 minutes) ===
                if current_minute in [0, 30] and current_minute < 5:
                    await self.hourly_scan()
                    
                # === NEWS ANALYSIS (Every 4 hours) - No separate notifications ===
                if NEWS_API_AVAILABLE and current_hour % 4 == 0 and current_minute < 5:
                    await self.news_based_analysis()
                    
                # === MACRO SENTIMENT (Every 6 hours) - No separate notifications ===
                if current_hour % 6 == 0 and current_minute < 5:
                    await self.macro_sentiment_analysis()
                    
                # Sleep for a minute before next check
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            # Send error to Telegram (only critical errors)
            if self.telegram_notifier:
                try:
                    error_msg = f"🚨 <b>Kritik Sistem Hatası</b>\n\n<code>{str(e)[:150]}...</code>\n\nSistem yeniden başlatılıyor..."
                    await self.telegram_notifier.send_message(error_msg)
                except:
                    pass
        finally:
            await self.shutdown()
            
    async def shutdown(self):
        """Gracefully shutdown the system."""
        self.logger.info("Shutting down crypto analyzer...")
        self.running = False
        
        if self.websocket_client:
            try:
                await self.websocket_client.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting WebSocket: {e}")

    async def get_latest_signals(self) -> str:
        """Get latest trading signals from REAL data."""
        try:
            # Load latest signals from file
            signals_file = os.path.join(config.DATA_DIR, 'signals.json')
            if os.path.exists(signals_file):
                with open(signals_file, 'r') as f:
                    signals_data = json.load(f)
                
                if signals_data and len(signals_data) > 0:
                    # Get last 5 signals
                    latest_signals = signals_data[-5:]
                    
                    message = "🎯 <b>Latest Trading Signals</b>\n\n"
                    for signal in latest_signals:
                        symbol = signal.get('symbol', 'Unknown')
                        action = signal.get('action', 'WAIT')
                        confidence = signal.get('confidence', 0)
                        reason = signal.get('reason', 'No reason provided')
                        
                        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "🟡"
                        message += f"{emoji} <b>{symbol}</b>: {action} ({confidence:.2f})\n"
                        message += f"   📝 {reason}\n\n"
                    
                    return message
            
            return "🎯 <b>Latest Trading Signals</b>\n\n❌ No real signals available at the moment."
            
        except Exception as e:
            return f"🎯 <b>Latest Trading Signals</b>\n\n❌ Error: {str(e)}"

    async def get_market_overview(self) -> str:
        """Get current market overview from REAL data."""
        try:
            # Get current market data
            market_data = await self.get_market_data()
            
            if not market_data:
                return "📈 <b>Current Market Overview</b>\n\n❌ No real market data available at the moment."
            
            # Calculate statistics
            total_symbols = len(market_data)
            positive_changes = sum(1 for data in market_data.values() if data.get('change_24h', 0) > 0)
            negative_changes = sum(1 for data in market_data.values() if data.get('change_24h', 0) < 0)
            
            # Get top gainers and losers
            sorted_by_change = sorted(market_data.items(), key=lambda x: x[1].get('change_24h', 0), reverse=True)
            top_gainers = sorted_by_change[:3]
            top_losers = sorted_by_change[-3:]
            
            message = "📈 <b>Current Market Overview</b>\n\n"
            message += f"📊 <b>Market Summary:</b>\n"
            message += f"• Total Symbols: {total_symbols}\n"
            message += f"• Positive: {positive_changes} 🟢\n"
            message += f"• Negative: {negative_changes} 🔴\n"
            message += f"• Neutral: {total_symbols - positive_changes - negative_changes} 🟡\n\n"
            
            message += "🏆 <b>Top Gainers:</b>\n"
            for symbol, data in top_gainers:
                change = data.get('change_24h', 0) * 100
                price = data.get('price', 0)
                message += f"• {symbol}: ${price:,.2f} (+{change:.2f}%)\n"
            
            message += "\n📉 <b>Top Losers:</b>\n"
            for symbol, data in top_losers:
                change = data.get('change_24h', 0) * 100
                price = data.get('price', 0)
                message += f"• {symbol}: ${price:,.2f} ({change:.2f}%)\n"
            
            return message
            
        except Exception as e:
            return f"📈 <b>Current Market Overview</b>\n\n❌ Error: {str(e)}"

    async def perform_symbol_analysis(self, symbol: str) -> str:
        """Perform detailed analysis for a specific symbol using REAL data."""
        try:
            # Get current market data
            market_data = await self.get_market_data()
            
            if not market_data or symbol not in market_data:
                return f"🧠 <b>Analysis for {symbol}</b>\n\n❌ No real data available for {symbol}."
            
            data = market_data[symbol]
            price = data.get('price', 0)
            change_24h = data.get('change_24h', 0) * 100
            volume = data.get('volume', 0)
            high_24h = data.get('high_24h', 0)
            low_24h = data.get('low_24h', 0)
            source = data.get('source', 'Unknown')
            
            message = f"🧠 <b>Analysis for {symbol}</b>\n\n"
            message += f"💰 <b>Price Data:</b>\n"
            message += f"• Current Price: ${price:,.2f}\n"
            message += f"• 24h Change: {change_24h:+.2f}%\n"
            message += f"• 24h High: ${high_24h:,.2f}\n"
            message += f"• 24h Low: ${low_24h:,.2f}\n"
            message += f"• Volume: {volume:,.0f}\n\n"
            
            message += f"📊 <b>Technical Analysis:</b>\n"
            message += f"• Data Source: {source}\n"
            message += f"• Trend: {'🟢 Bullish' if change_24h > 0 else '🔴 Bearish' if change_24h < 0 else '🟡 Neutral'}\n"
            
            # Add AI analysis if available
            try:
                from llm.aggregator import AIAggregator
                aggregator = AIAggregator()
                analysis = await aggregator.analyze_single_crypto(symbol, data)
                
                if analysis and 'signals' in analysis:
                    signals = analysis['signals']
                    if signals:
                        signal = signals[0]  # Get first signal
                        action = signal.get('action', 'WAIT')
                        confidence = signal.get('confidence', 0)
                        reason = signal.get('reason', 'No AI analysis available')
                        
                        message += f"• AI Signal: {action} ({confidence:.2f})\n"
                        message += f"• AI Reason: {reason}\n"
            except Exception as e:
                message += f"• AI Analysis: Not available ({str(e)})\n"
            
            return message
            
        except Exception as e:
            return f"🧠 <b>Analysis for {symbol}</b>\n\n❌ Error: {str(e)}"

    async def get_performance_stats(self) -> str:
        """Get performance statistics from REAL data."""
        try:
            # Load signals from file
            signals_file = os.path.join(config.DATA_DIR, 'signals.json')
            if os.path.exists(signals_file):
                with open(signals_file, 'r') as f:
                    signals_data = json.load(f)
                
                if signals_data:
                    total_signals = len(signals_data)
                    buy_signals = sum(1 for s in signals_data if s.get('action') == 'BUY')
                    sell_signals = sum(1 for s in signals_data if s.get('action') == 'SELL')
                    wait_signals = sum(1 for s in signals_data if s.get('action') == 'WAIT')
                    
                    avg_confidence = sum(s.get('confidence', 0) for s in signals_data) / total_signals if total_signals > 0 else 0
                    
                    message = "📈 <b>Performance Statistics</b>\n\n"
                    message += f"• Total Signals: {total_signals}\n"
                    message += f"• Buy Signals: {buy_signals} 🟢\n"
                    message += f"• Sell Signals: {sell_signals} 🔴\n"
                    message += f"• Wait Signals: {wait_signals} 🟡\n"
                    message += f"• Average Confidence: {avg_confidence:.2f}\n"
                    
                    return message
            
            return "📈 <b>Performance Statistics</b>\n\n❌ No real performance data available at the moment."
            
        except Exception as e:
            return f"📈 <b>Performance Statistics</b>\n\n❌ Error: {str(e)}"


def run_scheduler_background():
    """Run the scheduler in background thread for Render."""
    global analyzer_instance, analyzer
    
    async def scheduler_main():
        analyzer_instance = CryptoAnalyzer()
        analyzer = analyzer_instance  # Set global instance for telegram bot
        await analyzer_instance.run_scheduler()
    
    # Run in new event loop for background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scheduler_main())

async def main():
    """Main entry point for local development."""
    global analyzer_instance, analyzer
    analyzer_instance = CryptoAnalyzer()
    analyzer = analyzer_instance  # Set global instance for telegram bot
    await analyzer_instance.run_scheduler()

# Render.com entry point
def create_app():
    """Create Flask app for Render deployment."""
    global analyzer_instance
    
    # Start the scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler_background, daemon=True)
    scheduler_thread.start()
    
    # Wait a moment for initialization
    time.sleep(2)
    
    return app

if __name__ == "__main__":
    # Local development
    asyncio.run(main())
else:
    # Render.com deployment
    app = create_app() 
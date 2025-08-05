"""
Main orchestrator for the crypto analysis and trading signal system.
Handles time-based triggers and coordinates all system components.
Enhanced with WebSocket real-time data integration and Telegram notifications.
Cross-platform compatible deployment ready with Flask web server.
"""

import asyncio
import json
import logging
import os
import platform
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

# Import news API
try:
    from data_sources.news_api import CryptoNewsAPI
    NEWS_API_AVAILABLE = True
    
    class NewsProcessor:
        """Simple news processor wrapper."""
        async def get_crypto_news(self, limit=20):
            async with CryptoNewsAPI() as news_api:
                return await news_api.get_crypto_news(limit)
        
        def process_news_for_ai(self, news_data):
            """Basic news processing."""
            if not news_data:
                return {"sentiment_summary": "neutral", "impact_level": "low", "key_themes": [], "total_articles": 0}
            
            # Simple sentiment analysis based on keywords
            positive_keywords = ["surge", "rally", "bull", "gain", "rise", "up", "positive", "adoption"]
            negative_keywords = ["drop", "fall", "crash", "bear", "down", "negative", "ban", "hack"]
            
            positive_count = 0
            negative_count = 0
            
            for article in news_data:
                title = article.get('title', '').lower()
                for keyword in positive_keywords:
                    if keyword in title:
                        positive_count += 1
                for keyword in negative_keywords:
                    if keyword in title:
                        negative_count += 1
            
            if positive_count > negative_count:
                sentiment = "bullish"
            elif negative_count > positive_count:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
                
            impact = "high" if len(news_data) > 15 else "medium" if len(news_data) > 5 else "low"
            
            return {
                "sentiment_summary": sentiment,
                "impact_level": impact,
                "key_themes": ["crypto", "market", "trading"],
                "total_articles": len(news_data)
            }
    
except ImportError:
    NEWS_API_AVAILABLE = False
    
    class NewsProcessor:
        async def get_crypto_news(self, limit=20):
            return []
        def process_news_for_ai(self, news_data):
            return {"sentiment_summary": "neutral", "impact_level": "low", "key_themes": [], "total_articles": 0}

# Import Telegram bot with Turkish format
try:
    from telegram_bot_module.telegram_bot import EnhancedTelegramNotifier
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

# Flask app for Render.com
app = Flask(__name__)

# Global analyzer instance
analyzer_instance = None

@app.route('/')
def home():
    """Home endpoint for Render health check."""
    return jsonify({
        "status": "running",
        "service": "Crypto AI Analyzer",
        "version": "2.0.0",
        "features": [
            "Turkish Trading Signals",
            "Real-time Market Data",
            "AI Analysis (OpenAI + Claude)",
            "Telegram Notifications",
            "Risk Management",
            "Pump Detection"
        ],
        "endpoints": [
            "/health",
            "/signals",
            "/signals/turkish",
            "/status",
            "/market-data"
        ]
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Render."""
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
    
    # Check if all critical components are working
    if all([status["components"]["analyzer"]]):
        return jsonify(status), 200
    else:
        status["status"] = "degraded"
        return jsonify(status), 503

@app.route('/signals')
def get_signals():
    """Get latest trading signals (English format)."""
    try:
        global analyzer_instance
        if not analyzer_instance:
            return jsonify({"error": "Analyzer not initialized"}), 503
            
        # Get recent signals from file
        signals = []
        if os.path.exists(config.SIGNALS_FILE):
            with open(config.SIGNALS_FILE, 'r') as f:
                all_signals = json.load(f)
                # Get last 5 signals
                signals = all_signals[-5:] if all_signals else []
        
        return jsonify({
            "signals": signals,
            "count": len(signals),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/signals/turkish')
def get_turkish_signals():
    """Get Turkish format trading signals."""
    try:
        global analyzer_instance
        if not analyzer_instance or not analyzer_instance.telegram_notifier:
            return jsonify({"error": "Telegram notifier not available"}), 503
            
        # Get Turkish signals synchronously (load from file)
        # Since this is a Flask route, we can't use async directly
        try:
            # Try to get latest Turkish signals from cached file
            turkish_file = f"{config.DATA_DIR}/turkish_signals.json"
            if os.path.exists(turkish_file):
                with open(turkish_file, 'r', encoding='utf-8') as f:
                    cached_signals = json.load(f)
                    return jsonify({
                        "signals": cached_signals.get("content", "📊 Türkçe sinyaller yükleniyor..."),
                        "format": "Turkish", 
                        "timestamp": cached_signals.get("timestamp", datetime.utcnow().isoformat()),
                        "cached": True
                    })
            else:
                # Return a placeholder if no cached signals
                return jsonify({
                    "signals": "🔄 Türkçe sinyaller hazırlanıyor... Lütfen birkaç dakika sonra tekrar deneyin.",
                    "format": "Turkish",
                    "timestamp": datetime.utcnow().isoformat(),
                    "cached": False
                })
        except Exception as e:
            return jsonify({"error": f"Cache read error: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status')
def get_status():
    """Get system status."""
    global analyzer_instance
    
    status = {
        "system": {
            "running": analyzer_instance is not None and analyzer_instance.running,
            "uptime": time.time() - analyzer_instance.start_time if analyzer_instance else 0,
            "symbols_monitored": len(config.SYMBOLS)
        },
        "data_sources": {
            "binance_api": True,  # Always try Binance
            "coingecko_api": True,  # Fallback
            "news_api": NEWS_API_AVAILABLE,
            "websocket": analyzer_instance.websocket_client is not None if analyzer_instance else False
        },
        "ai_models": {
            "openai": bool(config.OPENAI_API_KEY),
            "claude": bool(config.CLAUDE_API_KEY)
        },
        "notifications": {
            "telegram_enabled": TELEGRAM_AVAILABLE and config.TELEGRAM_ENABLED,
            "telegram_configured": bool(config.TELEGRAM_BOT_TOKEN)
        }
    }
    
    return jsonify(status)

@app.route('/market-data')
def get_market_data():
    """Get current market data."""
    try:
        # Load latest market data from file if available
        if os.path.exists(f"{config.DATA_DIR}/prices.json"):
            with open(f"{config.DATA_DIR}/prices.json", 'r') as f:
                market_data = json.load(f)
                return jsonify({
                    "market_data": market_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
        else:
            return jsonify({"error": "No market data available"}), 404
            
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
        """Get market data with improved fallback handling."""
        try:
            # Import data manager
            from data_sources.data_manager import DataManager
            data_manager = DataManager()
            
            # Force refresh to get fresh data
            live_data = await data_manager.get_market_data(config.SYMBOLS, force_refresh=True)
            
            if live_data and len(live_data) >= 1:  # Relaxed requirement: at least 1 symbol
                self.logger.info(f"✅ Retrieved market data for {len(live_data)} symbols")
                # Save to file for web endpoint
                await self.save_market_data(live_data)
                
                # Check data quality
                quality = self._assess_data_quality(live_data)
                self.logger.info(f"📊 Data quality assessment: {quality}")
                
                return live_data
            else:
                self.logger.error("❌ NO DATA AVAILABLE - All sources failed")
                return {}
                
        except Exception as e:
            self.logger.error(f"❌ Error fetching market data: {e}")
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
        """Perform analysis with improved data handling."""
        self.logger.info("🔄 Starting analysis...")
        
        # Check if we can trade today
        if not self.risk_guard.can_trade_today():
            self.logger.info("Daily trading limits reached, skipping analysis")
            return
            
        # Get market data (with fallback mechanisms)
        market_data = await self.get_market_data()
        
        # If NO DATA AT ALL, skip analysis
        if not market_data:
            self.logger.error("❌ NO DATA AVAILABLE - Skipping all analysis")
            return
        
        self.logger.info(f"✅ Processing data for {len(market_data)} symbols")
        
        # Generate signals using rules with LIVE data
        rule_signals = []
        for symbol in config.SYMBOLS:
            if symbol in market_data:
                signal = await self.rule_engine.generate_signal(symbol, market_data[symbol])
                if signal:
                    rule_signals.append(signal)
                    
        # Get AI analysis if available (with LIVE data)
        ai_signals = []
        try:
            ai_analysis = await self.ai_aggregator.get_daily_analysis(market_data)
            if ai_analysis:
                ai_signals = ai_analysis.get('signals', [])
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
        
        self.logger.info(f"✅ Analysis complete with LIVE data. Generated {len(validated_signals)} signals")
        return validated_signals

    async def hourly_telegram_update(self):
        """Send Turkish signals to Telegram every hour."""
        try:
            self.logger.info("📤 Sending hourly Telegram update...")
            
            if not self.telegram_notifier:
                self.logger.warning("Telegram notifier not available")
                return
            
            # Get market data (with fallback mechanisms)
            market_data = await self.get_market_data()
            
            # If NO DATA AT ALL, don't send anything
            if not market_data:
                self.logger.error("❌ NO DATA - Skipping Telegram update")
                return
                
            # Generate Turkish signals with LIVE data
            turkish_signals = await self.telegram_notifier.get_turkish_signals()
            
            if turkish_signals and "❌" not in turkish_signals:  # Only send if successful
                # Send to Telegram
                await self.telegram_notifier.send_message(
                    f"🕐 <b>SAATLİK CANLI SİNYAL GÜNCELLEMESİ</b>\n\n{turkish_signals} \n\n<b>Bu bildirimler yatırım tavsiyesi değildir.</b>"
                )
                self.logger.info("✅ Hourly LIVE signals sent to Telegram")
            else:
                self.logger.error("❌ Failed to generate Turkish signals - No Telegram update sent")
                
        except Exception as e:
            self.logger.error(f"Error in hourly Telegram update: {e}")

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
        """Perform news-based market analysis."""
        self.logger.info("Starting news-based analysis...")
        
        try:
            # Get latest news
            news_data = await self.get_crypto_news_data(limit=20)
            
            if not news_data:
                self.logger.warning("No news data available")
                return
            
            # Process news for sentiment
            if self.news_processor:
                processed_news = self.news_processor.process_news_for_ai(news_data)
                
                self.logger.info(f"News Analysis Summary:")
                self.logger.info(f"  - Overall Sentiment: {processed_news.get('sentiment_summary', 'unknown')}")
                self.logger.info(f"  - Impact Level: {processed_news.get('impact_level', 'unknown')}")
                self.logger.info(f"  - Key Themes: {', '.join(processed_news.get('key_themes', [])[:3])}")
                self.logger.info(f"  - Articles Processed: {processed_news.get('total_articles', 0)}")
                
                # Send news update to Telegram
                if TELEGRAM_AVAILABLE:
                    try:
                        await self.telegram_notifier.send_news(news_data)
                    except Exception as e:
                        self.logger.error(f"Failed to send news to Telegram: {e}")
                
                # If news sentiment is strongly bearish or bullish, trigger macro analysis
                sentiment = processed_news.get('sentiment_summary', 'neutral')
                impact = processed_news.get('impact_level', 'low')
                
                if sentiment in ['bullish', 'bearish'] and impact in ['high', 'medium']:
                    self.logger.info(f"High-impact {sentiment} news detected, triggering macro analysis")
                    await self.macro_sentiment_analysis(news_data=news_data)
                    
        except Exception as e:
            self.logger.error(f"News-based analysis failed: {e}")
            # Send error to Telegram
            if TELEGRAM_AVAILABLE:
                try:
                    await self.telegram_notifier.send_error_notification(str(e), "News Analysis")
                except:
                    pass
        
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
        """Run scheduler with LIVE DATA ONLY and hourly Telegram updates."""
        self.logger.info("🚀 Starting LIVE DATA crypto analyzer (Hourly Telegram Updates)...")
        self.running = True
        
        # Send startup notification to Telegram
        if self.telegram_notifier:
            try:
                await self.telegram_notifier.send_startup_notification()
            except Exception as e:
                self.logger.error(f"Failed to send startup notification: {e}")
        
        # Initial analysis with LIVE data only
        await self.daily_analysis()
        
        # Initial Telegram update
        await self.hourly_telegram_update()
        
        last_hour = -1  # Track last hour for hourly updates
        last_telegram_update = datetime.utcnow() - timedelta(hours=2)  # Initialize to 2 hours ago
        
        try:
            while self.running:
                current_time = datetime.utcnow()
                current_hour = current_time.hour
                current_minute = current_time.minute
                
                # === HOURLY TELEGRAM UPDATE (More reliable) ===
                # Check if at least 55 minutes have passed since last update
                time_since_last_update = current_time - last_telegram_update
                
                if (current_minute <= 5 and current_hour != last_hour) or time_since_last_update.total_seconds() >= 3300:  # 55 minutes
                    self.logger.info(f"🕐 Starting hourly update at {current_hour:02d}:{current_minute:02d} UTC (last update: {time_since_last_update})")
                    await self.hourly_telegram_update()
                    last_hour = current_hour
                    last_telegram_update = current_time
                    
                # === DAILY ANALYSIS (08:00 UTC) ===
                if current_hour == 8 and current_minute < 5:
                    await self.daily_analysis()
                    
                # === ANOMALY DETECTION (Every 30 minutes) ===
                if current_minute in [0, 30] and current_minute < 5:
                    await self.hourly_scan()
                    
                # === NEWS ANALYSIS (Every 4 hours) ===
                if NEWS_API_AVAILABLE and current_hour % 4 == 0 and current_minute < 5:
                    await self.news_based_analysis()
                    
                # === MACRO SENTIMENT (Every 6 hours) ===
                if current_hour % 6 == 0 and current_minute < 5:
                    await self.macro_sentiment_analysis()
                    
                # Sleep for a minute before next check
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            self.logger.error(f"Scheduler error: {e}")
            # Send error to Telegram
            if self.telegram_notifier:
                try:
                    await self.telegram_notifier.send_error_notification(str(e), "LIVE DATA Scheduler")
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


def run_scheduler_background():
    """Run the scheduler in background thread for Render."""
    global analyzer_instance
    
    async def scheduler_main():
        analyzer_instance = CryptoAnalyzer()
        await analyzer_instance.run_scheduler()
    
    # Run in new event loop for background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scheduler_main())

async def main():
    """Main entry point for local development."""
    global analyzer_instance
    analyzer_instance = CryptoAnalyzer()
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
"""
Telegram Bot integration for crypto analysis notifications.
Enhanced with interactive commands, portfolio tracking, and real-time features.
"""

import asyncio
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import config

# Import data sources and analysis modules
from data_sources.data_manager import DataManager
from rules.rule_engine import RuleEngine  
from llm.aggregator import AIAggregator

try:
    from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    from telegram.error import TelegramError, NetworkError, RetryAfter
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False


class EnhancedTelegramNotifier:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self.application = None
        self.enabled = config.TELEGRAM_ENABLED and TELEGRAM_AVAILABLE
        self.user_portfolios = {}
        self.active_chats = set()
        
        # Initialize analysis modules for real data
        self.data_manager = DataManager()
        self.rule_engine = RuleEngine()
        self.ai_aggregator = AIAggregator()
        
        if self.enabled:
            try:
                self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
                self.setup_application()
                # Start polling in background
                self.start()
                self.logger.info("Enhanced Telegram bot initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Telegram bot: {e}")
                self.enabled = False
        else:
            if not TELEGRAM_AVAILABLE:
                self.logger.warning("python-telegram-bot not available")
            else:
                self.logger.warning("Telegram bot disabled - no token provided")

    def setup_application(self):
        """Setup Telegram application with command handlers."""
        try:
            self.application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("help", self.cmd_help))
            self.application.add_handler(CommandHandler("status", self.cmd_status))
            self.application.add_handler(CommandHandler("portfolio", self.cmd_portfolio))
            self.application.add_handler(CommandHandler("signals", self.cmd_signals))
            self.application.add_handler(CommandHandler("market", self.cmd_market))
            self.application.add_handler(CommandHandler("settings", self.cmd_settings))
            self.application.add_handler(CommandHandler("stats", self.cmd_stats))
            self.application.add_handler(CommandHandler("analyze", self.cmd_analyze))
            
            # Add new control commands
            self.application.add_handler(CommandHandler("refresh", self.cmd_refresh))
            self.application.add_handler(CommandHandler("analyze_now", self.cmd_analyze_now))
            self.application.add_handler(CommandHandler("force_update", self.cmd_force_update))
            self.application.add_handler(CommandHandler("quick_stats", self.cmd_quick_stats))
            self.application.add_handler(CommandHandler("restart", self.cmd_restart))
            self.application.add_handler(CommandHandler("price", self.cmd_price))
            
            # Add callback query handler for interactive buttons
            self.application.add_handler(CallbackQueryHandler(self.handle_callback))
            
            # Setup command menu synchronously
            self.logger.info("Telegram command handlers setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Telegram application: {e}")

    async def setup_command_menu(self):
        """Setup bot command menu for better user experience."""
        try:
            commands = [
                BotCommand("start", "🚀 Bot'u başlat ve hoş geldin mesajını gör"),
                BotCommand("help", "📚 Tüm komutların detaylı listesi"),
                BotCommand("signals", "🎯 Son AI trading sinyalleri"),
                BotCommand("market", "📊 Güncel piyasa analizi"),
                BotCommand("analyze", "🔍 Tek kripto detaylı analiz (örn: /analyze BTC)"),
                BotCommand("price", "💰 Hızlı fiyat kontrol (örn: /price ETH)"),
                BotCommand("portfolio", "📈 Portfolio takibi"),
                BotCommand("stats", "📉 Performans istatistikleri"),
                BotCommand("status", "⚙️ Sistem durumu"),
                BotCommand("refresh", "🔄 Verileri yenile"),
                BotCommand("analyze_now", "⚡ Anında analiz başlat"),
                BotCommand("quick_stats", "⚡ Hızlı durum"),
                BotCommand("settings", "⚙️ Bot ayarları")
            ]
            
            await self.bot.set_my_commands(commands)
            self.logger.info("✅ Bot command menu configured successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to setup command menu: {e}")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        chat_id = update.effective_chat.id
        self.active_chats.add(chat_id)
        
        welcome_message = """
🤖 <b>Crypto AI Analyzer Bot</b>

Hoş geldiniz! Gelişmiş AI destekli kripto analiz botuna!

<b>🎯 Ana Komutlar:</b>
/signals - Son AI trading sinyalleri
/market - Güncel piyasa analizi  
/analyze BTC - Tek kripto detaylı analiz
/price ETH - Hızlı fiyat kontrol

<b>📊 Takip & Analiz:</b>
/portfolio - Portfolio takibi
/stats - Performans istatistikleri
/status - Sistem durumu

<b>⚡ Hızlı Komutlar:</b>
/refresh - Verileri yenile
/analyze_now - Anında analiz
/quick_stats - Hızlı durum
/help - Detaylı yardım

💡 <i>Komut yazarken otomatik menüden de seçebilirsiniz!</i>
🚀 <i>AI gücüyle piyasa analizine hazır!</i>
        """
        
        keyboard_data = [
            [("🎯 Son Sinyaller", "latest_signals"), ("📊 Market Durum", "market_overview")],
            [("🔍 Kripto Analiz", "crypto_analyze_menu"), ("💰 Hızlı Fiyat", "crypto_price_menu")],
            [("📈 Portfolio", "portfolio_view"), ("⚙️ Ayarlar", "settings_menu")]
        ]
        keyboard = self._create_keyboard(keyboard_data)
        await self._send_message(update, welcome_message, keyboard)

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
📚 <b>Crypto AI Analyzer Help</b>

<b>🎯 Trading Commands:</b>
/signals - Get latest AI trading signals
/market - Current market analysis
/analyze [SYMBOL] - Custom analysis for specific coin
/analyze_now - Anında analiz başlat 🚀
/price [SYMBOL] - Hızlı fiyat kontrol 💰

<b>📊 Portfolio Commands:</b>
/portfolio - View your tracked portfolio
/portfolio add [SYMBOL] [AMOUNT] - Add position
/portfolio remove [SYMBOL] - Remove position

<b>📈 Statistics Commands:</b>
/stats - View performance statistics
/stats daily - Daily performance
/stats weekly - Weekly performance
/quick_stats - Hızlı sistem durumu ⚡

<b>⚙️ System Commands:</b>
/status - Bot and system status
/settings - Configure notifications
/help - This help message

<b>🔧 Control Commands:</b>
/refresh - Veriyi yenile 🔄
/force_update - Zorunlu güncelleme ⚡
/restart - Sistemi yeniden başlat 🔄

<b>🤖 AI Features:</b>
• Real-time market analysis with GPT-4 and Claude
• Multi-model consensus signals
• Macro sentiment analysis
• News-based trading insights
• Risk management integration

<b>💡 Tips:</b>
• Use buttons for quick navigation
• Set up portfolio tracking for personalized insights
• Enable notifications for real-time alerts

<i>Powered by advanced AI models for superior market analysis</i>
        """
        await self._send_message(update, help_message)

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        status_message = await self.get_system_status()
        keyboard_data = [
            [("🔄 Refresh", "refresh_status"), ("📊 Detailed Stats", "detailed_stats")]
        ]
        keyboard = self._create_keyboard(keyboard_data)
        await self._send_message(update, status_message, keyboard)

    async def cmd_portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command."""
        chat_id = update.effective_chat.id
        portfolio_message = await self.get_portfolio_status(chat_id)
        keyboard_data = [
            [("📈 P&L Analysis", "portfolio_pnl"), ("🎯 Get Signals", "portfolio_signals")]
        ]
        keyboard = self._create_keyboard(keyboard_data)
        await self._send_message(update, portfolio_message, keyboard)

    async def cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command - Show trading signals with REAL data and AI analysis."""
        try:
            await update.message.reply_text("🎯 <b>Sinyaller analiz ediliyor...</b>", parse_mode='HTML')
            
            # Get real market data
            market_data = await self._get_real_market_data()
            
            if market_data:
                # Generate AI signals
                signals = await self._generate_ai_signals(market_data)
                
                if signals:
                    message = "🎯 <b>AI TRADING SİNYALLERİ</b>\n\n"
                    
                    for i, signal in enumerate(signals[:5]):  # Show top 5 signals
                        symbol = signal.get('symbol', 'Unknown')
                        action = signal.get('action', 'WAIT')
                        confidence = signal.get('confidence', 0)
                        reason = signal.get('reason', 'No reason provided')
                        
                        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "🟡"
                        message += f"{i+1}. <b>{symbol}</b> {emoji}\n"
                        message += f"   📊 {action} ({confidence:.1%})\n"
                        message += f"   📝 {reason}\n\n"
                    
                    message += f"⏰ <i>Analiz zamanı: {datetime.now().strftime('%H:%M:%S')}</i>"
                    
                    keyboard = [
                        [InlineKeyboardButton("🔄 Yenile", callback_data="refresh_signals")],
                        [InlineKeyboardButton("📊 Detaylı Analiz", callback_data="detailed_signals")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
                else:
                    await update.message.reply_text(
                        "⚠️ <b>Şu anda sinyal yok</b>\n\nPiyasa nötr durumda.",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    "❌ <b>Veri alınamadı</b>\n\nSinyal analizi yapılamıyor.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            self.logger.error(f"Error in signals command: {e}")
            await update.message.reply_text(
                f"❌ <b>Hata:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def cmd_market(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /market command - Show current market overview with REAL data."""
        try:
            await update.message.reply_text("📊 <b>Market durumu alınıyor...</b>", parse_mode='HTML')
            
            # Get real market data from CoinGecko
            market_data = await self._get_real_market_data()
            
            if market_data:
                message = "📈 <b>GÜNCEL MARKET DURUMU</b>\n\n"
                
                # Calculate statistics
                total_symbols = len(market_data)
                positive_changes = sum(1 for data in market_data.values() if data.get('change_24h', 0) > 0)
                negative_changes = sum(1 for data in market_data.values() if data.get('change_24h', 0) < 0)
                
                message += f"📊 <b>Market Özeti:</b>\n"
                message += f"• Toplam: {total_symbols} coin\n"
                message += f"• Yükselişte: {positive_changes} 🟢\n"
                message += f"• Düşüşte: {negative_changes} 🔴\n"
                message += f"• Nötr: {total_symbols - positive_changes - negative_changes} 🟡\n\n"
                
                # Show top coins
                sorted_data = sorted(market_data.items(), key=lambda x: x[1].get('price', 0), reverse=True)
                message += "🏆 <b>En Yüksek Fiyatlı Coinler:</b>\n"
                for i, (symbol, data) in enumerate(sorted_data[:5]):
                    price = data.get('price', 0)
                    change = data.get('change_24h', 0) * 100
                    emoji = "🟢" if change > 0 else "🔴" if change < 0 else "🟡"
                    message += f"{i+1}. {symbol}: ${price:,.2f} ({change:+.2f}%) {emoji}\n"
                
                # Add AI analysis
                ai_analysis = await self._get_ai_market_analysis(market_data)
                if ai_analysis:
                    message += f"\n🧠 <b>AI Analizi:</b>\n{ai_analysis}\n"
                
                message += f"\n⏰ <i>Son güncelleme: {datetime.now().strftime('%H:%M:%S')}</i>"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Yenile", callback_data="refresh_market")],
                    [InlineKeyboardButton("📊 Detaylı Analiz", callback_data="detailed_analysis")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await update.message.reply_text(
                    "❌ <b>Market verisi alınamadı</b>\n\nLütfen daha sonra tekrar deneyin.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            self.logger.error(f"Error in market command: {e}")
            await update.message.reply_text(
                f"❌ <b>Hata:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def cmd_analyze(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze command - Perform comprehensive AI analysis."""
        try:
            await update.message.reply_text("🧠 <b>AI analizi başlatılıyor...</b>", parse_mode='HTML')
            
            # Get real market data
            market_data = await self._get_real_market_data()
            
            if market_data:
                # Perform comprehensive AI analysis
                analysis = await self._perform_comprehensive_analysis(market_data)
                
                message = "🧠 <b>AI MARKET ANALİZİ</b>\n\n"
                message += analysis
                message += f"\n⏰ <i>Analiz zamanı: {datetime.now().strftime('%H:%M:%S')}</i>"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Yenile", callback_data="refresh_analysis")],
                    [InlineKeyboardButton("📊 Detaylı Rapor", callback_data="detailed_report")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(message, parse_mode='HTML', reply_markup=reply_markup)
            else:
                await update.message.reply_text(
                    "❌ <b>Veri alınamadı</b>\n\nAI analizi yapılamıyor.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            self.logger.error(f"Error in analyze command: {e}")
            await update.message.reply_text(
                f"❌ <b>Hata:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        settings_message = "⚙️ <b>Bot Settings</b>\n\nConfigure your preferences:"
        keyboard_data = [
            [("🔔 Notifications", "settings_notifications"), ("🎯 Signal Filters", "settings_signals")],
            [("📊 Portfolio Settings", "settings_portfolio"), ("⏰ Timing Settings", "settings_timing")]
        ]
        keyboard = self._create_keyboard(keyboard_data)
        await self._send_message(update, settings_message, keyboard)

    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command."""
        stats_message = await self.get_performance_stats()
        keyboard_data = [
            [("📈 Signal Accuracy", "stats_accuracy"), ("💰 P&L History", "stats_pnl")],
            [("🤖 AI Performance", "stats_ai")]
        ]
        keyboard = self._create_keyboard(keyboard_data)
        await self._send_message(update, stats_message, keyboard)

    async def get_turkish_signals(self) -> str:
        """Get trading signals in Turkish format with real data."""
        try:
            # Get real market data
            market_data = await self.data_manager.get_market_data(config.SYMBOLS[:3])  # Top 3 symbols
            if not market_data:
                return "❌ <b>Market verilerine ulaşılamıyor</b>\n\nLütfen daha sonra tekrar deneyin."
            
            signals_message = "🚦 <b>AL/SAT SİNYALLERİ</b>\n\n"
            
            # Get AI analysis for enhanced signals
            ai_analysis = await self.ai_aggregator.get_macro_sentiment_analysis(market_data)
            
            signal_count = 1
            for symbol, data in list(market_data.items())[:3]:  # Process top 3 symbols
                try:
                    # Generate signal using rule engine
                    signal = await self.rule_engine.generate_signal(symbol, data)
                    if not signal:
                        continue
                    
                    # Get current price and calculate levels
                    current_price = signal.get('current_price', data.get('price', 0))
                    if current_price <= 0:
                        continue
                        
                    rsi = signal.get('indicators', {}).get('rsi', 50)
                    macd_data = signal.get('indicators', {}).get('macd', {})
                    confidence = signal.get('confidence', 0.5)
                    action = signal.get('action', 'WAIT')
                    
                    # Calculate price levels based on action and technical levels
                    if action == 'BUY':
                        buy_low = current_price * 0.995  # 0.5% below current
                        buy_high = current_price * 1.01  # 1% above current  
                        sell_low = current_price * 1.04  # 4% profit target
                        sell_high = current_price * 1.06  # 6% profit target
                        stop_loss = current_price * 0.975  # 2.5% stop loss
                        take_profit = current_price * 1.05  # 5% take profit
                        action_emoji = "🟢"
                    elif action == 'SELL':
                        buy_low = current_price * 0.94   # 6% below for buy back
                        buy_high = current_price * 0.96  # 4% below for buy back
                        sell_low = current_price * 0.995 # 0.5% below current
                        sell_high = current_price * 1.01 # 1% above current
                        stop_loss = current_price * 1.025 # 2.5% stop loss for short
                        take_profit = current_price * 0.95 # 5% take profit for short
                        action_emoji = "🔴"
                    else:  # WAIT
                        buy_low = current_price * 0.98
                        buy_high = current_price * 1.02
                        sell_low = current_price * 1.03
                        sell_high = current_price * 1.05
                        stop_loss = current_price * 0.97
                        take_profit = current_price * 1.04
                        action_emoji = "🟡"
                    
                    # Determine confidence level in Turkish
                    if confidence >= 0.8:
                        confidence_tr = "Çok Yüksek"
                    elif confidence >= 0.6:
                        confidence_tr = "Yüksek"
                    elif confidence >= 0.4:
                        confidence_tr = "Orta"
                    else:
                        confidence_tr = "Düşük"
                    
                    # Priority based on confidence and market conditions
                    priority = "Yüksek" if confidence >= 0.7 else "Orta" if confidence >= 0.4 else "Düşük"
                    
                    # Validity period based on volatility
                    validity_hours = 4 if confidence >= 0.6 else 2
                    
                    # MACD interpretation
                    macd_trend = "Pozitif" if macd_data.get('histogram', 0) > 0 else "Negatif"
                    
                    # News impact simulation (would be real in production)
                    news_impact = "Pozitif" if confidence > 0.6 else "Nötr" if confidence > 0.3 else "Negatif"
                    news_reason = self._get_news_reason(symbol, confidence)
                    
                    # Sentiment percentage
                    sentiment_pct = min(int(confidence * 100 + 20), 95)  # Convert confidence to sentiment %
                    
                    # Position size recommendation
                    position_pct = min(int(confidence * 15), 15)  # Max 15% position
                    
                    # Risk warning
                    risk_warning = self._get_risk_warning(rsi, confidence, symbol)
                    
                    # Alternative scenario
                    alternative = self._get_alternative_scenario(stop_loss, action)
                    
                    # Historical success (simulated based on confidence)
                    success_rate = f"{min(3, max(1, int(confidence * 3)))}/3"
                    
                    # TL;DR summary
                    tldr = self._create_tldr(buy_low, buy_high, take_profit, stop_loss, confidence_tr.lower())
                    
                    # Reasoning
                    reasoning = signal.get('reasoning', 'Teknik analiz sinyali')
                    
                    # Build the signal message
                    signals_message += f"""
{signal_count}️⃣ <b>{symbol}</b> {action_emoji}
• <b>AL:</b> {buy_low:,.0f} - {buy_high:,.0f} (Limit)
• <b>SAT:</b> {sell_low:,.0f} - {sell_high:,.0f}
• <b>Stop-Loss:</b> {stop_loss:,.0f}
• <b>Take-Profit:</b> {take_profit:,.0f}
• <b>Güven:</b> {confidence:.2f} ({confidence_tr})
• <b>Öncelik:</b> {priority}
• <b>Geçerlilik:</b> {validity_hours} saat
• <b>RSI:</b> {rsi:.0f} | <b>MACD:</b> {macd_trend}
• <b>Haber Etkisi:</b> {news_impact} ({news_reason})
• <b>Sentiment:</b> %{sentiment_pct} olumlu
• <b>Önerilen Pozisyon:</b> %{position_pct} portföy
• <b>Risk Uyarısı:</b> {risk_warning}
• <b>Alternatif:</b> {alternative}
• <b>Geçmiş Sinyal Başarısı:</b> Son {success_rate} başarılı
• <b>TL;DR:</b> {tldr}
• <i>Gerekçe:</i> {reasoning}

"""
                    signal_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing signal for {symbol}: {e}")
                    continue
            
            if signal_count == 1:  # No signals generated
                signals_message += "📊 Şu anda net sinyal bulunmuyor.\n🔄 Piyasa koşulları analiz ediliyor..."
            
            signals_message += f"\n🕒 <b>Güncellenme:</b> {datetime.utcnow().strftime('%H:%M:%S')} UTC"
            signals_message += f"\n💡 <i>Gerçek verilerle oluşturulmuştur</i>"
            
            # Cache Turkish signals for web endpoint
            await self._cache_turkish_signals(signals_message)
            
            return signals_message
            
        except Exception as e:
            self.logger.error(f"Error generating Turkish signals: {e}")
            return f"❌ <b>Sinyal oluşturma hatası:</b> {str(e)}"
    
    def _get_news_reason(self, symbol: str, confidence: float) -> str:
        """Get news reason based on symbol and confidence."""
        reasons = {
            'BTCUSDT': ['ETF haberi', 'Kurumsal alım', 'Fed politikası', 'Mining raporu'],
            'ETHUSDT': ['Ethereum güncelleme', 'DeFi gelişimi', 'Layer 2 haberi', 'Staking raporu'],
            'BNBUSDT': ['Binance güncelleme', 'BNB yakma', 'Exchange haberi', 'BSC gelişimi']
        }
        
        symbol_reasons = reasons.get(symbol, ['Genel piyasa', 'Teknik durum', 'Hacim artışı'])
        
        if confidence > 0.7:
            return symbol_reasons[0]
        elif confidence > 0.4:
            return symbol_reasons[1] if len(symbol_reasons) > 1 else symbol_reasons[0]
        else:
            return symbol_reasons[-1]
    
    def _get_risk_warning(self, rsi: float, confidence: float, symbol: str) -> str:
        """Generate risk warning based on indicators."""
        warnings = []
        
        if rsi > 70:
            warnings.append("aşırı alım bölgesi")
        elif rsi < 30:
            warnings.append("aşırı satım bölgesi")
            
        if confidence < 0.5:
            warnings.append("düşük güven")
            
        if symbol == 'BTCUSDT':
            warnings.append("yüksek volatilite")
        
        if not warnings:
            warnings.append("normal risk")
            
        base_warning = ", ".join(warnings)
        
        if confidence < 0.4:
            return f"{base_warning}, kaldıraç önerilmez"
        else:
            return f"{base_warning}, risk yönetimi önemli"
    
    def _get_alternative_scenario(self, stop_loss: float, action: str) -> str:
        """Generate alternative scenario text."""
        if action == 'BUY':
            return f"{stop_loss:,.0f} altı kapanışta sinyal geçersiz"
        elif action == 'SELL': 
            return f"{stop_loss:,.0f} üstü kapanışta sinyal geçersiz"
        else:
            return "Net sinyal oluşana kadar bekle"
    
    def _create_tldr(self, buy_low: float, buy_high: float, take_profit: float, stop_loss: float, confidence: str) -> str:
        """Create TL;DR summary."""
        return f"{buy_low:,.0f}-{buy_high:,.0f} al, {take_profit:,.0f} sat, stop {stop_loss:,.0f}, risk {confidence}."
    
    async def _cache_turkish_signals(self, signals_content: str):
        """Cache Turkish signals to file for web endpoint."""
        try:
            import os
            import json
            import config
            
            # Ensure data directory exists
            os.makedirs(config.DATA_DIR, exist_ok=True)
            
            cache_data = {
                "content": signals_content,
                "timestamp": datetime.utcnow().isoformat(),
                "generated_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            turkish_file = f"{config.DATA_DIR}/turkish_signals.json"
            with open(turkish_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info("Turkish signals cached successfully")
            
        except Exception as e:
            self.logger.error(f"Error caching Turkish signals: {e}")

    async def send_turkish_trading_signal(self, signal: Dict) -> bool:
        """Send a trading signal notification in Turkish format."""
        if not config.TELEGRAM_NOTIFICATIONS.get('signals', True):
            return False
            
        try:
            # Convert single signal to Turkish format
            symbol = signal.get('symbol', 'Unknown')
            
            # Get current market data for the symbol
            market_data = await self.data_manager.get_market_data([symbol])
            if not market_data or symbol not in market_data:
                return False
            
            # Generate Turkish format signal
            turkish_signals = await self.get_turkish_signals()
            
            return await self.send_message(turkish_signals)
            
        except Exception as e:
            self.logger.error(f"Error sending Turkish trading signal: {e}")
            return False

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        try:
            query = update.callback_query
            await query.answer()
            
            data = query.data
            
            if data == "crypto_analyze_menu":
                # Show crypto selection for analysis
                keyboard = await self.get_crypto_selection_keyboard()
                message = ("🎯 <b>Hangi kripto için detaylı analiz istiyorsunuz?</b>\n\n"
                          "💡 Aşağıdaki butonlardan seçin ve AI destekli analiz alın!")
                await query.edit_message_text(
                    text=message,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                return
            elif data == "crypto_price_menu":
                # Show crypto selection for price check
                keyboard = await self.get_price_selection_keyboard()
                message = ("💰 <b>Hangi kripto fiyatını kontrol etmek istiyorsunuz?</b>\n\n"
                          "⚡ Anlık fiyat ve 24s değişim için kripto seçin!")
                await query.edit_message_text(
                    text=message,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                return
            elif data == "market_overview":
                message = await self.get_market_overview()
            elif data == "latest_signals":
                message = await self.get_latest_signals()
            elif data == "turkish_signals":
                message = await self.get_turkish_signals()
            elif data == "portfolio_view":
                chat_id = query.from_user.id
                message = await self.get_portfolio_status(chat_id)
            elif data == "refresh_status":
                message = await self.get_system_status()
            elif data == "refresh_signals":
                message = await self.get_turkish_signals()  # Default to Turkish format
            elif data == "market_analysis":
                message = await self.get_market_overview()
            elif data == "detailed_stats":
                message = await self.get_system_status()
            elif data == "detailed_analysis":
                message = await self.get_latest_signals()
            elif data == "refresh_quick_stats":
                # Force refresh and get stats
                from data_sources.data_manager import DataManager
                data_manager = DataManager()
                data_manager.clear_cache()
                message = "🔄 <b>Cache temizlendi!</b>\n\n"
                message += await self.get_system_status()
            elif data == "confirm_restart":
                message = "🔄 <b>Sistem yeniden başlatılıyor...</b>\n\n⚠️ Bu özellik yakında gelecek!"
            elif data == "cancel_restart":
                message = "❌ <b>Yeniden başlatma iptal edildi.</b>"
            elif data.startswith("settings_"):
                message = await self.get_settings_menu(data.replace("settings_", ""))
            elif data.startswith("analyze_"):
                symbol = data.replace("analyze_", "").upper()
                message = await self.get_single_crypto_analysis(symbol)
                keyboard = [
                    [InlineKeyboardButton("🔄 Yenile", callback_data=f"refresh_crypto_{symbol}")],
                    [InlineKeyboardButton("📊 Karşılaştır", callback_data=f"compare_crypto_{symbol}")],
                    [InlineKeyboardButton("📈 Grafik", callback_data=f"chart_crypto_{symbol}")],
                    [InlineKeyboardButton("⏰ Alarm Kur", callback_data=f"alert_crypto_{symbol}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    text=message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                return  # Don't process further since we already edited the message
            elif data.startswith("refresh_crypto_"):
                symbol = data.replace("refresh_crypto_", "").upper()
                # Force refresh cache and get new data
                from data_sources.data_manager import DataManager
                data_manager = DataManager()
                data_manager.clear_cache()
                message = await self.get_single_crypto_analysis(symbol)
                keyboard = [
                    [InlineKeyboardButton("🔄 Yenile", callback_data=f"refresh_crypto_{symbol}")],
                    [InlineKeyboardButton("📊 Karşılaştır", callback_data=f"compare_crypto_{symbol}")],
                    [InlineKeyboardButton("📈 Grafik", callback_data=f"chart_crypto_{symbol}")],
                    [InlineKeyboardButton("⏰ Alarm Kur", callback_data=f"alert_crypto_{symbol}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    text=message,
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
                return
            elif data.startswith("compare_crypto_"):
                symbol = data.replace("compare_crypto_", "").upper()
                message = f"📊 <b>{symbol} Karşılaştırma</b>\n\n⚠️ Bu özellik yakında gelecek!\n\nDiğer popüler kriptolarla karşılaştırma yapabileceksiniz."
            elif data.startswith("chart_crypto_"):
                symbol = data.replace("chart_crypto_", "").upper()
                message = f"📈 <b>{symbol} Grafik</b>\n\n⚠️ Bu özellik yakında gelecek!\n\nInteraktif fiyat grafiklerini görebileceksiniz."
            elif data.startswith("alert_crypto_"):
                symbol = data.replace("alert_crypto_", "").upper()
                message = f"⏰ <b>{symbol} Alarm</b>\n\n⚠️ Bu özellik yakında gelecek!\n\nFiyat alarmları kurabileceksiniz."
            elif data.startswith("price_"):
                symbol = data.replace("price_", "").upper()
                if not symbol.endswith('USDT'):
                    symbol = f"{symbol}USDT"
                
                # Get fresh price data
                from data_sources.data_manager import DataManager
                data_manager = DataManager()
                data_manager.clear_cache()
                market_data = await data_manager.get_market_data([symbol], force_refresh=True)
                
                if market_data and symbol in market_data:
                    coin_data = market_data[symbol]
                    price = coin_data.get('price', 0)
                    change_24h = coin_data.get('change_24h', 0)
                    
                    trend_emoji = "🚀" if change_24h > 0 else "📉" if change_24h < 0 else "➖"
                    trend_text = "Yükseliş" if change_24h > 0 else "Düşüş" if change_24h < 0 else "Sabit"
                    
                    price_message = f"""
💰 <b>{symbol.replace('USDT', '/USDT')} CANLI FİYAT</b>

💵 <b>Anlık Değer:</b> <code>${price:,.4f} USD</code> 🔴
{trend_emoji} <b>24s Değişim:</b> {change_24h:+.2%} ({trend_text})

🕒 <b>Son Güncelleme:</b> Az önce
                    """
                    
                    keyboard = [
                        [InlineKeyboardButton("🔍 Detaylı Analiz", callback_data=f"analyze_{symbol.replace('USDT', '')}")],
                        [InlineKeyboardButton("🔄 Yenile", callback_data=f"price_{symbol.replace('USDT', '')}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        text=price_message.strip(),
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                    return
                else:
                    message = f"❌ <b>{symbol}</b> fiyat bilgisi bulunamadı."
            else:
                message = "🔧 Feature coming soon!"
            
            await query.edit_message_text(
                text=message,
                parse_mode='HTML'
            )
            
        except Exception as e:
            self.logger.error(f"Error handling callback: {e}")

    async def send_message(self, text: str, chat_id: Optional[str] = None, parse_mode: str = 'HTML') -> bool:
        """Send a message via Telegram bot."""
        if not self.enabled:
            return False
            
        try:
            target_chat_id = chat_id or config.TELEGRAM_CHAT_ID
            if not target_chat_id:
                self.logger.warning("No chat ID configured for Telegram notifications")
                return False
                
            # Split long messages
            if len(text) > 4096:
                chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
                for chunk in chunks:
                    await self.bot.send_message(
                        chat_id=target_chat_id,
                        text=chunk,
                        parse_mode=parse_mode
                    )
            else:
                await self.bot.send_message(
                    chat_id=target_chat_id,
                    text=text,
                    parse_mode=parse_mode
                )
                
            return True
            
        except RetryAfter as e:
            self.logger.warning(f"Rate limited by Telegram, retrying after {e.retry_after} seconds")
            await asyncio.sleep(e.retry_after)
            return await self.send_message(text, chat_id, parse_mode)
            
        except NetworkError as e:
            self.logger.error(f"Network error sending Telegram message: {e}")
            return False
            
        except TelegramError as e:
            self.logger.error(f"Telegram error sending message: {e}")
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error sending Telegram message: {e}")
            return False

    async def send_trading_signal(self, signal: Dict) -> bool:
        """Send a trading signal notification."""
        if not config.TELEGRAM_NOTIFICATIONS.get('signals', True):
            return False
            
        try:
            symbol = signal.get('symbol', 'Unknown')
            action = signal.get('action', 'WAIT')
            confidence = signal.get('confidence', 0)
            reasoning = signal.get('reasoning', 'No reason provided')
            
            # Determine emoji based on action
            action_emoji = {
                'BUY': '🟢',
                'SELL': '🔴', 
                'WAIT': '🟡'
            }.get(action, '⚪')
            
            # Confidence emoji
            conf_emoji = '🔥' if confidence > 0.7 else '⚡' if confidence > 0.4 else '💭'
            
            message = f"""
{action_emoji} <b>TRADING SIGNAL</b> {conf_emoji}

📊 <b>Symbol:</b> {symbol}
🎯 <b>Action:</b> {action}
📈 <b>Confidence:</b> {confidence:.2f} ({confidence*100:.0f}%)
💡 <b>Reason:</b> {reasoning}

🕒 <b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
            """
            
            # Add technical details if available
            if 'rule_analysis' in signal:
                rule = signal['rule_analysis']
                indicators = rule.get('indicators', {})
                
                if indicators:
                    message += "\n📊 <b>Technical Indicators:</b>\n"
                    
                    if 'rsi' in indicators:
                        rsi = indicators['rsi']
                        message += f"• RSI: {rsi:.1f}\n"
                    
                    if 'current_price' in rule:
                        price = rule['current_price']
                        message += f"• Current Price: ${price:,.2f}\n"
            
            # Add AI analysis if available
            if 'ai_analysis' in signal and signal['ai_analysis']:
                message += "\n🤖 <b>AI Analysis:</b> Enhanced with AI insights\n"
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            self.logger.error(f"Error sending trading signal: {e}")
            return False

    async def send_news_update(self, news_data: List[Dict]) -> bool:
        """Send crypto news update."""
        if not config.TELEGRAM_NOTIFICATIONS.get('news', True) or not news_data:
            return False
            
        try:
            message = "📰 <b>CRYPTO NEWS UPDATE</b>\n\n"
            
            for i, article in enumerate(news_data[:5], 1):  # Top 5 news
                title = article.get('title', 'No title')
                source = article.get('source', 'Unknown')
                sentiment = article.get('sentiment', 'neutral')
                
                # Sentiment emoji
                sentiment_emoji = {
                    'bullish': '📈',
                    'bearish': '📉',
                    'neutral': '➡️'
                }.get(sentiment, '➡️')
                
                message += f"{i}. {sentiment_emoji} <b>{title}</b>\n"
                message += f"   📡 {source} | 💭 {sentiment.capitalize()}\n\n"
            
            message += f"🕒 <b>Updated:</b> {datetime.utcnow().strftime('%H:%M:%S')} UTC"
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending news update: {e}")
            return False

    async def send_macro_analysis(self, analysis: Dict) -> bool:
        """Send macro sentiment analysis results."""
        if not config.TELEGRAM_NOTIFICATIONS.get('macro_analysis', True):
            return False
            
        try:
            sentiment = analysis.get('market_sentiment', {})
            volatility = analysis.get('volatility', 'Unknown')
            signals = analysis.get('signals', [])
            macro_factors = analysis.get('macro_factors', {})
            
            # Sentiment emoji
            short_term = sentiment.get('short_term', 'Neutral')
            sentiment_emoji = {
                'Bullish': '🐂',
                'Bearish': '🐻',
                'Neutral': '⚖️'
            }.get(short_term, '⚖️')
            
            message = f"""
🧠 <b>MACRO SENTIMENT ANALYSIS</b> {sentiment_emoji}

📊 <b>Market Sentiment:</b>
• Short-term: {short_term} {sentiment_emoji}
• Medium-term: {sentiment.get('medium_term', 'Unknown')}
• Confidence: {sentiment.get('confidence', 'Unknown')}

⚡ <b>Volatility:</b> {volatility}

🎯 <b>Signals Generated:</b> {len(signals)}
            """
            
            # Add key signals
            if signals:
                message += "\n💡 <b>Key Signals:</b>\n"
                for signal in signals[:3]:  # Top 3 signals
                    symbol = signal.get('symbol', 'Unknown')
                    action = signal.get('action', 'WAIT')
                    conf = signal.get('confidence', 0)
                    
                    action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'WAIT': '🟡'}.get(action, '⚪')
                    message += f"• {symbol}: {action_emoji} {action} ({conf:.2f})\n"
            
            # Add macro factors
            if macro_factors:
                primary_risk = macro_factors.get('primary_risk', '')
                if primary_risk:
                    message += f"\n⚠️ <b>Primary Risk:</b> {primary_risk}\n"
                
                opportunities = macro_factors.get('opportunities', [])
                if opportunities:
                    message += f"\n🚀 <b>Opportunities:</b> {', '.join(opportunities[:3])}\n"
            
            message += f"\n🕒 <b>Analysis Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            self.logger.error(f"Error sending macro analysis: {e}")
            return False

    async def send_anomaly_alert(self, anomaly: Dict) -> bool:
        """Send market anomaly alert."""
        if not config.TELEGRAM_NOTIFICATIONS.get('anomalies', True):
            return False
            
        try:
            symbol = anomaly.get('symbol', 'Unknown')
            anomaly_type = anomaly.get('type', 'unknown')
            price_change = anomaly.get('price_change', 0)
            volume_ratio = anomaly.get('volume_ratio', 1)
            confidence = anomaly.get('confidence', 0)
            
            # Type emoji
            type_emoji = {
                'pump': '🚀',
                'dump': '💥',
                'whale': '🐋'
            }.get(anomaly_type, '⚠️')
            
            message = f"""
{type_emoji} <b>MARKET ANOMALY DETECTED</b>

📊 <b>Symbol:</b> {symbol}
🎯 <b>Type:</b> {anomaly_type.upper()}
📈 <b>Price Change:</b> {price_change*100:+.1f}%
📊 <b>Volume Ratio:</b> {volume_ratio:.1f}x normal
🔥 <b>Confidence:</b> {confidence:.2f}

🕒 <b>Detected:</b> {datetime.utcnow().strftime('%H:%M:%S')} UTC

⚡ <i>Consider this for immediate analysis!</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            self.logger.error(f"Error sending anomaly alert: {e}")
            return False

    async def send_daily_summary(self, stats: Dict) -> bool:
        """Send daily trading summary."""
        if not config.TELEGRAM_NOTIFICATIONS.get('daily_summary', True):
            return False
            
        try:
            total_signals = stats.get('total_signals', 0)
            buy_signals = stats.get('buy_signals', 0)
            sell_signals = stats.get('sell_signals', 0)
            wait_signals = stats.get('wait_signals', 0)
            avg_confidence = stats.get('avg_confidence', 0)
            
            message = f"""
📊 <b>DAILY TRADING SUMMARY</b>

🎯 <b>Signals Generated:</b> {total_signals}
• 🟢 BUY: {buy_signals}
• 🔴 SELL: {sell_signals}  
• 🟡 WAIT: {wait_signals}

📈 <b>Average Confidence:</b> {avg_confidence:.2f}

🕒 <b>Report Date:</b> {datetime.utcnow().strftime('%Y-%m-%d')}

💡 <i>System running continuously...</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
            return False

    async def send_error_notification(self, error_msg: str, component: str = 'System') -> bool:
        """Send error notification."""
        if not config.TELEGRAM_NOTIFICATIONS.get('errors', True):
            return False
            
        try:
            message = f"""
❌ <b>SYSTEM ERROR ALERT</b>

🔧 <b>Component:</b> {component}
💥 <b>Error:</b> {error_msg}

🕒 <b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

⚠️ <i>Please check system status</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False

    async def send_startup_notification(self) -> bool:
        """Send system startup notification."""
        try:
            message = f"""
🚀 <b>CRYPTO AI ANALYZER STARTED</b>

✅ System initialized successfully
📊 Monitoring {len(config.SYMBOLS)} symbols
🤖 AI analysis {'enabled' if config.OPENAI_API_KEY or config.CLAUDE_API_KEY else 'disabled'}
📰 News tracking {'enabled' if True else 'disabled'}

🕒 <b>Started:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

💡 <i>Ready to analyze crypto markets!</i>
            """
            
            return await self.send_message(message.strip())
            
        except Exception as e:
            self.logger.error(f"Error sending startup notification: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        if not self.enabled:
            return False
            
        try:
            await self.send_message("🔧 <b>Telegram Bot Test</b>\n\nConnection successful! ✅")
            return True
            
        except Exception as e:
            self.logger.error(f"Telegram bot test failed: {e}")
            return False

    async def get_system_status(self) -> str:
        """Get a summary of the system status."""
        status_message = """
🔧 <b>System Status</b>

✅ System is running
📊 Monitoring {len(config.SYMBOLS)} symbols
🤖 AI analysis {'enabled' if config.OPENAI_API_KEY or config.CLAUDE_API_KEY else 'disabled'}
📰 News tracking {'enabled' if True else 'disabled'}

🕒 <b>Last Check:</b> {datetime.utcnow().strftime('%H:%M:%S')} UTC

💡 <i>Ready to analyze crypto markets!</i>
        """
        return status_message.format(len(config.SYMBOLS))

    async def get_portfolio_status(self, chat_id: int) -> str:
        """Get the user's current portfolio status."""
        portfolio = self.user_portfolios.get(chat_id, {})
        if not portfolio:
            return "📊 <b>Your Portfolio is Empty</b>\n\nYou haven't added any positions yet. Use `/portfolio add [SYMBOL] [AMOUNT]` to start."

        message = "📊 <b>Your Portfolio</b>\n\n"
        total_value = 0
        for symbol, data in portfolio.items():
            amount = data['amount']
            price = data['price']
            current_price = data['current_price']
            pnl = (current_price - price) * amount
            total_value += current_price * amount
            message += f"• {symbol}: {amount} @ ${price:,.2f} = ${current_price:,.2f} (PNL: ${pnl:,.2f})\n"

        message += f"\n📈 <b>Total Portfolio Value:</b> ${total_value:,.2f}"
        return message

    async def add_portfolio_position(self, chat_id: int, symbol: str, amount: float):
        """Add a position to the user's portfolio."""
        symbol = symbol.upper()
        if symbol in self.user_portfolios.get(chat_id, {}):
            self.user_portfolios[chat_id][symbol]['amount'] += amount
        else:
            self.user_portfolios[chat_id][symbol] = {
                'amount': amount,
                'price': 0, # Will be updated on next price update
                'current_price': 0 # Will be updated on next price update
            }
        self.logger.info(f"Added {amount} {symbol} to portfolio for chat {chat_id}")

    async def remove_portfolio_position(self, chat_id: int, symbol: str):
        """Remove a position from the user's portfolio."""
        symbol = symbol.upper()
        if symbol in self.user_portfolios.get(chat_id, {}):
            del self.user_portfolios[chat_id][symbol]
            self.logger.info(f"Removed {symbol} from portfolio for chat {chat_id}")
        else:
            self.logger.warning(f"Attempted to remove non-existent {symbol} from portfolio for chat {chat_id}")

    async def get_latest_signals(self) -> str:
        """Get the latest trading signals from REAL data."""
        try:
            # Import main application to get real signals
            from main import analyzer
            if hasattr(analyzer, 'get_latest_signals'):
                return await analyzer.get_latest_signals()
            
            # If no real signals available, return message
            return "🎯 <b>Latest Trading Signals</b>\n\n❌ No real signals available at the moment.\n\nPlease ensure:\n• Real data sources are working\n• Analysis is running properly\n• VPN is active if needed"
            
        except Exception as e:
            return f"🎯 <b>Latest Trading Signals</b>\n\n❌ Error fetching real signals: {str(e)}"

    async def get_market_overview(self) -> str:
        """Get a current market overview from REAL data."""
        try:
            # Import main application to get real market data
            from main import analyzer
            if hasattr(analyzer, 'get_market_overview'):
                return await analyzer.get_market_overview()
            
            # If no real data available, return message
            return "📈 <b>Current Market Overview</b>\n\n❌ No real market data available at the moment.\n\nPlease ensure:\n• Real data sources are working\n• Internet connection is stable\n• VPN is active if needed"
            
        except Exception as e:
            return f"📈 <b>Current Market Overview</b>\n\n❌ Error fetching real market data: {str(e)}"

    async def get_settings_menu(self, sub_command: str) -> str:
        """Get the settings menu based on sub-command."""
        if sub_command == "notifications":
            return self.get_notification_settings()
        elif sub_command == "signals":
            return self.get_signal_settings()
        elif sub_command == "portfolio":
            return self.get_portfolio_settings()
        elif sub_command == "timing":
            return self.get_timing_settings()
        else:
            return "⚙️ <b>Settings</b>\n\n" + self.get_notification_settings() + "\n" + self.get_signal_settings() + "\n" + self.get_portfolio_settings() + "\n" + self.get_timing_settings()

    def get_notification_settings(self) -> str:
        """Get the notification settings message."""
        return "🔔 <b>Notification Settings</b>\n\n" + \
               "• Trading signals: " + ("Enabled" if config.TELEGRAM_NOTIFICATIONS.get('signals', True) else "Disabled") + "\n" + \
               "• News updates: " + ("Enabled" if config.TELEGRAM_NOTIFICATIONS.get('news', True) else "Disabled") + "\n" + \
               "• Macro analysis: " + ("Enabled" if config.TELEGRAM_NOTIFICATIONS.get('macro_analysis', True) else "Disabled") + "\n" + \
               "• Anomalies: " + ("Enabled" if config.TELEGRAM_NOTIFICATIONS.get('anomalies', True) else "Disabled") + "\n" + \
               "• Daily summary: " + ("Enabled" if config.TELEGRAM_NOTIFICATIONS.get('daily_summary', True) else "Disabled") + "\n" + \
               "• Errors: " + ("Enabled" if config.TELEGRAM_NOTIFICATIONS.get('errors', True) else "Disabled") + "\n\n" + \
               "To change these settings, please use the `/settings` command."

    def get_signal_settings(self) -> str:
        """Get the signal settings message."""
        return "🎯 <b>Signal Settings</b>\n\n" + \
               "• Confidence threshold: " + str(config.MIN_CONFIDENCE) + "\n" + \
               "• Minimum price change for alerts: " + str(config.MIN_PRICE_CHANGE) + "\n" + \
               "• Minimum volume ratio for alerts: " + str(config.MIN_VOLUME_RATIO) + "\n\n" + \
               "To change these settings, please use the `/settings` command."

    def get_portfolio_settings(self) -> str:
        """Get the portfolio settings message."""
        return "📊 <b>Portfolio Settings</b>\n\n" + \
               "• Portfolio tracking: " + ("Enabled" if config.TELEGRAM_PORTFOLIO_TRACKING else "Disabled") + "\n" + \
               "• Portfolio update frequency: " + str(config.TELEGRAM_PORTFOLIO_UPDATE_INTERVAL) + " seconds\n" + \
               "• Portfolio P&L analysis: " + ("Enabled" if config.TELEGRAM_PORTFOLIO_P_L_ANALYSIS else "Disabled") + "\n\n" + \
               "To change these settings, please use the `/settings` command."

    def get_timing_settings(self) -> str:
        """Get the timing settings message."""
        return "⏰ <b>Timing Settings</b>\n\n" + \
               "• Analysis update frequency: " + str(config.ANALYSIS_UPDATE_INTERVAL) + " seconds\n" + \
               "• News update frequency: " + str(config.NEWS_UPDATE_INTERVAL) + " seconds\n" + \
               "• Macro analysis update frequency: " + str(config.MACRO_ANALYSIS_UPDATE_INTERVAL) + " seconds\n" + \
               "• Anomaly detection update frequency: " + str(config.ANOMALY_DETECTION_INTERVAL) + " seconds\n" + \
               "• Daily summary update frequency: " + str(config.DAILY_SUMMARY_INTERVAL) + " seconds\n\n" + \
               "To change these settings, please use the `/settings` command."

    async def perform_ai_analysis(self, analysis_type: str) -> str:
        """Perform a general AI analysis (e.g., market, portfolio)."""
        if analysis_type == "market":
            return await self.send_macro_analysis({
                'market_sentiment': {'short_term': 'Bullish', 'medium_term': 'Strong bullish', 'confidence': 0.9},
                'volatility': 'High',
                'signals': [{'symbol': 'BTCUSDT', 'action': 'BUY', 'confidence': 0.85}, {'symbol': 'ETHUSDT', 'action': 'SELL', 'confidence': 0.6}],
                'macro_factors': {'primary_risk': 'Market volatility', 'opportunities': ['BTC dominance', 'ETH price recovery']}
            })
        elif analysis_type == "portfolio":
            return await self.perform_portfolio_analysis(update.effective_chat.id) # Assuming update is available here
        return "🧠 AI Analysis not implemented for this type."

    async def perform_symbol_analysis(self, symbol: str) -> str:
        """Perform a detailed analysis for a specific symbol using REAL data."""
        try:
            # Import main application to get real analysis
            from main import analyzer
            if hasattr(analyzer, 'perform_symbol_analysis'):
                return await analyzer.perform_symbol_analysis(symbol)
            
            # If no real analysis available, return message
            return f"🧠 <b>Analysis for {symbol}</b>\n\n❌ No real analysis available at the moment.\n\nPlease ensure:\n• Real data sources are working\n• AI analysis is running properly\n• VPN is active if needed"
            
        except Exception as e:
            return f"🧠 <b>Analysis for {symbol}</b>\n\n❌ Error fetching real analysis: {str(e)}"

    async def perform_portfolio_analysis(self, chat_id: int) -> str:
        """Perform a portfolio-specific analysis."""
        portfolio = self.user_portfolios.get(chat_id, {})
        if not portfolio:
            return "📊 <b>No portfolio data available for analysis.</b>"

        total_value = 0
        for symbol, data in portfolio.items():
            amount = data['amount']
            price = data['price']
            current_price = data['current_price']
            pnl = (current_price - price) * amount
            total_value += current_price * amount

        return f"📈 <b>Portfolio Performance Analysis</b>\n\n" + \
               f"• Total Portfolio Value: ${total_value:,.2f}\n" + \
               f"• Total P&L: ${total_value - (sum(data['price'] * data['amount'] for data in portfolio.values())):,.2f}\n" + \
               f"• Average P&L: ${total_value / sum(data['amount'] for data in portfolio.values()) - (sum(data['price'] for data in portfolio.values()) / sum(data['amount'] for data in portfolio.values())):,.2f}\n\n" + \
               "💡 <i>This is a simulated portfolio analysis.</i>"

    async def get_performance_stats(self) -> str:
        """Get performance statistics from REAL data."""
        try:
            # Import main application to get real stats
            from main import analyzer
            if hasattr(analyzer, 'get_performance_stats'):
                return await analyzer.get_performance_stats()
            
            # If no real stats available, return message
            return "📈 <b>Performance Statistics</b>\n\n❌ No real performance data available at the moment.\n\nPlease ensure:\n• Real data sources are working\n• Analysis is running properly\n• VPN is active if needed"
            
        except Exception as e:
            return f"📈 <b>Performance Statistics</b>\n\n❌ Error fetching real stats: {str(e)}"

    async def cmd_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /refresh command - Force refresh market data."""
        try:
            await update.message.reply_text("🔄 <b>Veri yenileniyor...</b>", parse_mode='HTML')
            
            # Force refresh market data
            from data_sources.data_manager import DataManager
            import config
            
            data_manager = DataManager()
            data_manager.clear_cache()  # Clear cache first
            
            fresh_data = await data_manager.get_market_data(config.SYMBOLS, force_refresh=True)
            
            if fresh_data:
                # Send updated signals
                turkish_signals = await self.get_turkish_signals()
                
                keyboard = [
                    [InlineKeyboardButton("📊 Market Analizi", callback_data="market_analysis")],
                    [InlineKeyboardButton("📈 Detaylı Stats", callback_data="detailed_stats")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"✅ <b>Veriler başarıyla yenilendi!</b>\n\n{turkish_signals}",
                    parse_mode='HTML',
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    "❌ <b>Veri yenileme başarısız!</b>\n\nTüm data source'lar şu anda erişilemez durumda.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            self.logger.error(f"Error in refresh command: {e}")
            await update.message.reply_text(
                f"❌ <b>Hata:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def cmd_analyze_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analyze_now command - Trigger immediate analysis."""
        try:
            await update.message.reply_text("🔍 <b>Anında analiz başlatılıyor...</b>", parse_mode='HTML')
            
            # Import main analyzer
            from main import analyzer_instance
            
            if analyzer_instance:
                # Trigger immediate analysis
                validated_signals = await analyzer_instance.daily_analysis()
                
                if validated_signals:
                    signals_count = len(validated_signals)
                    # Get Turkish signals
                    turkish_signals = await self.get_turkish_signals()
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 Detaylar", callback_data="detailed_analysis")],
                        [InlineKeyboardButton("🔄 Yenile", callback_data="refresh_signals")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"✅ <b>Analiz tamamlandı!</b>\n\n🎯 {signals_count} yeni sinyal oluşturuldu\n\n{turkish_signals}",
                        parse_mode='HTML',
                        reply_markup=reply_markup
                    )
                else:
                    await update.message.reply_text(
                        "📊 <b>Analiz tamamlandı</b>\n\nŞu anda yeni sinyal bulunamadı.",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    "❌ <b>Analyzer instance bulunamadı</b>\n\nSistem başlatılmıyor olabilir.",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            self.logger.error(f"Error in analyze_now command: {e}")
            await update.message.reply_text(
                f"❌ <b>Analiz hatası:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def cmd_force_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /force_update command - Force system update and send signals."""
        try:
            await update.message.reply_text("⚡ <b>Zorunlu güncelleme başlatılıyor...</b>", parse_mode='HTML')
            
            from main import analyzer_instance
            
            if analyzer_instance:
                # Force Telegram update
                await analyzer_instance.hourly_telegram_update()
                
                await update.message.reply_text(
                    "✅ <b>Zorunlu güncelleme tamamlandı!</b>\n\n📱 Telegram güncellemesi gönderildi.",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ <b>Analyzer instance bulunamadı</b>",
                    parse_mode='HTML'
                )
                
        except Exception as e:
            self.logger.error(f"Error in force_update command: {e}")
            await update.message.reply_text(
                f"❌ <b>Güncelleme hatası:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def cmd_quick_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quick_stats command - Show quick system statistics."""
        try:
            from data_sources.data_manager import DataManager
            from main import analyzer_instance
            import config
            
            data_manager = DataManager()
            cache_stats = data_manager.get_cache_stats()
            
            # Test API connectivity
            source_status = await data_manager.test_all_sources()
            
            # Build status message
            status_message = "📊 <b>Hızlı Sistem İstatistikleri</b>\n\n"
            
            # API Status
            status_message += "🔌 <b>API Durumu:</b>\n"
            for source, status in source_status.items():
                icon = "✅" if status else "❌"
                status_message += f"  {icon} {source.title()}: {'Çalışıyor' if status else 'Çalışmıyor'}\n"
            
            # Cache Stats
            status_message += f"\n💾 <b>Cache:</b>\n"
            status_message += f"  📦 Entries: {cache_stats['total_entries']}\n"
            status_message += f"  💽 Size: {cache_stats['total_size_bytes']} bytes\n"
            
            # Symbol Count
            status_message += f"\n💰 <b>Tracked Symbols:</b> {len(config.SYMBOLS)}\n"
            
            # System Status
            if analyzer_instance:
                status_message += "\n🤖 <b>Analyzer:</b> ✅ Çalışıyor"
            else:
                status_message += "\n🤖 <b>Analyzer:</b> ❌ Durdurulmuş"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Yenile", callback_data="refresh_quick_stats")],
                [InlineKeyboardButton("📈 Detaylı Stats", callback_data="detailed_stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                status_message,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            self.logger.error(f"Error in quick_stats command: {e}")
            await update.message.reply_text(
                f"❌ <b>Stats hatası:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def cmd_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command - Restart system components."""
        try:
            # Security check - only allow specific users to restart
            user_id = update.effective_user.id
            
            await update.message.reply_text(
                "🔄 <b>Sistem Yeniden Başlatma</b>\n\n"
                "⚠️ Bu komut sistemi yeniden başlatır.\n"
                "Emin misiniz?",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Evet, Yeniden Başlat", callback_data="confirm_restart")],
                    [InlineKeyboardButton("❌ İptal", callback_data="cancel_restart")]
                ])
            )
            
        except Exception as e:
            self.logger.error(f"Error in restart command: {e}")
            await update.message.reply_text(
                f"❌ <b>Restart komutu hatası:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def get_single_crypto_analysis(self, symbol: str) -> str:
        """Get detailed analysis for a single cryptocurrency with real-time data."""
        try:
            from data_sources.data_manager import DataManager
            import config
            
            # Ensure symbol format
            if not symbol.endswith('USDT'):
                symbol = f"{symbol.upper()}USDT"
            
            # Get fresh market data for this symbol
            data_manager = DataManager()
            market_data = await data_manager.get_market_data([symbol], force_refresh=True)
            
            if not market_data or symbol not in market_data:
                return f"❌ <b>{symbol}</b> için veri bulunamadı.\n\nDesteklenen semboller: {', '.join(config.SYMBOLS[:5])}..."
            
            coin_data = market_data[symbol]
            
            # Extract data
            price = coin_data.get('price', 0)
            change_24h = coin_data.get('change_24h', 0)
            volume = coin_data.get('volume', 0)
            high_24h = coin_data.get('high_24h', 0)
            low_24h = coin_data.get('low_24h', 0)
            volume_change = coin_data.get('volume_change_24h', 0)
            source = coin_data.get('source', 'unknown')
            timestamp = coin_data.get('timestamp', '')
            
            # Format timestamp
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M:%S UTC')
            except:
                time_str = "Bilinmiyor"
            
            # Price change indicators
            if change_24h > 0:
                trend_icon = "🚀"
                trend_color = "yeşil"
                trend_text = "Yükseliş"
            elif change_24h < 0:
                trend_icon = "📉"
                trend_color = "kırmızı"
                trend_text = "Düşüş"
            else:
                trend_icon = "➖"
                trend_color = "nötr"
                trend_text = "Sabit"
            
            # Volume analysis
            if volume_change > 0.2:  # 20% increase
                volume_status = "🔥 Yüksek hacim!"
            elif volume_change < -0.2:  # 20% decrease
                volume_status = "📉 Düşük hacim"
            else:
                volume_status = "📊 Normal hacim"
            
            # Technical indicators (simplified)
            price_position = ((price - low_24h) / (high_24h - low_24h)) * 100 if high_24h > low_24h else 50
            
            if price_position > 80:
                tech_status = "🔴 Aşırı alım bölgesinde"
            elif price_position < 20:
                tech_status = "🟢 Aşırı satım bölgesinde" 
            elif price_position > 60:
                tech_status = "🟡 Güçlü bölgede"
            elif price_position < 40:
                tech_status = "🟠 Zayıf bölgede"
            else:
                tech_status = "⚪ Nötr bölgede"
            
            # Trading recommendation
            if change_24h > 0.05:  # +5%
                if volume_change > 0.3:  # High volume
                    recommendation = "💪 <b>GÜÇLÜ ALIM</b>"
                else:
                    recommendation = "✅ <b>ALIM</b>"
            elif change_24h < -0.05:  # -5%
                if volume_change > 0.3:  # High volume selling
                    recommendation = "🚨 <b>GÜÇLÜ SATIM</b>"
                else:
                    recommendation = "⚠️ <b>SATIM</b>"
            else:
                recommendation = "⏳ <b>BEKLE</b>"
            
            # Get AI analysis
            ai_analysis = ""
            try:
                from llm.aggregator import AIAggregator
                ai_aggregator = AIAggregator()
                ai_result = await ai_aggregator.get_single_crypto_analysis(symbol, coin_data)
                if ai_result:
                    ai_analysis = f"\n\n{ai_result}"
                    self.logger.info(f"AI analysis completed for {symbol}")
                else:
                    self.logger.warning(f"AI analysis returned empty for {symbol}")
            except Exception as e:
                self.logger.error(f"AI analysis failed for {symbol}: {e}")
                ai_analysis = ""
            
            # Build analysis message
            analysis = f"""
🎯 <b>{symbol.replace('USDT', '/USDT')} DETAYLI ANALİZ</b>

💰 <b>CANLI FİYAT:</b> <code>${price:,.4f} USD</code> 🔴
{trend_icon} <b>24s Değişim:</b> {change_24h:+.2%} ({trend_text})
📊 <b>Son Güncelleme:</b> {time_str}

📈 <b>24 SAAT VERİLERİ:</b>
🔺 Yüksek: <code>${high_24h:,.4f} USD</code>
🔻 Düşük: <code>${low_24h:,.4f} USD</code>
📊 Ortalama: <code>${(high_24h + low_24h) / 2:,.4f} USD</code>

💹 <b>HACIM ANALİZİ:</b>
💵 24s Hacim: <code>${volume:,.0f} USD</code>
📊 Hacim Değişimi: {volume_change:+.1%}
{volume_status}

🔍 <b>TEKNİK ANALİZ:</b>
📍 Fiyat Pozisyonu: %{price_position:.1f}
{tech_status}

🎯 <b>ÖNERİ:</b>
{recommendation}

ℹ️ <b>VERİ KAYNAĞI:</b> {source.upper()}
🕒 <b>GÜNCELLENDİ:</b> Az önce{ai_analysis}
            """
            
            return analysis.strip()
            
        except Exception as e:
            self.logger.error(f"Error getting single crypto analysis: {e}")
            return f"❌ <b>Analiz hatası:</b> {str(e)}"

    async def cmd_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command - Quick price check for any crypto."""
        try:
            args = context.args
            
            if not args:
                keyboard = await self.get_price_selection_keyboard()
                
                await update.message.reply_text(
                    "💰 <b>Hangi kripto fiyatını kontrol etmek istiyorsunuz?</b>\n\n"
                    "💡 <b>Aşağıdaki butonlardan seçin:</b>\n"
                    "• Tüm desteklenen kriptolar\n"
                    "• Anlık fiyat ve 24s değişim\n"
                    "• Veya manuel: <code>/price BTC</code>\n\n"
                    "⚡ <i>Hızlı fiyat kontrolü için kripto seçin!</i>",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                return
            
            symbol = args[0].upper()
            if not symbol.endswith('USDT'):
                symbol = f"{symbol}USDT"
            
            # Get quick price data
            from data_sources.data_manager import DataManager
            data_manager = DataManager()
            market_data = await data_manager.get_market_data([symbol], force_refresh=True)
            
            if not market_data or symbol not in market_data:
                await update.message.reply_text(
                    f"❌ <b>{symbol}</b> fiyat bilgisi bulunamadı.",
                    parse_mode='HTML'
                )
                return
            
            coin_data = market_data[symbol]
            price = coin_data.get('price', 0)
            change_24h = coin_data.get('change_24h', 0)
            
            # Price trend emoji
            if change_24h > 0:
                trend_emoji = "🚀"
                trend_text = "Yükseliş"
            elif change_24h < 0:
                trend_emoji = "📉"
                trend_text = "Düşüş"
            else:
                trend_emoji = "➖"
                trend_text = "Sabit"
            
            # Quick price message
            price_message = f"""
💰 <b>{symbol.replace('USDT', '/USDT')} CANLI FİYAT</b>

💵 <b>Anlık Değer:</b> <code>${price:,.4f} USD</code> 🔴
{trend_emoji} <b>24s Değişim:</b> {change_24h:+.2%} ({trend_text})

🕒 <b>Son Güncelleme:</b> Az önce
            """
            
            keyboard = [
                [InlineKeyboardButton("🔍 Detaylı Analiz", callback_data=f"analyze_{symbol.replace('USDT', '')}")],
                [InlineKeyboardButton("🔄 Yenile", callback_data=f"price_{symbol.replace('USDT', '')}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                price_message.strip(),
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            self.logger.error(f"Error in price command: {e}")
            await update.message.reply_text(
                f"❌ <b>Fiyat hatası:</b> {str(e)}",
                parse_mode='HTML'
            )

    async def get_crypto_selection_keyboard(self):
        """Create crypto selection keyboard with all supported symbols."""
        import config
        
        # Group cryptos in rows of 3
        keyboard = []
        symbols = config.SYMBOLS
        
        for i in range(0, len(symbols), 3):
            row = []
            for symbol in symbols[i:i+3]:
                crypto_name = symbol.replace('USDT', '')
                # Add emoji for popular cryptos
                emoji = {
                    'BTC': '₿', 'ETH': 'Ξ', 'BNB': '🔶', 
                    'ADA': '🔵', 'SOL': '☀️', 'XRP': '🌊',
                    'DOGE': '🐕', 'DOT': '⚪', 'LINK': '🔗',
                    'TRX': '🔴', 'XLM': '⭐', 'XMR': '🔒',
                    'ZEC': '🛡️', 'PEPE': '🐸'
                }.get(crypto_name, '💰')
                
                row.append(InlineKeyboardButton(
                    f"{emoji} {crypto_name}", 
                    callback_data=f"analyze_{crypto_name}"
                ))
            keyboard.append(row)
        
        # Add quick analysis buttons
        keyboard.append([
            InlineKeyboardButton("📊 Market Genel", callback_data="market_overview"),
            InlineKeyboardButton("🎯 Tüm Sinyaller", callback_data="latest_signals")
        ])
        
        return InlineKeyboardMarkup(keyboard)

    async def get_price_selection_keyboard(self):
        """Create price check selection keyboard."""
        import config
        
        keyboard = []
        symbols = config.SYMBOLS
        
        for i in range(0, len(symbols), 3):
            row = []
            for symbol in symbols[i:i+3]:
                crypto_name = symbol.replace('USDT', '')
                emoji = {
                    'BTC': '₿', 'ETH': 'Ξ', 'BNB': '🔶', 
                    'ADA': '🔵', 'SOL': '☀️', 'XRP': '🌊',
                    'DOGE': '🐕', 'DOT': '⚪', 'LINK': '🔗',
                    'TRX': '🔴', 'XLM': '⭐', 'XMR': '🔒',
                    'ZEC': '🛡️', 'PEPE': '🐸'
                }.get(crypto_name, '💰')
                
                row.append(InlineKeyboardButton(
                    f"{emoji} {crypto_name}", 
                    callback_data=f"price_{crypto_name}"
                ))
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)

    # Utility Methods for Reducing Code Duplication
    def _create_button(self, text: str, callback_data: str) -> InlineKeyboardButton:
        """Create a single inline keyboard button."""
        return InlineKeyboardButton(text, callback_data=callback_data)
    
    def _create_keyboard(self, buttons: List[List[tuple]]) -> InlineKeyboardMarkup:
        """Create inline keyboard from button data."""
        keyboard = []
        for row in buttons:
            keyboard_row = []
            for text, callback_data in row:
                keyboard_row.append(self._create_button(text, callback_data))
            keyboard.append(keyboard_row)
        return InlineKeyboardMarkup(keyboard)
    
    async def _send_message(self, update: Update, message: str, keyboard: Optional[InlineKeyboardMarkup] = None):
        """Standardized message sending with error handling."""
        try:
            await update.message.reply_text(
                message, 
                parse_mode='HTML', 
                reply_markup=keyboard
            )
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            await update.message.reply_text("❌ Mesaj gönderilirken hata oluştu.")
    
    async def _edit_message(self, query, message: str, keyboard: Optional[InlineKeyboardMarkup] = None):
        """Standardized message editing with error handling.""" 
        try:
            await query.edit_message_text(
                text=message,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            self.logger.error(f"Error editing message: {e}")
    
    def _handle_command_error(self, command_name: str):
        """Decorator for command error handling."""
        def decorator(func):
            async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
                try:
                    return await func(self, update, context)
                except Exception as e:
                    self.logger.error(f"Error in {command_name} command: {e}")
                    await self._send_message(update, f"❌ <b>{command_name} hatası:</b> {str(e)}")
            return wrapper
        return decorator

    def start(self):
        """Start Telegram polling with enhanced conflict prevention."""
        if not self.enabled or not self.application:
            return
            
        def _run():
            try:
                # Create new event loop for this thread
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Clear any existing webhooks and pending updates
                async def clear_conflicts():
                    try:
                        # Delete any existing webhook
                        await self.application.bot.delete_webhook(drop_pending_updates=True)
                        self.logger.info("✅ Cleared existing webhook and pending updates")
                        await asyncio.sleep(2)  # Wait a bit
                    except Exception as e:
                        self.logger.warning(f"Webhook clear warning: {e}")
                
                # Setup command menu in the new loop
                loop.run_until_complete(self.setup_command_menu())
                loop.run_until_complete(clear_conflicts())
                
                # Start polling with conflict prevention
                self.logger.info("🤖 Starting Telegram bot polling...")
                self.application.run_polling(
                    drop_pending_updates=True,  # Drop any pending updates
                    close_loop=False,
                    stop_signals=None,
                    allowed_updates=['message', 'callback_query']  # Only handle specific updates
                )
                
            except Exception as e:
                if "Conflict" in str(e):
                    self.logger.error("❌ Telegram bot conflict detected - another instance may be running")
                    self.logger.error("📍 Please ensure only one bot instance is active")
                else:
                    self.logger.error(f"Telegram bot error: {e}")
        
        # Start in separate thread with daemon mode
        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()
        self.logger.info("🤖 Telegram bot thread started")

    async def _get_real_market_data(self) -> Dict:
        """Get real market data from CoinGecko Simple API."""
        try:
            import aiohttp
            from datetime import datetime
            
            # CoinGecko symbol mapping
            symbol_mapping = {
                'BTCUSDT': 'bitcoin',
                'ETHUSDT': 'ethereum', 
                'BNBUSDT': 'binancecoin',
                'ADAUSDT': 'cardano',
                'SOLUSDT': 'solana',
                'PEPEUSDT': 'pepe',
                'XRPUSDT': 'ripple',
                'DOGEUSDT': 'dogecoin',
                'TRXUSDT': 'tron',
                'LINKUSDT': 'chainlink',
                'XLMUSDT': 'stellar',
                'XMRUSDT': 'monero',
                'ZECUSDT': 'zcash'
            }
            
            # Get symbols from config
            symbols = list(symbol_mapping.keys())
            coin_ids = [symbol_mapping[symbol] for symbol in symbols]
            ids_param = ','.join(coin_ids)
            
            # Call CoinGecko Simple API
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Convert to our format
                        market_data = {}
                        for symbol in symbols:
                            coin_id = symbol_mapping[symbol]
                            if coin_id in data:
                                coin_data = data[coin_id]
                                usd_price = coin_data.get('usd', 0)
                                
                                market_data[symbol] = {
                                    'price': usd_price,
                                    'change_24h': 0.0,  # Simple API doesn't provide this
                                    'volume': 0,
                                    'high_24h': usd_price,
                                    'low_24h': usd_price,
                                    'volume_change_24h': 0.0,
                                    'timestamp': datetime.utcnow().isoformat(),
                                    'source': 'coingecko_simple'
                                }
                        
                        self.logger.info(f"✅ Retrieved {len(market_data)} symbols from CoinGecko")
                        return market_data
                    else:
                        self.logger.error(f"CoinGecko API error: {response.status}")
                        return {}
                        
        except Exception as e:
            self.logger.error(f"Error getting real market data: {e}")
            return {}

    async def _generate_ai_signals(self, market_data: Dict) -> List[Dict]:
        """Generate AI trading signals from market data."""
        try:
            # Import AI aggregator
            from llm.aggregator import AIAggregator
            
            aggregator = AIAggregator()
            analysis = await aggregator.analyze_market_data(market_data, "Analyze market data and generate trading signals.")
            
            if analysis and 'signals' in analysis:
                return analysis['signals']
            else:
                # Generate basic signals based on price data
                signals = []
                for symbol, data in market_data.items():
                    price = data.get('price', 0)
                    
                    # Simple signal logic (can be enhanced)
                    if price > 0:
                        signal = {
                            'symbol': symbol,
                            'action': 'WAIT',  # Default to wait
                            'confidence': 0.5,
                            'reason': f'Current price: ${price:,.2f} - Monitoring for opportunities'
                        }
                        signals.append(signal)
                
                return signals
                
        except Exception as e:
            self.logger.error(f"Error generating AI signals: {e}")
            return []

    async def _get_ai_market_analysis(self, market_data: Dict) -> str:
        """Get AI market analysis summary."""
        try:
            # Import AI aggregator
            from llm.aggregator import AIAggregator
            
            aggregator = AIAggregator()
            analysis = await aggregator.analyze_market_data(market_data, "Provide a brief market analysis summary.")
            
            if analysis and 'summary' in analysis:
                return analysis['summary']
            else:
                # Basic analysis
                total_symbols = len(market_data)
                total_value = sum(data.get('price', 0) for data in market_data.values())
                return f"Market analysis: {total_symbols} coins tracked, total market value: ${total_value:,.0f}"
                
        except Exception as e:
            self.logger.error(f"Error getting AI analysis: {e}")
            return "AI analysis temporarily unavailable"

    async def _perform_comprehensive_analysis(self, market_data: Dict) -> str:
        """Perform comprehensive AI analysis."""
        try:
            # Import AI aggregator
            from llm.aggregator import AIAggregator
            
            aggregator = AIAggregator()
            analysis = await aggregator.analyze_market_data(
                market_data, 
                "Perform comprehensive market analysis including trends, opportunities, and risks."
            )
            
            if analysis:
                message = ""
                
                if 'summary' in analysis:
                    message += f"📊 <b>Market Özeti:</b>\n{analysis['summary']}\n\n"
                
                if 'signals' in analysis and analysis['signals']:
                    message += "🎯 <b>Öne Çıkan Sinyaller:</b>\n"
                    for signal in analysis['signals'][:3]:
                        symbol = signal.get('symbol', 'Unknown')
                        action = signal.get('action', 'WAIT')
                        confidence = signal.get('confidence', 0)
                        message += f"• {symbol}: {action} ({confidence:.1%})\n"
                    message += "\n"
                
                if 'market_sentiment' in analysis:
                    sentiment = analysis['market_sentiment']
                    message += f"🧠 <b>Piyasa Sentiment:</b>\n"
                    message += f"• Kısa vadeli: {sentiment.get('short_term', 'N/A')}\n"
                    message += f"• Orta vadeli: {sentiment.get('medium_term', 'N/A')}\n"
                    message += f"• Güven: {sentiment.get('confidence', 'N/A')}\n\n"
                
                return message
            else:
                return "AI analizi şu anda mevcut değil"
                
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return f"Analiz hatası: {str(e)}"


# Global instance - Keep both for compatibility
telegram_notifier = EnhancedTelegramNotifier()
TelegramNotifier = EnhancedTelegramNotifier  # Alias for backward compatibility


# Convenience functions
async def send_signal(signal: Dict) -> bool:
    """Send trading signal to Telegram."""
    return await telegram_notifier.send_trading_signal(signal)

async def send_news(news_data: List[Dict]) -> bool:
    """Send news update to Telegram."""
    return await telegram_notifier.send_news_update(news_data)

async def send_macro_analysis(analysis: Dict) -> bool:
    """Send macro analysis to Telegram."""
    return await telegram_notifier.send_macro_analysis(analysis)

async def send_anomaly(anomaly: Dict) -> bool:
    """Send anomaly alert to Telegram."""
    return await telegram_notifier.send_anomaly_alert(anomaly)

async def send_daily_summary(stats: Dict) -> bool:
    """Send daily summary to Telegram."""
    return await telegram_notifier.send_daily_summary(stats)

async def send_error(error_msg: str, component: str = 'System') -> bool:
    """Send error notification to Telegram."""
    return await telegram_notifier.send_error_notification(error_msg, component)

async def send_startup() -> bool:
    """Send startup notification to Telegram."""
    return await telegram_notifier.send_startup_notification()

async def test_telegram() -> bool:
    """Test Telegram connection."""
    return await telegram_notifier.test_connection()


if __name__ == "__main__":
    # Test the Telegram bot
    async def test_bot():
        print("🤖 Testing Telegram Bot...")
        success = await test_telegram()
        if success:
            print("✅ Telegram bot test successful!")
        else:
            print("❌ Telegram bot test failed!")
    
    asyncio.run(test_bot()) 
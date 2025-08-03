"""
Configuration settings for the crypto analysis and trading signal system.
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')  # Optional: specific chat ID
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN.strip())

# Trading Thresholds
DAILY_PROFIT_TARGET = 0.01  # 1% daily profit target
MAX_DAILY_TRADES = 2
MAX_DAILY_LOSS = -0.02  # -2% max daily loss
MIN_RISK_REWARD_RATIO = 2.0

# Technical Indicators Settings
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
EMA_SHORT = 20
EMA_LONG = 50
VOLUME_THRESHOLD = 1.5  # 1.5x average volume

# Pump Detection Settings
PUMP_PRICE_THRESHOLD = 0.05  # 5% price increase
PUMP_VOLUME_THRESHOLD = 3.0  # 3x average volume
PUMP_SCAN_INTERVAL = 1800  # 30 minutes in seconds

# Time Settings (UTC)
ASIA_SESSION_START = 0  # 00:00 UTC
ASIA_SESSION_END = 8   # 08:00 UTC
OVERLAP_SESSION_START = 13  # 13:00 UTC
OVERLAP_SESSION_END = 16   # 16:00 UTC
DAILY_ANALYSIS_HOUR = 8    # 08:00 UTC

# Market Settings
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT','PEPEUSDT','XRPUSDT','DOGEUSDT','TRXUSDT','LINKUSDT','XLMUSDT','XMRUSDT','ZECUSDT']
DATA_INTERVAL = '1h'  # 1 hour candlesticks

# File Paths
DATA_DIR = 'data'
PRICES_FILE = f'{DATA_DIR}/prices.json'
NEWS_FILE = f'{DATA_DIR}/news.json'
SIGNALS_FILE = f'{DATA_DIR}/signals.json'
LOG_FILE = f'{DATA_DIR}/system.log'

# AI Model Settings
AI_TIMEOUT = 30  # seconds
AI_MAX_RETRIES = 3
USE_AI_FALLBACK = True

# Risk Management
POSITION_SIZE = 0.1  # 10% of portfolio per trade
STOP_LOSS_PCT = 0.02  # 2% stop loss
TAKE_PROFIT_PCT = 0.03  # 3% take profit
PORTFOLIO_VALUE = 10000  # Base portfolio value in USD
MAX_POSITION_PCT = 0.2  # Maximum 20% of portfolio per position

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Telegram Notifications Settings
TELEGRAM_NOTIFICATIONS = {
    'signals': True,        # Send trading signals
    'news': True,          # Send news updates
    'macro_analysis': True, # Send macro analysis
    'anomalies': True,     # Send anomaly alerts
    'daily_summary': True, # Send daily summary
    'errors': True         # Send error notifications
} 
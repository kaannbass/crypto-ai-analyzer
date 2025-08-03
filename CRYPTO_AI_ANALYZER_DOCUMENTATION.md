# Crypto AI Analyzer - Kapsamlı Proje Dokümantasyonu

## 📋 İçindekiler

1. [Proje Genel Bakış](#proje-genel-bakış)
2. [Sistem Mimarisi](#sistem-mimarisi)
3. [Dosya Yapısı](#dosya-yapısı)
4. [Ana Bileşenler](#ana-bileşenler)
5. [Konfigürasyon](#konfigürasyon)
6. [Veri Kaynakları](#veri-kaynakları)
7. [AI Entegrasyonu](#ai-entegrasyonu)
8. [Kural Tabanlı Sistem](#kural-tabanlı-sistem)
9. [Risk Yönetimi](#risk-yönetimi)
10. [Pump Tespit Sistemi](#pump-tespit-sistemi)
11. [Zamanlayıcı ve Oturum Yönetimi](#zamanlayıcı-ve-oturum-yönetimi)
12. [İstatistik ve Raporlama](#istatistik-ve-raporlama)
13. [Kurulum ve Kullanım](#kurulum-ve-kullanım)
14. [API Referansı](#api-referansı)
15. [Geliştiriciler İçin Notlar](#geliştiriciler-için-notlar)

## 🎯 Proje Genel Bakış

Crypto AI Analyzer, kripto para piyasalarını analiz ederek otomatik alım-satım sinyalleri üreten gelişmiş bir Python sistemidir. Sistem, hem yapay zeka hem de kural tabanlı analiz yöntemlerini birleştirerek güvenilir ve risk yönetimli ticaret önerileri sunar.

### Temel Özellikler

- **🤖 Hibrit AI Sistemi**: OpenAI GPT-4 ve Anthropic Claude entegrasyonu
- **📊 Çoklu Veri Kaynağı**: Binance ve CoinGecko API'leri
- **⚡ Pump Tespit Sistemi**: Hızlı fiyat hareketlerini tespit etme
- **🛡️ Risk Yönetimi**: Kapsamlı sermaye koruma sistemi
- **⏰ Oturum Tabanlı Analiz**: Küresel piyasa oturumlarına göre optimizasyon
- **📈 Teknik Analiz**: RSI, MACD, Bollinger Bands dahil 20+ indikatör
- **📋 Gerçek Zamanlı İzleme**: Canlı sinyal ve fiyat takibi

## 🏗️ Sistem Mimarisi

### Katmanlı Mimari

```
┌─────────────────────────────────────────────┐
│                MAIN.PY                      │
│         (Ana Orchestrator)                  │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────┴───────────────────────────┐
│            SCHEDULER                        │
│        (Zaman Tetikleyici)                  │
└─────────────┬───────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼───┐ ┌──▼──┐ ┌─────▼─────┐
│ DAILY │ │HOUR │ │   PUMP    │
│ANALIZ │ │SCAN │ │  SCANNER  │
└───┬───┘ └──┬──┘ └─────┬─────┘
    │        │          │
┌───▼────────▼──────────▼─────┐
│        DATA MANAGER         │
│    (Veri Toplama/Cache)     │
└─────────┬───────────────────┘
          │
┌─────────▼───────────────────┐
│      API KATMANI            │
│  (Binance + CoinGecko)      │
└─────────────────────────────┘
```

### İşlem Akışı

1. **Zamanlayıcı** belirlenen zamanlarda analiz tetikler
2. **Veri Yöneticisi** piyasa verilerini toplar ve önbelleğe alır
3. **AI Aggregator** tüm AI modellerinden analiz alır
4. **Kural Motoru** teknik analiz yapar
5. **Risk Koruması** sinyalleri doğrular
6. **Ana Sistem** sonuçları birleştirir ve kaydeder

## 📁 Dosya Yapısı

```
crypto-ai-analyzer/
├── 📄 main.py                          # Ana uygulama orchestrator
├── ⚙️ config.py                        # Sistem konfigürasyonu
├── 📋 requirements.txt                 # Python bağımlılıkları
├── 📊 monitor_results.py               # Gerçek zamanlı izleme
├── 🔍 test_data_sources.py            # Veri kaynağı testleri
│
├── 📁 data/                           # Veri depolama
│   ├── 💰 prices.json                 # Fiyat verileri
│   ├── 📰 news.json                   # Haber verileri  
│   ├── 🎯 signals.json                # Üretilen sinyaller
│   └── 📜 system.log                  # Sistem logları
│
├── 📁 data_sources/                   # Veri kaynakları
│   ├── 🔧 __init__.py
│   ├── 💹 binance_api.py              # Binance API istemcisi
│   ├── 🌐 coingecko_api.py            # CoinGecko API istemcisi
│   └── 📊 data_manager.py             # Veri yönetimi ve cache
│
├── 📁 llm/                           # AI/LLM entegrasyonu
│   ├── 🔧 __init__.py
│   ├── 🤖 aggregator.py               # AI model aggregator
│   ├── 🎨 claude_client.py            # Claude AI istemcisi
│   ├── 💬 openai_client.py            # OpenAI GPT istemcisi
│   └── 📁 prompt_templates/
│       └── 📝 daily_prompt.md         # Günlük analiz prompt'u
│
├── 📁 rules/                         # Kural tabanlı sistem
│   ├── 🔧 __init__.py
│   ├── ⚖️ rule_engine.py              # Teknik analiz motoru
│   ├── 🛡️ risk_guard.py               # Risk yönetimi
│   └── 📈 stats_engine.py             # İstatistik ve raporlama
│
├── 📁 pump_scanner/                  # Pump tespit sistemi
│   ├── 🔧 __init__.py
│   └── ⚡ pump_detector.py            # Pump tespit algoritması
│
└── 📁 scheduler/                     # Zamanlayıcı sistemi
    ├── 🔧 __init__.py
    └── ⏰ time_trigger.py             # Zaman tetikleyici
```

## 🎛️ Ana Bileşenler

### 1. Ana Orchestrator (main.py)

`CryptoAnalyzer` sınıfı tüm sistemi koordine eder:

#### Temel İşlevler:
```python
class CryptoAnalyzer:
    def __init__(self):
        # Tüm alt sistemleri başlatır
        self.rule_engine = RuleEngine()
        self.risk_guard = RiskGuard() 
        self.ai_aggregator = AIAggregator()
        self.pump_detector = PumpDetector()
```

#### Analiz Türleri:

**📅 Günlük Analiz (08:00 UTC)**
- Kapsamlı piyasa analizi
- AI ve kural tabanlı sinyaller
- Risk değerlendirmesi
- Portföy optimizasyonu

**⏰ Saatlik Tarama**
- Anormallik tespiti
- Momentum değişimleri
- Hızlı sinyal üretimi

**⚡ Pump Taraması (30 dakikada bir)**
- Hızlı fiyat hareketleri
- Hacim doğrulaması
- Sürdürülebilirlik analizi

### 2. Konfigürasyon Sistemi (config.py)

Tüm sistem parametrelerini merkezi olarak yönetir:

#### Ticaret Parametreleri:
```python
DAILY_PROFIT_TARGET = 0.01      # %1 günlük kar hedefi
MAX_DAILY_TRADES = 2            # Günlük max işlem sayısı
MAX_DAILY_LOSS = -0.02          # %2 max günlük kayıp
MIN_RISK_REWARD_RATIO = 2.0     # Minimum risk/ödül oranı
```

#### Teknik İndikatör Ayarları:
```python
RSI_PERIOD = 14                 # RSI periyodu
RSI_OVERSOLD = 30              # RSI aşırı satım
RSI_OVERBOUGHT = 70            # RSI aşırı alım
MACD_FAST = 12                 # MACD hızlı EMA
MACD_SLOW = 26                 # MACD yavaş EMA
EMA_SHORT = 20                 # Kısa EMA
EMA_LONG = 50                  # Uzun EMA
```

#### Pump Tespit Ayarları:
```python
PUMP_PRICE_THRESHOLD = 0.05     # %5 fiyat artışı eşiği
PUMP_VOLUME_THRESHOLD = 3.0     # 3x hacim artışı eşiği
PUMP_SCAN_INTERVAL = 1800       # 30 dakika tarama aralığı
```

## 🌐 Veri Kaynakları

### 1. Veri Yöneticisi (data_manager.py)

Çoklu veri kaynağını yönetir ve cache sistemi sağlar:

#### Temel Özellikler:
```python
class DataManager:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 60        # 60 saniye cache
        self.preferred_source = 'binance'
```

#### Fallback Sistemi:
1. **Binance API** (Birincil)
2. **CoinGecko API** (Yedek)
3. **Dosya Cache** (Son çare)
4. **Mock Data** (Test için)

#### Veri Doğrulama:
```python
def _validate_data(self, data: Dict, expected_symbols: List[str]) -> bool:
    required_fields = ['price', 'volume', 'change_24h']
    # Her sembol için gerekli alanları kontrol eder
```

### 2. Binance API İstemcisi (binance_api.py)

Binance'in resmi API'sini kullanarak gerçek zamanlı veri sağlar:

#### Desteklenen Endpoint'ler:
```python
async def get_ticker_24h(self, symbol=None):      # 24 saatlik ticker
async def get_current_prices(self, symbols):      # Mevcut fiyatlar
async def get_market_data(self, symbols):         # Kapsamlı piyasa verisi
async def get_klines(self, symbol, interval):     # Mum grafiği verisi
async def get_order_book(self, symbol):           # Emir defteri
```

#### Veri Formatı:
```python
{
    'BTCUSDT': {
        'price': 50000.0,
        'volume': 1000000.0,
        'high_24h': 51000.0,
        'low_24h': 49000.0,
        'change_24h': 0.02,             # %2 artış
        'bid_price': 49995.0,
        'ask_price': 50005.0,
        'timestamp': '2024-01-01T12:00:00',
        'source': 'binance'
    }
}
```

### 3. CoinGecko API İstemcisi (coingecko_api.py)

Ücretsiz CoinGecko API'si ile alternatif veri kaynağı:

#### Sembol Eşleme:
```python
symbol_mapping = {
    'BTCUSDT': 'bitcoin',
    'ETHUSDT': 'ethereum',
    'BNBUSDT': 'binancecoin',
    'ADAUSDT': 'cardano',
    'SOLUSDT': 'solana'
}
```

#### Ek Veriler:
- Market cap ve sıralama
- Dolaşımdaki arz miktarı
- Trend olan coinler
- Fiyat değişim yüzdeleri

## 🤖 AI Entegrasyonu

### 1. AI Aggregator (aggregator.py)

Birden fazla AI modelinin çıktısını birleştirir:

#### Desteklenen Modeller:
- **OpenAI GPT-4** (Hızlı analiz)
- **Anthropic Claude** (Detaylı analiz)

#### Analiz Süreci:
```python
async def get_daily_analysis(self, market_data):
    # Paralel AI analizleri başlat
    tasks = []
    if self.openai_client.is_available():
        tasks.append(('openai', self.openai_client.analyze_market_data(...)))
    if self.claude_client.is_available():
        tasks.append(('claude', self.claude_client.analyze_market_data(...)))
    
    # Sonuçları birleştir
    return self.aggregate_analyses(results)
```

#### Sinyal Birleştirme:
```python
def aggregate_symbol_signals(self, symbol, signals):
    # Güven skorlarını ağırlıklandır
    # Uzlaşma eylemini belirle
    # Anlaşma bonusu uygula
    # Final güven skorunu hesapla
```

### 2. OpenAI İstemcisi (openai_client.py)

GPT-4 ile piyasa analizi:

#### Analiz Türleri:
```python
async def analyze_market_data(self, market_data, prompt):
    # Ana piyasa verisi analizi
    
async def evaluate_news_sentiment(self, news_data):
    # Haber duygu analizi
    
async def analyze_pump_sustainability(self, pump_data):
    # Pump sürdürülebilirlik analizi
    
async def get_daily_market_overview(self, market_data):
    # Günlük piyasa genel bakışı
```

#### Mock Analiz Mantığı:
```python
def generate_mock_analysis(self, market_data, prompt):
    for symbol, data in market_data.items():
        price_change = data.get('change_24h', 0)
        
        if price_change > 0.05:          # %5 artış
            action = 'SELL'              # Kar realizasyonu
            confidence = 0.7
        elif price_change < -0.05:       # %5 düşüş  
            action = 'BUY'               # Dip alımı
            confidence = 0.75
        else:
            action = 'WAIT'              # Belirsizlik
            confidence = 0.6
```

### 3. Claude İstemcisi (claude_client.py)

Claude AI ile konservatif analiz:

#### Özel Özellikler:
```python
def analyze_market_context(self, market_data):
    # Piyasa genişliği analizi
    # Volatilite rejimi tespiti
    # Korelasyon risk değerlendirmesi
    
def generate_strategic_outlook(self, market_data):
    # Trend gücü belirleme
    # Stratejik görünüm oluşturma
    # Zaman ufku ve katalizörler
```

#### Risk Değerlendirmesi:
```python
async def evaluate_risk_factors(self, market_data):
    # Piyasa tabanlı riskler
    # Hacim tabanlı riskler  
    # Korelasyon riskleri
    # Genel risk skoru hesaplama
```

## ⚖️ Kural Tabanlı Sistem

### 1. Kural Motoru (rule_engine.py)

Teknik analiz indikatörlerini kullanarak sinyal üretir:

#### Teknik İndikatörler:

**RSI (Relative Strength Index)**
```python
def calculate_rsi(self, prices, period=14):
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [delta if delta > 0 else 0 for delta in deltas]
    losses = [-delta if delta < 0 else 0 for delta in deltas]
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
```

**MACD (Moving Average Convergence Divergence)**
```python
def calculate_macd(self, prices):
    ema_fast = self.calculate_ema(prices, config.MACD_FAST)
    ema_slow = self.calculate_ema(prices, config.MACD_SLOW)
    
    macd_line = ema_fast - ema_slow
    signal_line = self.calculate_ema([macd_line], config.MACD_SIGNAL)
    histogram = macd_line - signal_line
```

**Bollinger Bands**
```python
def calculate_bollinger_bands(self, prices, period=20, std_dev=2):
    sma = sum(recent_prices) / period
    variance = sum((price - sma) ** 2 for price in recent_prices) / period
    std_deviation = math.sqrt(variance)
    
    upper_band = sma + (std_deviation * std_dev)
    lower_band = sma - (std_deviation * std_dev)
```

#### Sinyal Değerlendirme:
```python
def evaluate_indicators(self, symbol, current_price, rsi, macd_data, bb_data, volume_data):
    signals = []
    confidence = 0.0
    
    # RSI Analizi
    if rsi < config.RSI_OVERSOLD:        # Aşırı satım
        signals.append('BUY')
        confidence += 0.3
    elif rsi > config.RSI_OVERBOUGHT:    # Aşırı alım
        signals.append('SELL') 
        confidence += 0.3
    
    # MACD Analizi
    if macd_data['histogram'] > 0:       # Boğa kesişimi
        signals.append('BUY')
        confidence += 0.25
    
    # Bollinger Bands Analizi  
    if current_price <= bb_data['lower']: # Alt bantta
        signals.append('BUY')
        confidence += 0.2
        
    # Final karar
    buy_signals = signals.count('BUY')
    sell_signals = signals.count('SELL')
    
    if buy_signals > sell_signals:
        action = 'BUY'
    elif sell_signals > buy_signals:
        action = 'SELL'
    else:
        action = 'WAIT'
```

### 2. Risk Koruması (risk_guard.py)

Sermaye koruma ve risk yönetimi:

#### Günlük Limitler:
```python
def can_trade_today(self):
    today_trades = [trade for trade in self.daily_trades 
                   if trade_date == today]
    
    # Maksimum günlük işlem kontrolü
    if len(today_trades) >= config.MAX_DAILY_TRADES:
        return False
        
    # Günlük kayıp limiti kontrolü
    today_pnl = sum(trade.get('pnl', 0) for trade in today_trades)
    if today_pnl <= config.MAX_DAILY_LOSS:
        return False
```

#### Sinyal Doğrulama:
```python
def validate_signal(self, signal):
    # Günlük ticaret kontrolü
    if not self.can_trade_today():
        return False
        
    # Minimum güven kontrolü
    if signal.get('confidence', 0) < 0.5:
        return False
        
    # Mevcut pozisyon kontrolü
    if symbol in self.open_positions:
        return False
        
    # Risk/ödül oranı kontrolü
    if not self.check_risk_reward_ratio(signal):
        return False
```

#### Pozisyon Yönetimi:
```python
def open_position(self, signal, entry_price):
    stop_loss = self.calculate_stop_loss(entry_price, action)
    take_profit = self.calculate_take_profit(entry_price, action)
    
    position = {
        'symbol': symbol,
        'action': action,
        'entry_price': entry_price,
        'stop_loss': stop_loss,         # %2 stop loss
        'take_profit': take_profit,     # %3 take profit
        'quantity': self.calculate_quantity(entry_price),
        'status': 'open'
    }
```

#### Stop Loss & Take Profit:
```python
def check_stop_loss_take_profit(self, current_prices):
    for symbol, position in self.open_positions.items():
        current_price = current_prices[symbol]
        
        if action == 'BUY':
            if current_price <= stop_loss:
                self.close_position(symbol, current_price, 'stop_loss')
            elif current_price >= take_profit:
                self.close_position(symbol, current_price, 'take_profit')
```

## ⚡ Pump Tespit Sistemi

### Pump Detector (pump_detector.py)

Hızlı fiyat hareketlerini tespit eden gelişmiş sistem:

#### Ana Tarama Süreci:
```python
async def scan_for_pumps(self):
    market_data = await self.get_current_market_data()
    
    for symbol in config.SYMBOLS:
        pump = await self.analyze_symbol_for_pump(symbol, market_data[symbol])
        if pump:
            pumps_detected.append(pump)
    
    # Yakın zamanda tespit edilenleri filtrele
    new_pumps = self.filter_recent_pumps(pumps_detected)
```

#### Fiyat Metrik Hesaplama:
```python
def calculate_price_metrics(self, current_price, price_history):
    recent_prices = price_history[-12:]  # Son 12 veri noktası
    avg_price_1h = sum(recent_prices) / len(recent_prices)
    
    # 1 saatlik değişim
    price_change_1h = (current_price - avg_price_1h) / avg_price_1h
    
    # 15 dakikalık değişim  
    if len(recent_prices) >= 3:
        price_15m_ago = recent_prices[-3]
        price_change_15m = (current_price - price_15m_ago) / price_15m_ago
```

#### Hacim Analizi:
```python
def calculate_volume_metrics(self, current_volume, volume_history):
    recent_volumes = volume_history[-24:]  # Son 24 periyot
    avg_volume = sum(recent_volumes) / len(recent_volumes)
    
    volume_ratio = current_volume / avg_volume
    
    # Hacim trendi
    if len(recent_volumes) >= 6:
        recent_avg = sum(recent_volumes[-6:]) / 6
        older_avg = sum(recent_volumes[-12:-6]) / 6
        volume_trend = 'increasing' if recent_avg > older_avg * 1.2 else 'stable'
```

#### Pump Kriterleri:
```python
def evaluate_pump_criteria(self, symbol, price_metrics, volume_metrics):
    price_change_15m = price_metrics.get('price_change_15m', 0)
    volume_ratio = volume_metrics.get('volume_ratio', 1.0)
    
    # Temel kriterler
    meets_price_threshold = price_change_15m >= config.PUMP_PRICE_THRESHOLD    # %5
    meets_volume_threshold = volume_ratio >= config.PUMP_VOLUME_THRESHOLD      # 3x
    
    # Kalite filtreleri
    reasonable_24h_change = abs(change_24h) <= 0.5  # %50'den az
    volume_trend_positive = volume_trend in ['increasing', 'unknown']
    
    # Pump skoru hesaplama
    pump_score = 0.0
    if meets_price_threshold: pump_score += 0.4
    if meets_volume_threshold: pump_score += 0.3
    if sustained_movement: pump_score += 0.2
    if volume_trend_positive: pump_score += 0.1
```

#### Risk Faktörleri:
```python
def assess_pump_risks(self, price_metrics, volume_metrics):
    risks = []
    
    if price_change_15m > 0.20:  # %20'den fazla 15 dakikada
        risks.append('Extreme price movement - high retracement risk')
        
    if volume_ratio > 10:  # Aşırı yüksek hacim
        risks.append('Extreme volume spike - may indicate whale manipulation')
        
    if current_hour < 6 or current_hour > 22:  # Düşük aktivite saatleri
        risks.append('Low activity hours - pump may lack follow-through')
```

## ⏰ Zamanlayıcı ve Oturum Yönetimi

### Time Trigger (time_trigger.py)

Küresel piyasa oturumlarına göre optimizasyon:

#### Oturum Tanımları:
```python
def get_current_session(self):
    hour = datetime.utcnow().hour
    
    if 0 <= hour < 8:    return 'asia'      # Asya oturumu
    elif 8 <= hour < 13: return 'europe'    # Avrupa oturumu  
    elif 13 <= hour < 16: return 'overlap'  # Çakışma oturumu
    elif hour >= 17:     return 'us'        # ABD oturumu
```

#### Oturum Karakteristikleri:
```python
def get_session_characteristics(self, session):
    characteristics = {
        'asia': {
            'volatility': 'medium',
            'recommended_strategy': 'range_trading',
            'risk_multiplier': 1.0
        },
        'europe': {
            'volatility': 'high', 
            'recommended_strategy': 'trend_following',
            'risk_multiplier': 1.2
        },
        'overlap': {
            'volatility': 'very_high',
            'recommended_strategy': 'breakout_trading', 
            'risk_multiplier': 1.5
        },
        'us': {
            'volatility': 'high',
            'recommended_strategy': 'momentum_trading',
            'risk_multiplier': 1.3
        }
    }
```

#### Zaman Bazlı Ayarlamalar:
```python
def adjust_confidence_by_time(self, confidence):
    session = self.get_current_session()
    
    if session == 'overlap':
        time_multiplier = 1.1      # Yüksek aktivite
    elif session in ['europe', 'us']:
        time_multiplier = 1.05     # Ana oturumlar
    elif session == 'weekend':
        time_multiplier = 0.8      # Hafta sonu
        
    # Haber zamanlarında azaltma
    if self.is_major_news_time():
        time_multiplier *= 0.85
```

#### Dinamik Tarama Frekansı:
```python
def get_optimal_scan_frequency(self):
    session = self.get_current_session()
    
    frequencies = {
        'overlap': 15,     # Her 15 dakika
        'europe': 20,      # Her 20 dakika
        'us': 20,          # Her 20 dakika
        'asia': 30,        # Her 30 dakika
        'weekend': 60      # Her saat
    }
```

## 📊 İstatistik ve Raporlama

### Stats Engine (stats_engine.py)

Performans takibi ve detaylı raporlama:

#### Performans Metrikleri:
```python
def calculate_performance_metrics(self, trades):
    total_trades = len(trades)
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
    
    win_rate = len(winning_trades) / total_trades
    
    # Ortalama kazanç/kayıp
    avg_win = sum(t.get('pnl', 0) for t in winning_trades) / len(winning_trades)
    avg_loss = sum(t.get('pnl', 0) for t in losing_trades) / len(losing_trades)
    
    # Kar faktörü
    gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
    gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
    profit_factor = gross_profit / gross_loss
    
    # Maksimum düşüş
    max_drawdown = self.calculate_max_drawdown(cumulative_pnl)
```

#### Günlük Rapor:
```python
def generate_daily_report(self, trades, signals):
    performance = self.calculate_performance_metrics(today_trades)
    signal_analysis = self.analyze_signals(today_signals)
    risk_analysis = self.analyze_risk(today_trades)
    
    report = {
        'date': today.isoformat(),
        'performance': performance,
        'signal_analysis': signal_analysis,
        'risk_analysis': risk_analysis,
        'summary': self.generate_summary(...)
    }
```

#### Sinyal Analizi:
```python
def analyze_signals(self, signals):
    buy_signals = [s for s in signals if s.get('action') == 'BUY']
    sell_signals = [s for s in signals if s.get('action') == 'SELL'] 
    wait_signals = [s for s in signals if s.get('action') == 'WAIT']
    
    # Ortalama güven
    confidences = [s.get('confidence', 0) for s in signals]
    avg_confidence = sum(confidences) / len(confidences)
    
    # Sinyal türleri
    signal_types = {}
    for signal in signals:
        signal_type = signal.get('type', 'daily')
        signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
```

### Monitor Results (monitor_results.py)

Gerçek zamanlı izleme arayüzü:

#### Canlı Veri Görüntüleme:
```python
def print_prices(price_data):
    for symbol, info in data.items():
        price = info.get('price', 0)
        change = info.get('change_24h', 0)
        volume = info.get('volume', 0)
        
        change_icon = "🔺" if change > 0 else "🔻" if change < 0 else "➖"
        print(f"{change_icon} {symbol}: ${price:,.2f} ({change:+.2%})")
```

#### Son Sinyaller:
```python
def print_latest_signals(signals, limit=3):
    recent_signals = signals[-limit:]
    
    for signal in recent_signals:
        action = signal.get('action', 'WAIT')
        confidence = signal.get('confidence', 0)
        reasoning = signal.get('reasoning', '')
        
        action_icon = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "🟡"
        print(f"{action_icon} {symbol}: {action} (conf: {confidence:.2f})")
```

## 🚀 Kurulum ve Kullanım

### Sistem Gereksinimleri

```bash
# Python sürümü
Python 3.8+

# İşletim sistemi
Linux / macOS / Windows

# Bellek
Minimum 512MB RAM

# Disk alanı  
100MB boş alan
```

### Kurulum Adımları

1. **Projeyi Klonlayın**
```bash
git clone <repository-url>
cd crypto-ai-analyzer
```

2. **Sanal Ortam Oluşturun**
```bash
python -m venv crypto-env
source crypto-env/bin/activate  # Linux/Mac
# veya
crypto-env\Scripts\activate     # Windows
```

3. **Bağımlılıkları Yükleyin**
```bash
pip install -r requirements.txt
```

4. **API Anahtarlarını Ayarlayın**
```bash
export OPENAI_API_KEY="your-openai-key"
export CLAUDE_API_KEY="your-claude-key"
```

5. **Sistemi Başlatın**
```bash
python main.py
```

6. **İzlemeyi Başlatın** (ayrı terminal)
```bash
python monitor_results.py
```

### Konfigürasyon Ayarları

`config.py` dosyasından özelleştirilebilir parametreler:

```python
# Ticaret Ayarları
DAILY_PROFIT_TARGET = 0.01      # Günlük kar hedefi
MAX_DAILY_TRADES = 2            # Max günlük işlem
MAX_DAILY_LOSS = -0.02          # Max günlük kayıp

# Analiz Edilen Coinler
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']

# Zamanlama
DAILY_ANALYSIS_HOUR = 8         # Günlük analiz saati (UTC)
PUMP_SCAN_INTERVAL = 1800       # Pump tarama aralığı (saniye)

# Risk Yönetimi
POSITION_SIZE = 0.1             # Pozisyon büyüklüğü (%10)
STOP_LOSS_PCT = 0.02            # Stop loss (%2)
TAKE_PROFIT_PCT = 0.03          # Take profit (%3)
```

## 📋 API Referansı

### CryptoAnalyzer Ana Sınıfı

```python
class CryptoAnalyzer:
    async def daily_analysis()          # Günlük kapsamlı analiz
    async def hourly_scan()             # Saatlik anormallik taraması  
    async def pump_scan()               # Pump tespit taraması
    async def get_market_data()         # Piyasa verisi alma
    def combine_signals()               # Sinyalleri birleştirme
    def save_signal()                   # Sinyal kaydetme
    async def run_scheduler()           # Ana zamanlayıcı döngüsü
```

### DataManager Veri Yönetimi

```python
class DataManager:
    async def get_market_data(symbols, force_refresh=False)
    async def get_historical_data(symbol, interval='1h', limit=100)
    async def test_all_sources()        # Tüm API bağlantılarını test et
    def clear_cache()                   # Cache'i temizle
    def get_cache_stats()               # Cache istatistikleri
```

### RuleEngine Teknik Analiz

```python
class RuleEngine:
    def calculate_rsi(prices, period=14)
    def calculate_macd(prices)
    def calculate_ema(prices, period)
    def calculate_bollinger_bands(prices, period=20, std_dev=2)
    def generate_signal(symbol, market_data)
    def detect_anomaly(symbol, market_data)
```

### RiskGuard Risk Yönetimi

```python
class RiskGuard:
    def can_trade_today()               # Günlük ticaret kontrolü
    def validate_signal(signal)         # Sinyal doğrulama
    def open_position(signal, entry_price)
    def close_position(symbol, exit_price, reason)
    def check_stop_loss_take_profit(current_prices)
    def get_daily_stats()               # Günlük istatistikler
```

### PumpDetector Pump Tespit

```python
class PumpDetector:
    async def scan_for_pumps()          # Pump taraması
    async def analyze_symbol_for_pump(symbol, data)
    def calculate_price_metrics(current_price, price_history)
    def calculate_volume_metrics(current_volume, volume_history)
    def evaluate_pump_criteria(symbol, price_metrics, volume_metrics)
    def get_pump_statistics()           # Pump istatistikleri
```

## 🔧 Geliştiriciler İçin Notlar

### Kod Yapısı ve Mimarisi

#### SOLID Prensipleri
- **Single Responsibility**: Her sınıf tek bir sorumluluğa sahip
- **Open/Closed**: Yeni özellikler extension ile eklenir
- **Liskov Substitution**: Alt sınıflar üst sınıfların yerine geçebilir
- **Interface Segregation**: Küçük, odaklanmış interface'ler
- **Dependency Inversion**: Soyutlamalara bağımlılık

#### Async/Await Kullanımı
```python
# API çağrıları paralel olarak yapılır
tasks = []
tasks.append(('binance', get_binance_data(symbols)))
tasks.append(('coingecko', get_coingecko_data(symbols)))

results = await asyncio.gather(*[task[1] for task in tasks])
```

#### Error Handling
```python
try:
    result = await risky_operation()
except asyncio.TimeoutError:
    self.logger.warning("Operation timed out")
    result = fallback_operation()
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
    result = default_value
```

#### Logging Sistemi
```python
import logging

# Her modül kendi logger'ını kullanır
self.logger = logging.getLogger(__name__)

# Farklı log seviyeleri
self.logger.debug("Detaylı debug bilgisi")
self.logger.info("Genel bilgilendirme") 
self.logger.warning("Uyarı mesajı")
self.logger.error("Hata mesajı")
```

### Genişletme Noktaları

#### Yeni Veri Kaynağı Ekleme
1. `data_sources/` altında yeni API istemcisi oluştur
2. `DataManager._fetch_from_sources()` metoduna ekle
3. Veri formatı standardizasyonu uygula

#### Yeni AI Modeli Ekleme  
1. `llm/` altında yeni istemci sınıfı oluştur
2. `AIAggregator` içine entegrasyonu ekle
3. Sinyal birleştirme mantığını güncelle

#### Yeni Teknik İndikatör Ekleme
1. `RuleEngine` sınıfına hesaplama metodu ekle
2. `evaluate_indicators()` içine değerlendirme mantığı ekle
3. Konfigürasyona yeni parametreler ekle

### Test Etme

#### Unit Testler
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_data_manager():
    dm = DataManager()
    data = await dm.get_market_data(['BTCUSDT'])
    assert 'BTCUSDT' in data
    assert 'price' in data['BTCUSDT']
```

#### Entegrasyon Testleri
```python
async def test_full_analysis_cycle():
    analyzer = CryptoAnalyzer()
    await analyzer.daily_analysis()
    
    # Sinyallerin üretildiğini kontrol et
    assert len(analyzer.signals) > 0
```

#### Mock Testleri
```python
from unittest.mock import Mock, AsyncMock

@patch('data_sources.binance_api.BinanceAPI')
async def test_with_mock_api(mock_binance):
    mock_binance.get_market_data.return_value = mock_data
    # Test kodunu çalıştır
```

### Performans Optimizasyonu

#### Cache Stratejisi
- Veri API çağrıları 60 saniye cache'lenir
- Hesaplanan indikatörler geçici olarak saklanır
- Dosya I/O operasyonları minimize edilir

#### Bellek Yönetimi
```python
# Büyük veri yapılarını temizle
del large_data_structure

# Gereksiz referansları kaldır
self.cache.clear()

# Garbage collection'ı tetikle
import gc
gc.collect()
```

#### Paralel İşlem
```python
# Birden fazla sembolü paralel analiz et
tasks = [analyze_symbol(symbol) for symbol in symbols]
results = await asyncio.gather(*tasks)

# AI analizlerini paralel çalıştır
openai_task = asyncio.create_task(openai_analysis())
claude_task = asyncio.create_task(claude_analysis())
```

### Güvenlik Konuları

#### API Anahtar Yönetimi
```python
import os
from cryptography.fernet import Fernet

# Environment variables kullan
api_key = os.getenv('OPENAI_API_KEY')

# Kritik veriler için şifreleme
f = Fernet(key)
encrypted_data = f.encrypt(sensitive_data.encode())
```

#### Rate Limiting
```python
import time

class RateLimiter:
    def __init__(self, max_calls, time_window):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    async def acquire(self):
        now = time.time()
        # Rate limiting mantığı
```

#### Input Validation
```python
def validate_symbol(symbol):
    if not isinstance(symbol, str):
        raise ValueError("Symbol must be string")
    if not symbol.endswith('USDT'):
        raise ValueError("Only USDT pairs supported")
    return symbol.upper()
```

### Monitoring ve Alerting

#### Sistem Durumu İzleme
```python
class HealthChecker:
    async def check_api_health(self):
        # API bağlantılarını test et
        pass
    
    async def check_data_freshness(self):
        # Veri güncelliğini kontrol et
        pass
    
    async def check_signal_generation(self):
        # Sinyal üretimini kontrol et
        pass
```

#### Log Analizi
```python
import re
from collections import Counter

def analyze_logs():
    with open('data/system.log', 'r') as f:
        logs = f.readlines()
    
    # Error pattern'leri say
    error_patterns = Counter()
    for line in logs:
        if 'ERROR' in line:
            # Pattern'i çıkar ve say
            pass
```

## 📈 Gelecek Geliştirmeler

### Planlanan Özellikler

1. **Gelişmiş AI Entegrasyonu**
   - Sentiment analizi için Twitter/Reddit entegrasyonu
   - Makro ekonomik veri analizi
   - Multi-modal analiz (grafik + metin)

2. **Portfolio Yönetimi**
   - Çoklu coin portföy optimizasyonu
   - Risk parity algoritmaları
   - Dynamik hedge stratejileri

3. **Backtesting Sistemi**
   - Historik veri üzerinde strateji testi
   - Performance attribution analizi
   - Risk ayarlı getiri metrikleri

4. **Web Dashboard**
   - Real-time görselleştirme
   - Mobil responsive tasarım
   - Interaktif grafik ve analizler

5. **Machine Learning**
   - Custom model training
   - Feature engineering otomasyonu
   - Ensemble learning yöntemleri

### Teknik İyileştirmeler

1. **Mikroservis Mimarisi**
   - Docker containerization
   - Kubernetes orchestration
   - Service mesh entegrasyonu

2. **Database Entegrasyonu**
   - PostgreSQL/TimescaleDB
   - Redis cache katmanı
   - Data lake çözümü

3. **Messaging System**
   - Apache Kafka/RabbitMQ
   - Event-driven architecture
   - Real-time data streaming

4. **Monitoring ve Observability**
   - Prometheus/Grafana
   - Distributed tracing
   - Custom metrics

---

## 📝 Sonuç

Crypto AI Analyzer, modern yazılım geliştirme prensiplerini kullanarak tasarlanmış kapsamlı bir kripto para analiz sistemidir. Hibrit AI yaklaşımı, sağlam risk yönetimi ve modüler mimari sayesinde hem güvenilir hem de genişletilebilir bir çözüm sunar.

Sistem, gerçek zamanlı veri işleme, çoklu AI model entegrasyonu ve detaylı risk yönetimi ile profesyonel trading operasyonları için gerekli tüm bileşenleri içerir. Açık kaynak kodlu yapısı sayesinde topluluk katkıları ile sürekli gelişim gösterebilir.

**Proje deposu**: [GitHub Repository URL]
**Lisans**: MIT License
**Geliştirici**: AI Assistant
**Versiyon**: 1.0.0
**Son güncellenme**: 2024

---

*Bu dokümantasyon, Crypto AI Analyzer projesinin tüm teknik detaylarını kapsamaktadır. Sorularınız veya katkılarınız için GitHub repository'sindeki issue tracker'ı kullanabilirsiniz.* 
# 🚀 Crypto AI Analyzer - Çalıştırma Rehberi

## 📋 Sistem Genel Bakış

Artık sistemde **3 ana bileşen** var:

1. **🤖 Ana AI Analyzer** (`main.py`) - Günlük/saatlik analiz, AI entegrasyonu
2. **⚡ WebSocket Client** (`binance_websocket_client.py`) - Real-time fiyat takibi ve pump tespiti
3. **📊 Enhanced Monitor** (`monitor_results_enhanced.py`) - Gelişmiş izleme arayüzü

## 🛠️ Kurulum

### 1. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 2. API Anahtarları (Opsiyonel)
```bash
export OPENAI_API_KEY="your-openai-key"
export CLAUDE_API_KEY="your-claude-key"
```

## 🏃‍♂️ Sistemi Çalıştırma

### Seçenek 1: Tam Sistem (Önerilen)

**Terminal 1 - Ana Sistem:**
```bash
python main.py
```
Bu başlatacak:
- ✅ WebSocket real-time veri akışı
- ✅ Günlük analiz (08:00 UTC)
- ✅ Saatlik anomali taraması
- ✅ 30 dakikada bir pump taraması
- ✅ AI analiz entegrasyonu
- ✅ Risk yönetimi

**Terminal 2 - Enhanced Monitor:**
```bash
python monitor_results_enhanced.py
```
Bu gösterecek:
- 💹 Real-time WebSocket fiyatları
- 💰 API fiyatları
- 📡 Live feed aktivitesi
- 🎯 Son sinyaller
- 📈 İstatistikler
- 🟢/🔴 WebSocket durumu

### Seçenek 2: Sadece WebSocket Client

```bash
python binance_websocket_client.py
```
Bu sadece:
- ⚡ Real-time fiyat akışı
- 🚀 Pump alert'leri
- 📄 `crypto_feed.jsonl` dosyasına log

### Seçenek 3: Sadece Eski Monitor

```bash
python monitor_results.py
```
Bu sadece statik dosyaları izler.

## 📊 Çıktılar ve Dosyalar

### Oluşturulacak Dosyalar:
```
data/
├── signals.json           # AI ve kural tabanlı sinyaller
├── prices.json           # API fiyat verileri
├── system.log           # Sistem logları
└── websocket_feed.jsonl # Real-time WebSocket verileri

crypto_feed.jsonl         # Enhanced monitor için WebSocket logları
```

### Real-time WebSocket Logları:
```json
{"symbol": "BTCUSDT", "price": 29450.23, "timestamp": 1691055000, "event_type": "trade"}
{"symbol": "ETHUSDT", "price": 1850.45, "timestamp": 1691055001, "event_type": "trade"}
```

### Pump Alert Örneği:
```
🚀 PUMP ALERT: BTCUSDT +3.27% in last 5 ticks
🚀 PUMP ALERT: SOLUSDT +4.12% in last 5 ticks
```

## 🎛️ Konfigürasyon

### `config.py` - Ana Ayarlar:
```python
# İzlenecek coinler
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']

# Pump tespit eşikleri
PUMP_PRICE_THRESHOLD = 0.05    # %5 fiyat artışı
PUMP_VOLUME_THRESHOLD = 3.0    # 3x hacim artışı

# Risk yönetimi
MAX_DAILY_TRADES = 2           # Günlük max işlem
MAX_DAILY_LOSS = -0.02         # %2 max kayıp
```

### WebSocket Ayarları:
```python
# binance_websocket_client.py içinde
symbols = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "adausdt"]
log_file = "crypto_feed.jsonl"
```

## 📈 Enhanced Monitor Özellikler

### Real-time Görüntüleme:
- **💹 LIVE PRICES**: WebSocket'ten gelen anlık fiyatlar
- **💰 API PRICES**: Binance/CoinGecko API fiyatları
- **📡 LIVE FEED**: Son 20 tick aktivite özeti
- **🎯 LATEST SIGNALS**: Son 3 AI/kural sinyal
- **📈 STATISTICS**: Sinyal istatistikleri
- **🟢/🔴 WebSocket Status**: Bağlantı durumu

### Otomatik Özellikler:
- ✅ 10 saniyede bir ekran yenileme
- ✅ Yeni sinyal bildirileri
- ✅ WebSocket otomatik yeniden bağlanma
- ✅ Fiyat değişim takibi
- ✅ Pump alert entegrasyonu

## 🔧 Troubleshooting

### WebSocket Bağlantı Sorunları:
```bash
# İnternet bağlantısını kontrol et
ping 8.8.8.8

# Binance erişimini test et
curl -I https://api.binance.com/api/v3/ping
```

### Dosya İzin Sorunları:
```bash
# Data klasörü oluştur
mkdir -p data

# İzinleri düzelt
chmod 755 data/
```

### WebSocket Client Manuel Test:
```python
from binance_websocket_client import BinanceWebSocketClient

client = BinanceWebSocketClient(["btcusdt"], "test.jsonl")
client.start()

# Çalışırsa göreceksin:
# INFO:__main__:WebSocket connection opened
# 🚀 PUMP ALERT: BTCUSDT +3.27% in last 5 ticks
```

## ⚡ Performans İpuçları

### 1. CPU Kullanımı:
- WebSocket client minimum CPU kullanır
- Ana sistem sadece belirli zamanlarda analiz yapar
- Enhanced monitor 10 saniyede bir güncellenir

### 2. Bellek Kullanımı:
- WebSocket client ~10-20MB
- Ana sistem ~50-100MB
- Monitor ~10-15MB

### 3. Disk Kullanımı:
- `crypto_feed.jsonl` sürekli büyür
- Günde yaklaşık 50-100MB log
- Eski logları temizlemek için:
```bash
# Son 1000 satırı tut
tail -n 1000 crypto_feed.jsonl > temp && mv temp crypto_feed.jsonl
```

## 🎯 Kullanım Senaryoları

### Günlük Trader:
1. Sabah ana sistemi başlat (`python main.py`)
2. Enhanced monitor aç (`python monitor_results_enhanced.py`)
3. Real-time fiyatları ve sinyalleri takip et
4. Pump alert'lerine dikkat et

### Geliştirici:
1. Sadece WebSocket test et (`python binance_websocket_client.py`)
2. Log dosyalarını analiz et
3. Kendi analizlerini ekle

### Araştırmacı:
1. Veri topla (bir gün boyunca çalıştır)
2. `crypto_feed.jsonl` dosyasını analiz et
3. Pump pattern'lerini incele

## 📞 Destek

Sorun yaşarsan:
1. `data/system.log` dosyasını kontrol et
2. WebSocket bağlantı durumunu kontrol et
3. API key'lerin doğru olduğunu kontrol et

## 🎉 Başarılı Çalışma Örneği

Sistemi doğru çalıştırdığında göreceğin çıktı:

```
===============================================================================
🔍 CRYPTO AI ANALYZER - ENHANCED LIVE MONITORING
===============================================================================
🕒 Last Updated: 2024-01-15 14:30:25
🟢 WebSocket Status: CONNECTED

💹 LIVE PRICES (WebSocket):
🔺 BTCUSDT: $42,350.2340 (+0.125%)
🔻 ETHUSDT: $2,580.4520 (-0.087%)
🔺 SOLUSDT: $98.7650 (+0.234%)

📡 LIVE FEED ACTIVITY (last 15 ticks):
📊 BTCUSDT: 6 ticks, Latest: $42,350.2340 at 14:30:24
📊 ETHUSDT: 5 ticks, Latest: $2,580.4520 at 14:30:23
📊 SOLUSDT: 4 ticks, Latest: $98.7650 at 14:30:25

🎯 LATEST SIGNALS (last 3):
🟡 BTCUSDT: WAIT (conf: 0.65) [14:28:15]
   💬 Consolidation phase with 0.1% change. Wait for clear direction...
```

**Başarılar! 🚀** 
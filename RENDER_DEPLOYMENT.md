# 🚀 Render.com Deployment Rehberi

Bu rehber Crypto AI Analyzer'ı Render.com'da nasıl deploy edeceğinizi açıklar.

## 📋 Ön Gereksinimler

1. **GitHub Repository**: Kodunuz GitHub'da olmalı
2. **Render.com Hesabı**: [render.com](https://render.com) ücretsiz hesap
3. **API Keys**: Aşağıdaki API anahtarları

## 🔑 Gerekli API Keys

### 1. OpenAI API Key (Opsiyonel)
- [OpenAI Platform](https://platform.openai.com/api-keys) adresinden alın
- Format: `sk-...`

### 2. Claude API Key (Opsiyonel) 
- [Anthropic Console](https://console.anthropic.com/) adresinden alın
- Format: `sk-ant-...`

### 3. Telegram Bot Token (Zorunlu)
- [@BotFather](https://t.me/botfather) ile bot oluşturun
- Format: `123456789:ABC...`

### 4. Telegram Chat ID (Zorunlu)
- [@userinfobot](https://t.me/userinfobot) ile chat ID alın
- Format: `-100123456789` (grup için) veya `123456789` (kişisel)

## 🔧 Render.com Ayarları

### 1. Web Service Oluşturma

Render Dashboard'da:

```
Name: crypto-ai-analyzer
Language: Python 3
Branch: master
Build Command: pip install -r requirements.txt
Start Command: gunicorn main:app
```

### 2. Environment Variables

Render Dashboard → Environment sekmesinde şu değişkenleri ekleyin:

```bash
# Zorunlu - Telegram
TELEGRAM_BOT_TOKEN=123456789:ABC...
TELEGRAM_CHAT_ID=-100123456789

# Opsiyonel - AI Models (en az birini ekleyin)
OPENAI_API_KEY=sk-...
CLAUDE_API_KEY=sk-ant-...

# Sistem
PYTHON_VERSION=3.11.5
PORT=10000
```

### 3. Render Ayarları

```
Region: Oregon (US West)
Plan: Free (başlangıç için yeterli)
Auto-Deploy: Yes
```

## 📡 Endpoints

Deploy sonrası erişilebilir endpoints:

- `GET /` - Ana sayfa ve sistem bilgisi
- `GET /health` - Sağlık kontrolü
- `GET /signals` - İngilizce trading sinyalleri
- `GET /signals/turkish` - 🇹🇷 Türkçe trading sinyalleri
- `GET /status` - Sistem durumu
- `GET /market-data` - Piyasa verileri

## 🇹🇷 Türkçe Sinyal Formatı

Sistem otomatik olarak şu formatta Türkçe sinyaller üretir:

```
🚦 AL/SAT SİNYALLERİ

1️⃣ BTCUSDT 🟢
• AL: 48.500 - 49.200 (Limit)
• SAT: 51.000 - 52.000
• Stop-Loss: 47.800
• Take-Profit: 51.500
• Güven: 0.85 (Yüksek)
• Öncelik: Yüksek
• Geçerlilik: 4 saat
• RSI: 68 | MACD: Pozitif
• Haber Etkisi: Pozitif (ETF haberi)
• Sentiment: %70 olumlu
• Önerilen Pozisyon: %10 portföy
• Risk Uyarısı: Yüksek volatilite, risk yönetimi önemli
• Alternatif: 47.800 altı kapanışta sinyal geçersiz
• Geçmiş Sinyal Başarısı: Son 3/3 başarılı
• TL;DR: 48.500-49.200 al, 51.500 sat, stop 47.800, risk yüksek.
• Gerekçe: Güçlü hacim ve momentum
```

## 🔄 Otomatik İşlevler (CANLI VERİ İLE)

Deploy sonrası sistem otomatik olarak **SADECE CANLI VERİLERLE** çalışır:

1. **Saatlik Telegram Bildirimi** 🕐 (Her saat başı)
2. **Günlük Analiz** (08:00 UTC) 
3. **Anomaly Tarama** (30 dakikada bir)
4. **Haber Analizi** (4 saatte bir)
5. **Makro Sentiment Analizi** (6 saatte bir)
6. **Türkçe Sinyal Cache** (sürekli güncel)

**⚠️ ÖNEMLİ: Sistem sadece canlı market verileri kullanır. Mock/test verisi ASLA kullanılmaz!**

## ✅ Deployment Kontrolü

Deploy sonrası kontrol edin:

1. **Health Check**: `https://your-app.onrender.com/health`
2. **Türkçe Sinyaller**: `https://your-app.onrender.com/signals/turkish`
3. **Logs**: Render Dashboard → Logs sekmesi
4. **Telegram**: Bot'unuza `/start` yazın

## 🐛 Hata Giderme

### Deployment Hatası
- Requirements.txt'i kontrol edin
- Python version uyumluluğu (3.11.5)
- Build logs'u inceleyin

### API Hatası
- Environment variables doğru mu?
- API key'ler geçerli mi?
- Network connectivity var mı?

### Telegram Hatası
- Bot token doğru mu?
- Chat ID doğru format mı?
- Bot grup/kanala eklenmiş mi?

## 📞 Destek

Sorun yaşıyorsanız:
1. Render logs'u kontrol edin
2. `/health` endpoint'ini test edin
3. Environment variables'ı doğrulayın

## 💡 Önemli Notlar

- **Free Plan**: 750 saat/ay (yeterli)
- **Sleep Mode**: 15 dakika inaktivite sonrası uyur
- **Cold Start**: İlk istek 10-30 saniye sürebilir
- **Disk Space**: Geçici, restart'ta sıfırlanır
- **Memory**: 512MB limit (yeterli)

## 🚀 İleriki Adımlar

1. **Custom Domain** ekleyin
2. **Paid Plan** ile sürekli aktif tutun
3. **Monitoring** ekleyin (UptimeRobot vb.)
4. **Database** entegrasyonu (PostgreSQL)
5. **Redis Cache** ekleyin

---

**✨ Başarılı deployment için tüm environment variables'ı doğru ayarladığınızdan emin olun!** 
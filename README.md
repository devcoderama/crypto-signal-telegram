# Crypto Trading Bot

Sistem bot trading cryptocurrency yang modular dengan analisis teknikal real-time dan notifikasi Telegram.

## Fitur Utama

🤖 **Bot Telegram Interaktif**

- Command-based interface dengan inline keyboards
- Interactive session untuk input market dan timeframe
- Real-time notifications untuk TP/SL hits

📊 **Analisis Market Komprehensif**

- Data market dari TradingView dan Yahoo Finance (tanpa API key)
- 15+ indikator teknikal (RSI, MACD, Bollinger Bands, Stochastic, etc.)
- Sinyal trading otomatis dengan confidence level
- Dynamic TP/SL calculation berdasarkan ATR

📈 **Position Monitoring**

- Real-time tracking posisi trading
- Automatic TP/SL detection dan notifikasi
- PnL calculation dan monitoring
- Database SQLite untuk persistensi data

🔔 **Price Alerts**

- Custom price alerts per user
- Above/below condition support
- Automatic alert triggering dan notifications

⚙️ **User Settings**

- Customizable risk percentage
- Preferred timeframe settings
- Notification preferences
- Maximum positions limit

## Struktur Project

```
crypto_trading_bot/
├── main.py                 # Main launcher
├── telegram_bot.py         # Telegram bot dengan Telethon
├── market_analysis.py      # Engine analisis market
├── position_monitor.py     # Position tracking dan database
├── requirements.txt        # Python dependencies
├── .env                    # Configuration file
├── start_bot.sh           # Shell script launcher
└── trading_bot.db         # SQLite database (auto-created)
```

## Installation

### 1. Setup Environment

```bash
# Clone atau download project files
cd crypto_trading_bot

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Telegram Bot Setup

1. **Buat Bot Telegram:**

   - Chat dengan @BotFather di Telegram
   - Gunakan `/newbot` untuk membuat bot baru
   - Simpan Bot Token yang diberikan

2. **Dapatkan API Credentials:**

   - Kunjungi https://my.telegram.org/apps
   - Login dengan akun Telegram
   - Create new application
   - Simpan API ID dan API Hash

3. **Configuration:**

   ```bash
   # Copy dan edit file .env
   cp .env.example .env
   nano .env
   ```

   Isi dengan credentials Anda:

   ```env
   API_ID=your_telegram_api_id
   API_HASH=your_telegram_api_hash
   BOT_TOKEN=your_bot_token

   # Trading Configuration
   DEFAULT_RISK_PERCENTAGE=2.0
   DEFAULT_REWARD_RATIO=2.0
   MAX_POSITIONS=5
   ANALYSIS_INTERVAL=300
   ENABLE_NOTIFICATIONS=true
   ```

## Usage

### Menjalankan Bot

```bash
# Method 1: Python script
python3 main.py

# Method 2: Shell script
chmod +x start_bot.sh
./start_bot.sh

# Method 3: Background process
nohup python3 main.py > bot.log 2>&1 &
```

### Telegram Commands

- `/start` - Mulai menggunakan bot
- `/analyze [SYMBOL] [TIMEFRAME]` - Analisis market
- `/positions` - Lihat posisi trading aktif
- `/alerts` - Kelola price alerts
- `/settings` - Pengaturan bot
- `/help` - Bantuan penggunaan

### Interactive Usage

1. **Market Analysis:**

   ```
   /analyze BTC 1h
   ```

   atau gunakan interactive mode:

   ```
   /analyze
   > BTC
   > 1h
   ```

2. **Position Monitoring:**

   - Bot secara otomatis monitor posisi setiap 30 detik
   - Notification dikirim saat TP/SL terpicu
   - View posisi aktif dengan `/positions`

3. **Price Alerts:**
   ```
   /alerts
   > Add Alert
   > BTC
   > 52000
   > Above
   ```

## Technical Indicators

Bot menggunakan library `ta` untuk menghitung indikator:

- **Momentum:** RSI, Stochastic, Williams %R
- **Trend:** MACD, Moving Averages (SMA/EMA), ADX
- **Volatility:** Bollinger Bands, ATR
- **Volume:** OBV, Volume SMA

## Signal Generation Logic

```python
# Contoh logic sinyal LONG
if (rsi < 30 and
    macd > macd_signal and
    price > sma_20 and
    price <= bb_lower):
    signal = "LONG"
    confidence = calculate_confidence(indicators)
```

## Database Schema

### Positions Table

```sql
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,
    take_profit REAL NOT NULL,
    stop_loss REAL NOT NULL,
    status TEXT DEFAULT 'OPEN',
    pnl_percentage REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Price Alerts Table

```sql
CREATE TABLE price_alerts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    target_price REAL NOT NULL,
    condition TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1
);
```

## Troubleshooting

### Common Issues

1. **Import Error - pandas/numpy:**

   ```bash
   # Untuk macOS dengan Apple Silicon
   pip install --upgrade pip
   pip install numpy pandas --no-cache-dir

   # Atau gunakan conda
   conda install pandas numpy
   ```

2. **Telethon Session Error:**

   ```bash
   # Hapus file session dan restart
   rm trading_bot.session
   python3 main.py
   ```

3. **Database Locked:**
   ```bash
   # Restart bot, database akan auto-recover
   pkill -f main.py
   python3 main.py
   ```

### Logs

```bash
# View real-time logs
tail -f trading_bot.log

# Search for errors
grep ERROR trading_bot.log

# Monitor position updates
grep "Position" trading_bot.log
```

## Development

### Testing Components

```bash
# Test market analysis
python3 -c "from market_analysis import *; asyncio.run(test_analysis())"

# Test position monitor
python3 -c "from position_monitor import *; asyncio.run(test_position_monitor())"

# Test telegram bot components
python3 test_bot.py
```

### Adding New Indicators

1. Edit `market_analysis.py`
2. Add indicator calculation in `calculate_technical_indicators()`
3. Add signal logic in `generate_trading_signal()`
4. Update confidence calculation

### Custom Notifications

Customize notification messages in `telegram_bot.py`:

```python
def _format_signal_message(self, signal):
    # Customize message format here
    pass
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Tidak menggunakan API Exchange:**

   - Bot menggunakan data publik dari TradingView/Yahoo Finance
   - Tidak ada akses ke akun trading Anda
   - Hanya memberikan sinyal, bukan execute trades

2. **Telegram Bot Token:**

   - Jangan share Bot Token Anda
   - Gunakan environment variables, bukan hardcode
   - Regenerate token jika terkompromi

3. **Database Security:**
   - Database SQLite disimpan lokal
   - Backup secara berkala
   - Tidak berisi informasi finansial sensitif

## Disclaimer

🚨 **Trading Disclaimer:**

Bot ini hanya memberikan sinyal analisis teknikal untuk tujuan edukasi. Keputusan trading sepenuhnya tanggung jawab Anda. Selalu lakukan riset sendiri (DYOR) sebelum melakukan trading.

- Bot tidak mengeksekusi trades otomatis
- Sinyal tidak menjamin profit
- Market cryptocurrency sangat volatile
- Gunakan risk management yang tepat

## Support

Untuk pertanyaan atau bantuan:

- Create issue di repository
- Join Telegram group: @your_support_group
- Email: support@yourbot.com

## License

MIT License - Silakan gunakan dan modifikasi sesuai kebutuhan.

---

**Happy Trading! 🚀**

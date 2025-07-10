"""
Config module for the modular crypto trading bot.
Contains all configuration constants and settings.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_NAME = "🚀 Crypto Trading Assistant"
BOT_VERSION = "2.0.0"

# Message Templates
WELCOME_MESSAGE = """
🚀 **Selamat datang di Crypto Trading Assistant!**

Bot ini membantu Anda menganalisis pasar crypto dengan data real-time dari TradingView dan memberikan sinyal trading otomatis.

**Fitur Utama:**
📊 Analisis teknikal (RSI, MACD, MA, BB)
🎯 Sinyal Long/Short otomatis  
⚡ Take Profit & Stop Loss
🔔 Price alerts
📈 Monitor posisi real-time
📱 Notifikasi Telegram

Gunakan /help untuk melihat semua command yang tersedia!
"""

HELP_MESSAGE = """
📚 **PANDUAN PENGGUNAAN BOT**

**🔧 Command Utama:**
/start - Mulai menggunakan bot
/analyze - Analisis symbol crypto
/positions - Lihat posisi aktif
/alerts - Kelola price alerts
/settings - Pengaturan bot
/help - Panduan ini

**📊 Fitur Analisis:**
• Pilih symbol (BTC, ETH, ADA, dll)
• Pilih timeframe (1m, 5m, 15m, 1h, 4h, 1d)
• Dapatkan sinyal Long/Short otomatis
• Rekomendasi TP/SL berdasarkan analisis

**⚙️ Pengaturan:**
• Risk management
• Notifikasi alerts
• Default timeframe

**📱 Notifikasi Real-time:**
• Signal baru tersedia
• TP/SL tercapai
• Price alerts triggered

Ketik /analyze untuk mulai analisis!
"""

# Trading Symbols
SUPPORTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT",
    "SOLUSDT", "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "LUNAUSDT",
    "MATICUSDT", "LINKUSDT", "LTCUSDT", "UNIUSDT", "ATOMUSDT",
    "FTMUSDT", "AXSUSDT", "SANDUSDT", "MANAUSDT", "GALAUSDT"
]

# Timeframes
SUPPORTED_TIMEFRAMES = [
    "1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"
]

# Technical Analysis Settings
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

MA_SHORT = 20
MA_LONG = 50

BOLLINGER_PERIOD = 20
BOLLINGER_STD = 2

# Risk Management
DEFAULT_RISK_PERCENTAGE = 2.0
DEFAULT_REWARD_RATIO = 2.0
MAX_POSITIONS_PER_USER = 5

# Database Tables
USERS_TABLE = "users"
POSITIONS_TABLE = "positions"
ALERTS_TABLE = "alerts"
SIGNALS_TABLE = "signals_history"
BROADCASTS_TABLE = "broadcasts"
INTERACTIONS_TABLE = "user_interactions"

# Environment Variables with Defaults
def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable with default value."""
    return os.getenv(key, default)

# Load environment variables
API_ID = int(get_env_var("API_ID", "0"))
API_HASH = get_env_var("API_HASH")
BOT_TOKEN = get_env_var("BOT_TOKEN")
ADMIN_ID = int(get_env_var("ADMIN_ID", "0"))

DATABASE_PATH = get_env_var("DATABASE_PATH", "crypto_bot.db")
LOG_LEVEL = get_env_var("LOG_LEVEL", "INFO")
LOG_FILE = get_env_var("LOG_FILE", "crypto_bot.log")

# Validation
if not all([API_ID, API_HASH, BOT_TOKEN, ADMIN_ID]):
    raise ValueError("Missing required environment variables in .env file")

# Admin Commands
ADMIN_COMMANDS = [
    "/admin - Panel admin",
    "/broadcast - Broadcast ke semua user",
    "/stats - Statistik bot",
    "/users - Daftar user aktif"
]

# Button Texts
BUTTON_ANALYZE = "📊 Analisis Symbol"
BUTTON_POSITIONS = "📈 Posisi Saya"
BUTTON_ALERTS = "🔔 Price Alerts"
BUTTON_SETTINGS = "⚙️ Pengaturan"
BUTTON_HELP = "❓ Bantuan"

BUTTON_LONG = "🟢 LONG"
BUTTON_SHORT = "🔴 SHORT"
BUTTON_CLOSE = "❌ Close Posisi"

BUTTON_SET_TP = "🎯 Set Take Profit"
BUTTON_SET_SL = "🛡️ Set Stop Loss"
BUTTON_ADD_ALERT = "➕ Tambah Alert"
BUTTON_REMOVE_ALERT = "➖ Hapus Alert"

# Messages
MSG_CHOOSE_SYMBOL = "📊 Pilih symbol crypto untuk dianalisis:"
MSG_CHOOSE_TIMEFRAME = "⏰ Pilih timeframe untuk analisis:"
MSG_ANALYSIS_LOADING = "⏳ Sedang menganalisis... Mohon tunggu sebentar."
MSG_NO_POSITIONS = "📈 Anda belum memiliki posisi aktif."
MSG_NO_ALERTS = "🔔 Anda belum memiliki price alerts."

# Error Messages
ERROR_SYMBOL_NOT_FOUND = "❌ Symbol tidak ditemukan atau tidak didukung."
ERROR_INVALID_TIMEFRAME = "❌ Timeframe tidak valid."
ERROR_ANALYSIS_FAILED = "❌ Gagal menganalisis data. Silakan coba lagi."
ERROR_ADMIN_ONLY = "❌ Command ini hanya untuk admin."
ERROR_INVALID_INPUT = "❌ Input tidak valid. Silakan coba lagi."

# Success Messages
SUCCESS_POSITION_OPENED = "✅ Posisi berhasil dibuka!"
SUCCESS_POSITION_CLOSED = "✅ Posisi berhasil ditutup!"
SUCCESS_ALERT_ADDED = "✅ Price alert berhasil ditambahkan!"
SUCCESS_ALERT_REMOVED = "✅ Price alert berhasil dihapus!"
SUCCESS_BROADCAST_SENT = "✅ Broadcast berhasil dikirim!"

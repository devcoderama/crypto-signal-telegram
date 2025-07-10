#!/bin/bash

echo "🚀 Starting Modular Crypto Trading Bot..."

# Check if virtual environment exists
if [ ! -d "came_venv" ]; then
    echo "❌ Virtual environment 'came_venv' not found!"
    echo "Creating virtual environment..."
    python3 -m venv came_venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source came_venv/bin/activate

# Install/update requirements
echo "📦 Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements_new.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please ensure .env file exists with your credentials"
    exit 1
fi

# Validate credentials in .env
if ! grep -q "API_ID=" .env || ! grep -q "API_HASH=" .env || ! grep -q "BOT_TOKEN=" .env; then
    echo "❌ Missing credentials in .env file!"
    echo "Please ensure API_ID, API_HASH, and BOT_TOKEN are set"
    exit 1
fi

# Check if main bot file exists
if [ ! -f "bot.py" ]; then
    echo "❌ bot.py not found!"
    exit 1
fi

echo "✅ All checks passed!"
echo "🤖 Starting Crypto Trading Bot..."
echo "📱 Bot will handle:"
echo "   • Market analysis from TradingView"
echo "   • Trading signals with TP/SL"
echo "   • Position monitoring"
echo "   • Price alerts"
echo "   • Admin broadcast system"
echo ""
echo "👤 Admin ID: 7300772742"
echo "🔧 Press Ctrl+C to stop the bot"
echo "============================================"

# Run the bot
python3 bot.py

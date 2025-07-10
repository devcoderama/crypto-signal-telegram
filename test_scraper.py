#!/usr/bin/env python3
"""
Test script for TradingView scraper
"""

import asyncio
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.tradingview_scraper import TradingViewScraper

async def test_scraper():
    print("🧪 Testing Binance API connection...")
    
    async with TradingViewScraper() as scraper:
        # Test BTCUSDT
        data = await scraper.get_market_data('BTCUSDT', '1h')
        
        if data:
            print(f"✅ Success: {data['symbol']} = ${data['price']['current']:,.2f}")
            print(f"📈 24h Change: {data['price']['change']:+.2f}%")
            print(f"📊 Volume: {data['volume']:,.0f}")
            print(f"🔍 Data source: {'Real API' if data['price']['current'] > 100000 else 'Mock data'}")
        else:
            print("❌ Failed to get data")

if __name__ == "__main__":
    asyncio.run(test_scraper())

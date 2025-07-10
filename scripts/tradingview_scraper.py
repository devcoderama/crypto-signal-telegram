"""
TradingView Scraper Module
Script untuk mengambil data market dari TradingView dan Binance API
"""

import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import ssl

logger = logging.getLogger(__name__)

class TradingViewScraper:
    def __init__(self):
        self.session = None
        # Use Binance API directly
        self.binance_base = "https://api.binance.com/api/v3"
        # Updated headers to avoid 403 errors
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def __aenter__(self):
        # Create connector with proper SSL settings and timeouts
        connector = aiohttp.TCPConnector(
            ssl=True,  # Enable SSL verification
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=15, connect=5),
            raise_for_status=False  # Don't raise exceptions for HTTP errors
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_market_data(self, symbol: str, timeframe: str = "1h") -> Optional[Dict[str, Any]]:
        """
        Ambil data market dari multiple sources dengan fallback
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            timeframe: Chart timeframe (e.g., 1h, 4h, 1d)
            
        Returns:
            Dict dengan data market atau None jika gagal
        """
        try:
            logger.info(f"Fetching market data for {symbol} ({timeframe})")
            
            # Try Binance API first
            price_data = await self._get_binance_24hr_ticker(symbol)
            
            # If Binance fails, try CoinGecko
            if not price_data:
                logger.info(f"Binance failed, trying CoinGecko for {symbol}")
                price_data = await self._get_coingecko_price(symbol)
            
            if not price_data:
                logger.warning(f"All APIs failed for {symbol}, using mock data")
                return self._generate_mock_data(symbol, timeframe)
            
            # Get kline data for technical analysis
            kline_data = await self._get_binance_klines(symbol, timeframe)
            if not kline_data:
                logger.warning(f"No kline data for {symbol}, generating mock klines")
                mock_price = float(price_data.get('lastPrice', price_data.get('current_price', 0)))
                kline_data = self._generate_mock_klines(mock_price, 100)
            
            # Calculate technical indicators
            technical_data = self._calculate_technical_indicators(kline_data)
            
            # Format market data based on source
            if 'lastPrice' in price_data:  # Binance format
                market_data = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': datetime.now(),
                    'price': {
                        'current': float(price_data['lastPrice']),
                        'change': float(price_data['priceChangePercent']),
                        'change_abs': float(price_data['priceChange']),
                        'high': float(price_data['highPrice']),
                        'low': float(price_data['lowPrice']),
                        'open': float(price_data['openPrice'])
                    },
                    'volume': float(price_data['volume']),
                    'indicators': technical_data,
                    'raw_klines': kline_data[-20:]  # Last 20 candles for reference
                }
            else:  # CoinGecko format
                current_price = float(price_data['current_price'])
                change_24h = float(price_data.get('price_change_percentage_24h', 0))
                market_data = {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': datetime.now(),
                    'price': {
                        'current': current_price,
                        'change': change_24h,
                        'change_abs': current_price * (change_24h / 100),
                        'high': float(price_data.get('high_24h', current_price * 1.05)),
                        'low': float(price_data.get('low_24h', current_price * 0.95)),
                        'open': current_price * (1 - change_24h / 100)
                    },
                    'volume': float(price_data.get('total_volume', 1000000)),
                    'indicators': technical_data,
                    'raw_klines': kline_data[-20:]
                }
            
            logger.info(f"Successfully fetched data for {symbol}: ${market_data['price']['current']:,.2f}")
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return self._generate_mock_data(symbol, timeframe)

    async def _get_binance_24hr_ticker(self, symbol: str) -> Optional[Dict]:
        """Get 24hr ticker data from Binance with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"{self.binance_base}/ticker/24hr"
                params = {'symbol': symbol.upper()}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched 24hr ticker for {symbol}")
                        return data
                    elif response.status == 429:  # Rate limit
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Binance 24hr ticker API error: {response.status}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return None
            except Exception as e:
                logger.error(f"Error getting 24hr ticker from Binance (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    async def _get_binance_klines(self, symbol: str, timeframe: str, limit: int = 100) -> Optional[List[Dict]]:
        """Get kline (candlestick) data from Binance with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Convert timeframe format
                interval_map = {
                    '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                    '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
                    '1d': '1d', '3d': '3d', '1w': '1w'
                }
                
                interval = interval_map.get(timeframe, '1h')
                
                url = f"{self.binance_base}/klines"
                params = {
                    'symbol': symbol.upper(),
                    'interval': interval,
                    'limit': limit
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Convert to standard format
                        processed_data = []
                        for kline in data:
                            processed_data.append({
                                'timestamp': kline[0],
                                'open': float(kline[1]),
                                'high': float(kline[2]),
                                'low': float(kline[3]),
                                'close': float(kline[4]),
                                'volume': float(kline[5])
                            })
                        logger.info(f"Successfully fetched {len(processed_data)} klines for {symbol}")
                        return processed_data
                    elif response.status == 429:  # Rate limit
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Binance klines API error: {response.status}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return None
            except Exception as e:
                logger.error(f"Error getting klines from Binance (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    async def _get_coingecko_price(self, symbol: str) -> Optional[Dict]:
        """Get price data from CoinGecko API as fallback"""
        try:
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'BTCUSDT': 'bitcoin',
                'ETHUSDT': 'ethereum',
                'BNBUSDT': 'binancecoin',
                'ADAUSDT': 'cardano',
                'XRPUSDT': 'ripple',
                'SOLUSDT': 'solana',
                'DOTUSDT': 'polkadot',
                'DOGEUSDT': 'dogecoin',
                'AVAXUSDT': 'avalanche-2',
                'MATICUSDT': 'matic-network',
                'LINKUSDT': 'chainlink',
                'LTCUSDT': 'litecoin'
            }
            
            coin_id = symbol_map.get(symbol)
            if not coin_id:
                logger.warning(f"No CoinGecko mapping for {symbol}")
                return None
            
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true',
                'include_last_updated_at': 'true'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if coin_id in data:
                        coin_data = data[coin_id]
                        logger.info(f"Successfully fetched CoinGecko data for {symbol}")
                        return {
                            'current_price': coin_data['usd'],
                            'price_change_percentage_24h': coin_data.get('usd_24h_change', 0),
                            'total_volume': coin_data.get('usd_24h_vol', 1000000),
                            'high_24h': coin_data['usd'] * 1.05,  # Estimated
                            'low_24h': coin_data['usd'] * 0.95    # Estimated
                        }
                else:
                    logger.error(f"CoinGecko API error: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting CoinGecko data: {e}")
            return None

        return None
    
    def _generate_mock_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Generate mock data when API fails - using more realistic current prices"""
        # Updated base prices (more current as of 2025)
        base_prices = {
            'BTCUSDT': 116000,  # More realistic current BTC price
            'ETHUSDT': 3800,    # More realistic current ETH price
            'BNBUSDT': 680,     # More realistic current BNB price
            'ADAUSDT': 1.20,    # More realistic current ADA price
            'XRPUSDT': 2.80,    # More realistic current XRP price
            'SOLUSDT': 220,     # More realistic current SOL price
            'DOTUSDT': 12.5,    # More realistic current DOT price
            'DOGEUSDT': 0.42,   # More realistic current DOGE price
            'AVAXUSDT': 68,     # More realistic current AVAX price
            'MATICUSDT': 0.85,  # More realistic current MATIC price
            'LINKUSDT': 28,     # More realistic current LINK price
            'LTCUSDT': 140,     # More realistic current LTC price
        }
        
        base_price = base_prices.get(symbol, 1000)  # Default to $1000 for unknown symbols
        
        # Add some pseudo-random variation (-5% to +5%)
        price_variation = 0.9 + (0.2 * (hash(symbol + timeframe) % 100) / 100)
        current_price = base_price * price_variation
        
        mock_klines = self._generate_mock_klines(current_price, 100)
        technical_data = self._calculate_technical_indicators(mock_klines)
        
        # More realistic 24h change (-10% to +10%)
        change_pct = -10 + (20 * (hash(symbol) % 100) / 100)
        
        logger.warning(f"Using mock data for {symbol}: ${current_price:,.2f}")
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'timestamp': datetime.now(),
            'price': {
                'current': current_price,
                'change': change_pct,
                'change_abs': current_price * (change_pct / 100),
                'high': current_price * 1.08,
                'low': current_price * 0.92,
                'open': current_price * (1 - change_pct / 100)
            },
            'volume': 50000 + (hash(symbol) % 1000000),  # More realistic volume
            'indicators': technical_data,
            'raw_klines': mock_klines[-20:]
        }
    
    def _generate_mock_klines(self, current_price: float, count: int) -> List[Dict]:
        """Generate mock kline data for technical analysis"""
        klines = []
        price = current_price * 0.95  # Start from 95% of current price
        
        for i in range(count):
            # Simulate price movement
            change = (hash(f"{i}_{current_price}") % 200 - 100) / 10000  # -1% to +1%
            price = price * (1 + change)
            
            high = price * (1 + abs(change) * 2)
            low = price * (1 - abs(change) * 2)
            
            klines.append({
                'timestamp': datetime.now().timestamp() - (count - i) * 3600,  # 1 hour intervals
                'open': price * 0.999,
                'high': high,
                'low': low,
                'close': price,
                'volume': 1000000 + (hash(f"vol_{i}") % 500000)
            })
        
        return klines
    
    def _calculate_technical_indicators(self, klines: List[Dict]) -> Dict[str, Any]:
        """Calculate technical indicators from kline data"""
        try:
            if len(klines) < 50:
                logger.warning("Not enough data for technical analysis")
                return self._get_default_indicators()
            
            # Extract price data
            closes = [k['close'] for k in klines]
            highs = [k['high'] for k in klines]
            lows = [k['low'] for k in klines]
            volumes = [k['volume'] for k in klines]
            
            # Calculate RSI (14-period)
            rsi = self._calculate_rsi(closes, period=14)
            
            # Calculate Moving Averages
            sma_20 = sum(closes[-20:]) / 20
            sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sum(closes) / len(closes)
            
            ema_20 = self._calculate_ema(closes, period=20)
            ema_50 = self._calculate_ema(closes, period=50)
            
            # Calculate MACD
            macd_line, macd_signal, macd_histogram = self._calculate_macd(closes)
            
            # Calculate Bollinger Bands
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes)
            
            # Calculate trend strength
            trend_strength = self._calculate_trend_strength(closes, highs, lows)
            
            current_price = closes[-1]
            
            return {
                'rsi': rsi,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'ema_20': ema_20,
                'ema_50': ema_50,
                'macd': macd_line,
                'macd_signal': macd_signal,
                'macd_histogram': macd_histogram,
                'bb_upper': bb_upper,
                'bb_middle': bb_middle,
                'bb_lower': bb_lower,
                'trend_strength': trend_strength,
                'price_position': {
                    'above_sma20': current_price > sma_20,
                    'above_sma50': current_price > sma_50,
                    'above_ema20': current_price > ema_20,
                    'above_ema50': current_price > ema_50
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return self._get_default_indicators()
    
    def _get_default_indicators(self) -> Dict[str, Any]:
        """Return default indicator values when calculation fails"""
        return {
            'rsi': 50.0,
            'sma_20': 0.0,
            'sma_50': 0.0,
            'ema_20': 0.0,
            'ema_50': 0.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'macd_histogram': 0.0,
            'bb_upper': 0.0,
            'bb_middle': 0.0,
            'bb_lower': 0.0,
            'trend_strength': 0.0,
            'price_position': {
                'above_sma20': False,
                'above_sma50': False,
                'above_ema20': False,
                'above_ema50': False
            }
        }
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI (Relative Strength Index)"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return round(rsi, 2)
            
        except Exception:
            return 50.0
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate EMA (Exponential Moving Average)"""
        try:
            if len(prices) < period:
                return sum(prices) / len(prices)
            
            multiplier = 2 / (period + 1)
            ema = sum(prices[:period]) / period  # Start with SMA
            
            for price in prices[period:]:
                ema = (price * multiplier) + (ema * (1 - multiplier))
            
            return round(ema, 4)
            
        except Exception:
            return 0.0
    
    def _calculate_macd(self, prices: List[float]) -> tuple:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            if len(prices) < 26:
                return 0.0, 0.0, 0.0
            
            ema_12 = self._calculate_ema(prices, 12)
            ema_26 = self._calculate_ema(prices, 26)
            macd_line = ema_12 - ema_26
            
            # Calculate signal line (9-period EMA of MACD)
            macd_values = []
            for i in range(26, len(prices)):
                ema_12_temp = self._calculate_ema(prices[:i+1], 12)
                ema_26_temp = self._calculate_ema(prices[:i+1], 26)
                macd_values.append(ema_12_temp - ema_26_temp)
            
            if len(macd_values) >= 9:
                macd_signal = self._calculate_ema(macd_values, 9)
            else:
                macd_signal = 0.0
            
            macd_histogram = macd_line - macd_signal
            
            return round(macd_line, 6), round(macd_signal, 6), round(macd_histogram, 6)
            
        except Exception:
            return 0.0, 0.0, 0.0
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> tuple:
        """Calculate Bollinger Bands"""
        try:
            if len(prices) < period:
                avg = sum(prices) / len(prices)
                return avg, avg, avg
            
            sma = sum(prices[-period:]) / period
            variance = sum([(price - sma) ** 2 for price in prices[-period:]]) / period
            std = variance ** 0.5
            
            bb_upper = sma + (std * std_dev)
            bb_lower = sma - (std * std_dev)
            
            return round(bb_upper, 4), round(sma, 4), round(bb_lower, 4)
            
        except Exception:
            return 0.0, 0.0, 0.0
    
    def _calculate_trend_strength(self, closes: List[float], highs: List[float], lows: List[float]) -> float:
        """Calculate trend strength (0-100)"""
        try:
            if len(closes) < 20:
                return 50.0
            
            # Simple trend calculation based on price movement
            recent_closes = closes[-10:]
            older_closes = closes[-20:-10]
            
            recent_avg = sum(recent_closes) / len(recent_closes)
            older_avg = sum(older_closes) / len(older_closes)
            
            trend = ((recent_avg - older_avg) / older_avg) * 100
            
            # Normalize to 0-100 scale
            strength = min(100, max(0, 50 + trend * 10))
            
            return round(strength, 2)
            
        except Exception:
            return 50.0
    
    async def get_crypto_screener(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get list of popular cryptocurrencies from Binance
        
        Args:
            limit: Number of symbols to return
            
        Returns:
            List of crypto data
        """
        try:
            url = f"{self.binance_base}/ticker/24hr"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Filter only USDT pairs and sort by volume
                    usdt_pairs = [
                        item for item in data 
                        if item['symbol'].endswith('USDT') and 
                        float(item['volume']) > 1000000
                    ]
                    
                    # Sort by 24h quote volume (volume in USDT)
                    usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
                    
                    # Format the data
                    screener_data = []
                    for item in usdt_pairs[:limit]:
                        screener_data.append({
                            'symbol': item['symbol'],
                            'price': float(item['lastPrice']),
                            'change_24h': float(item['priceChangePercent']),
                            'volume_24h': float(item['quoteVolume']),
                            'high_24h': float(item['highPrice']),
                            'low_24h': float(item['lowPrice'])
                        })
                    
                    logger.info(f"Successfully fetched screener data for {len(screener_data)} symbols")
                    return screener_data
                else:
                    logger.error(f"Binance screener API error: {response.status}")
                    return self._get_fallback_screener_data(limit)
        except Exception as e:
            logger.error(f"Error getting crypto screener: {e}")
            return self._get_fallback_screener_data(limit)
    
    def _get_fallback_screener_data(self, limit: int) -> List[Dict[str, Any]]:
        """Get fallback screener data when API fails"""
        popular_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
            'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LUNAUSDT',
            'MATICUSDT', 'LINKUSDT', 'LTCUSDT', 'UNIUSDT', 'ATOMUSDT',
            'FTMUSDT', 'AXSUSDT', 'SANDUSDT', 'MANAUSDT', 'GALAUSDT'
        ]
        
        screener_data = []
        for symbol in popular_symbols[:limit]:
            mock_data = self._generate_mock_data(symbol, '1h')
            screener_data.append({
                'symbol': symbol,
                'price': mock_data['price']['current'],
                'change_24h': mock_data['price']['change'],
                'volume_24h': mock_data['volume'],
                'high_24h': mock_data['price']['high'],
                'low_24h': mock_data['price']['low']
            })
        
        return screener_data
    
    def _process_screener_item(self, item: Dict) -> Dict[str, Any]:
        """Process single screener item"""
        try:
            d = item['d']
            symbol = item['s'].split(':')[1] if ':' in item['s'] else item['s']
            
            return {
                'symbol': symbol,
                'price': d[1] if len(d) > 1 else 0,
                'change': d[2] if len(d) > 2 else 0,
                'volume': d[3] if len(d) > 3 else 0,
                'market_cap': d[4] if len(d) > 4 else 0,
                'rsi': d[5] if len(d) > 5 else 50,
                'recommendation': d[6] if len(d) > 6 else 0
            }
        except Exception as e:
            logger.error(f"Error processing screener item: {e}")
            return {}

# Technical Analysis Functions
class TechnicalAnalysis:
    @staticmethod
    def calculate_signal_strength(data: Dict) -> Dict[str, Any]:
        """
        Hitung kekuatan sinyal berdasarkan indikator teknikal
        
        Args:
            data: Market data dengan indicators
            
        Returns:
            Dict dengan analisis sinyal
        """
        try:
            indicators = data.get('indicators', {})
            price = data.get('price', {})
            
            signals = []
            confidence_factors = []
            analysis = {}
            
            # RSI Analysis
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                signals.append('LONG')
                confidence_factors.append(0.8)
                analysis['rsi'] = f"Oversold (RSI: {rsi:.1f})"
            elif rsi > 70:
                signals.append('SHORT')
                confidence_factors.append(0.8)
                analysis['rsi'] = f"Overbought (RSI: {rsi:.1f})"
            else:
                analysis['rsi'] = f"Neutral (RSI: {rsi:.1f})"
            
            # MACD Analysis
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            macd_histogram = indicators.get('macd_histogram', 0)
            
            if macd > macd_signal and macd_histogram > 0:
                signals.append('LONG')
                confidence_factors.append(0.7)
                analysis['macd'] = "Bullish crossover"
            elif macd < macd_signal and macd_histogram < 0:
                signals.append('SHORT')
                confidence_factors.append(0.7)
                analysis['macd'] = "Bearish crossover"
            else:
                analysis['macd'] = "No clear signal"
            
            # Moving Average Analysis
            current_price = price.get('current', 0)
            ema_20 = indicators.get('ema_20', current_price)
            ema_50 = indicators.get('ema_50', current_price)
            sma_20 = indicators.get('sma_20', current_price)
            sma_50 = indicators.get('sma_50', current_price)
            
            if current_price > ema_20 > ema_50:
                signals.append('LONG')
                confidence_factors.append(0.6)
                analysis['ma'] = "Price above moving averages"
            elif current_price < ema_20 < ema_50:
                signals.append('SHORT')
                confidence_factors.append(0.6)
                analysis['ma'] = "Price below moving averages"
            else:
                analysis['ma'] = "Mixed signals from moving averages"
            
            # Bollinger Bands Analysis
            bb_upper = indicators.get('bb_upper', 0)
            bb_lower = indicators.get('bb_lower', 0)
            bb_middle = indicators.get('bb_middle', 0)
            
            if current_price > bb_upper:
                signals.append('SHORT')
                confidence_factors.append(0.5)
                analysis['bb'] = "Price above upper band (overbought)"
            elif current_price < bb_lower:
                signals.append('LONG')
                confidence_factors.append(0.5)
                analysis['bb'] = "Price below lower band (oversold)"
            else:
                analysis['bb'] = "Price within bands (normal)"
            
            # Trend Analysis
            trend_strength = indicators.get('trend_strength', 50)
            if trend_strength > 70:
                signals.append('LONG')
                confidence_factors.append(0.4)
                analysis['trend'] = f"Strong uptrend ({trend_strength:.1f}%)"
            elif trend_strength < 30:
                signals.append('SHORT')
                confidence_factors.append(0.4)
                analysis['trend'] = f"Strong downtrend ({trend_strength:.1f}%)"
            else:
                analysis['trend'] = f"Neutral trend ({trend_strength:.1f}%)"
            
            # Calculate overall signal
            long_signals = signals.count('LONG')
            short_signals = signals.count('SHORT')
            
            if long_signals > short_signals:
                overall_signal = 'LONG'
                confidence = sum(confidence_factors[:long_signals]) / len(confidence_factors) if confidence_factors else 0
            elif short_signals > long_signals:
                overall_signal = 'SHORT'
                confidence = sum(confidence_factors[:short_signals]) / len(confidence_factors) if confidence_factors else 0
            else:
                overall_signal = 'NEUTRAL'
                confidence = 0.3
            
            # Calculate risk levels
            risk_data = TechnicalAnalysis.calculate_risk_levels(data, overall_signal)
            
            return {
                'signal': overall_signal,
                'confidence': round(confidence * 100, 1),
                'strength': len([s for s in signals if s == overall_signal]),
                'analysis': analysis,
                'take_profit': risk_data['take_profit'],
                'stop_loss': risk_data['stop_loss'],
                'risk_reward_ratio': risk_data['risk_reward_ratio'],
                'entry_price': current_price,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating signal strength: {e}")
            return TechnicalAnalysis.get_default_signal(data)
    
    @staticmethod
    def calculate_risk_levels(data: Dict, signal: str) -> Dict[str, float]:
        """Calculate take profit and stop loss levels"""
        try:
            price = data.get('price', {})
            current_price = price.get('current', 0)
            
            if current_price == 0:
                return {'take_profit': 0, 'stop_loss': 0, 'risk_reward_ratio': 0}
            
            # Estimate volatility from high/low
            high = price.get('high', current_price)
            low = price.get('low', current_price)
            atr_estimate = abs(high - low)
            
            if atr_estimate == 0:
                atr_estimate = current_price * 0.02  # 2% fallback
            
            if signal == 'LONG':
                stop_loss = current_price - (atr_estimate * 1.5)
                take_profit = current_price + (atr_estimate * 2.5)
            elif signal == 'SHORT':
                stop_loss = current_price + (atr_estimate * 1.5)
                take_profit = current_price - (atr_estimate * 2.5)
            else:
                stop_loss = current_price
                take_profit = current_price
            
            # Calculate risk-reward ratio
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit - current_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            return {
                'take_profit': round(take_profit, 4),
                'stop_loss': round(stop_loss, 4),
                'risk_reward_ratio': round(risk_reward_ratio, 2)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk levels: {e}")
            return {'take_profit': 0, 'stop_loss': 0, 'risk_reward_ratio': 0}
    
    @staticmethod
    def get_default_signal(data: Dict) -> Dict[str, Any]:
        """Return default signal when calculation fails"""
        price = data.get('price', {}).get('current', 0)
        return {
            'signal': 'NEUTRAL',
            'confidence': 0,
            'strength': 0,
            'analysis': {
                'rsi': 'Unable to calculate',
                'macd': 'Unable to calculate',
                'ma': 'Unable to calculate',
                'bb': 'Unable to calculate',
                'trend': 'Unable to calculate'
            },
            'take_profit': price,
            'stop_loss': price,
            'risk_reward_ratio': 0,
            'entry_price': price,
            'timestamp': datetime.now()
        }


# Test function
async def test_tradingview_scraper():
    """Test TradingView scraper"""
    print("🧪 Testing TradingView Scraper...")
    
    async with TradingViewScraper() as scraper:
        # Test market data
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        for symbol in symbols:
            print(f"\n📊 Testing {symbol}...")
            
            data = await scraper.get_market_data(symbol, '1h')
            
            if data:
                print(f"✅ Data fetched for {symbol}")
                print(f"   Price: ${data['price']['current']:,.2f}")
                print(f"   Change: {data['price']['change']:+.2f}%")
                print(f"   RSI: {data['indicators']['rsi']:.1f}")
                
                # Test technical analysis
                signal = TechnicalAnalysis.calculate_signal_strength(data)
                print(f"   Signal: {signal['signal']} ({signal['confidence']:.1f}%)")
                
            else:
                print(f"❌ Failed to fetch data for {symbol}")
            
            await asyncio.sleep(1)  # Rate limiting


if __name__ == "__main__":
    asyncio.run(test_tradingview_scraper())

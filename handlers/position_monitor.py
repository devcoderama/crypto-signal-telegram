"""
Position Monitor Module
Monitor posisi trading dan price alerts secara real-time
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from database import DatabaseManager
from scripts.tradingview_scraper import TradingViewScraper

logger = logging.getLogger(__name__)

class PositionMonitor:
    def __init__(self, client, db: DatabaseManager):
        self.client = client
        self.db = db
        self.is_monitoring = False
        self.check_interval = 30  # seconds
    
    async def start_monitoring(self):
        """Start monitoring positions and alerts"""
        self.is_monitoring = True
        logger.info("🔄 Starting position monitoring...")
        
        while self.is_monitoring:
            try:
                # Check positions for TP/SL hits
                await self.check_positions()
                
                # Check price alerts
                await self.check_price_alerts()
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop position monitoring"""
        self.is_monitoring = False
        logger.info("⏹️ Position monitoring stopped")
    
    async def check_positions(self):
        """Check all open positions for TP/SL hits"""
        try:
            # Get all open positions
            positions = await self.db.get_all_open_positions()
            
            if not positions:
                return
            
            # Group positions by symbol to minimize API calls
            symbols_to_check = list(set(pos['symbol'] for pos in positions))
            
            async with TradingViewScraper() as scraper:
                for symbol in symbols_to_check:
                    try:
                        # Get current market data
                        data = await scraper.get_market_data(symbol, '1m')
                        
                        if not data:
                            continue
                        
                        current_price = data['price']['current']
                        
                        # Check all positions for this symbol
                        symbol_positions = [pos for pos in positions if pos['symbol'] == symbol]
                        
                        for position in symbol_positions:
                            await self.check_position_levels(position, current_price)
                        
                        # Small delay between symbols
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error checking symbol {symbol}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error checking positions: {e}")
    
    async def check_position_levels(self, position: Dict, current_price: float):
        """Check if position hit TP or SL levels"""
        try:
            position_id = position['id']
            user_id = position['user_id']
            symbol = position['symbol']
            direction = position['direction']
            entry_price = position['entry_price']
            take_profit = position['take_profit']
            stop_loss = position['stop_loss']
            
            # Calculate current PnL
            if direction == 'LONG':
                pnl_percentage = ((current_price - entry_price) / entry_price) * 100
                
                # Check take profit
                if current_price >= take_profit:
                    await self.close_position(position, current_price, 'TP_HIT')
                    return
                
                # Check stop loss
                if current_price <= stop_loss:
                    await self.close_position(position, current_price, 'SL_HIT')
                    return
                    
            else:  # SHORT
                pnl_percentage = ((entry_price - current_price) / entry_price) * 100
                
                # Check take profit
                if current_price <= take_profit:
                    await self.close_position(position, current_price, 'TP_HIT')
                    return
                
                # Check stop loss
                if current_price >= stop_loss:
                    await self.close_position(position, current_price, 'SL_HIT')
                    return
            
            # Update current price and PnL if no TP/SL hit
            pnl_value = (pnl_percentage / 100) * (position['quantity'] * entry_price)
            
            await self.db.update_position(
                position_id,
                current_price=current_price,
                pnl=pnl_value,
                pnl_percentage=pnl_percentage
            )
            
        except Exception as e:
            logger.error(f"Error checking position levels: {e}")
    
    async def close_position(self, position: Dict, current_price: float, status: str):
        """Close position and send notification"""
        try:
            position_id = position['id']
            user_id = position['user_id']
            symbol = position['symbol']
            direction = position['direction']
            entry_price = position['entry_price']
            
            # Calculate final PnL
            if direction == 'LONG':
                pnl_percentage = ((current_price - entry_price) / entry_price) * 100
            else:  # SHORT
                pnl_percentage = ((entry_price - current_price) / entry_price) * 100
            
            pnl_value = (pnl_percentage / 100) * (position['quantity'] * entry_price)
            
            # Update position in database
            await self.db.update_position(
                position_id,
                current_price=current_price,
                pnl=pnl_value,
                pnl_percentage=pnl_percentage,
                status=status,
                closed_at=datetime.now().isoformat()
            )
            
            # Send notification to user
            await self.send_position_notification(position, current_price, status, pnl_percentage)
            
            logger.info(f"Position closed: {symbol} {direction} - {status} - PnL: {pnl_percentage:.2f}%")
            
        except Exception as e:
            logger.error(f"Error closing position: {e}")
    
    async def send_position_notification(self, position: Dict, current_price: float, status: str, pnl_percentage: float):
        """Send notification about position closure"""
        try:
            user_id = position['user_id']
            symbol = position['symbol']
            direction = position['direction']
            entry_price = position['entry_price']
            
            # Format notification message
            if status == 'TP_HIT':
                emoji = "🎯✅"
                title = "TAKE PROFIT HIT!"
                result = "PROFIT"
            else:  # SL_HIT
                emoji = "🛡️❌"
                title = "STOP LOSS HIT!"
                result = "LOSS"
            
            direction_emoji = "📈" if direction == "LONG" else "📉"
            pnl_emoji = "🟢" if pnl_percentage >= 0 else "🔴"
            
            message = f"""
{emoji} **{title}**

{direction_emoji} **{symbol} {direction} Position Closed**

💰 **Trade Summary:**
• Entry Price: ${entry_price:,.2f}
• Exit Price: ${current_price:,.2f}
• Result: **{result}**

{pnl_emoji} **PnL: {pnl_percentage:+.2f}%**

⏰ *Closed at {datetime.now().strftime('%H:%M:%S')}*
"""
            
            # Send notification
            await self.client.send_message(user_id, message)
            
        except Exception as e:
            logger.error(f"Error sending position notification: {e}")
    
    async def check_price_alerts(self):
        """Check all active price alerts"""
        try:
            # Get all active alerts
            alerts = await self.db.get_active_alerts()
            
            if not alerts:
                return
            
            # Group alerts by symbol
            symbols_to_check = list(set(alert['symbol'] for alert in alerts))
            
            async with TradingViewScraper() as scraper:
                for symbol in symbols_to_check:
                    try:
                        # Get current market data
                        data = await scraper.get_market_data(symbol, '1m')
                        
                        if not data:
                            continue
                        
                        current_price = data['price']['current']
                        
                        # Check all alerts for this symbol
                        symbol_alerts = [alert for alert in alerts if alert['symbol'] == symbol]
                        
                        for alert in symbol_alerts:
                            if self.check_alert_condition(alert, current_price):
                                await self.trigger_price_alert(alert, current_price)
                        
                        # Small delay between symbols
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error checking alerts for {symbol}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error checking price alerts: {e}")
    
    def check_alert_condition(self, alert: Dict, current_price: float) -> bool:
        """Check if alert condition is met"""
        target_price = alert['target_price']
        condition = alert['condition']
        
        if condition == 'ABOVE':
            return current_price >= target_price
        elif condition == 'BELOW':
            return current_price <= target_price
        
        return False
    
    async def trigger_price_alert(self, alert: Dict, current_price: float):
        """Trigger price alert and send notification"""
        try:
            alert_id = alert['id']
            user_id = alert['user_id']
            symbol = alert['symbol']
            target_price = alert['target_price']
            condition = alert['condition']
            
            # Deactivate alert in database
            await self.db.trigger_alert(alert_id, current_price)
            
            # Format notification message
            condition_emoji = "⬆️" if condition == 'ABOVE' else "⬇️"
            condition_text = "naik ke" if condition == 'ABOVE' else "turun ke"
            
            message = f"""
🔔 **PRICE ALERT TRIGGERED!**

{condition_emoji} **{symbol}** telah {condition_text} target price!

🎯 **Alert Details:**
• Target: ${target_price:,.2f}
• Current: ${current_price:,.2f}
• Condition: {condition}

⏰ *Triggered at {datetime.now().strftime('%H:%M:%S')}*

Gunakan /analyze {symbol.replace('USDT', '')} untuk analisis lanjutan.
"""
            
            # Send notification
            await self.client.send_message(user_id, message)
            
            logger.info(f"Price alert triggered: {symbol} {condition} ${target_price:,.2f}")
            
        except Exception as e:
            logger.error(f"Error triggering price alert: {e}")

# Position Manager for manual operations
class PositionManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def create_position(self, user_id: int, symbol: str, direction: str, 
                            entry_price: float, take_profit: float, stop_loss: float,
                            quantity: float = 1.0, confidence: float = 0.0) -> int:
        """Create new trading position"""
        try:
            position_id = await self.db.add_position(
                user_id=user_id,
                symbol=symbol,
                position_type=direction.lower(),
                entry_price=entry_price,
                quantity=quantity,
                timeframe='1h',  # default timeframe
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            
            logger.info(f"Position created: {symbol} {direction} for user {user_id}")
            return position_id
            
        except Exception as e:
            logger.error(f"Error creating position: {e}")
            return 0
    
    async def close_position_manually(self, position_id: int, current_price: float) -> bool:
        """Manually close a position"""
        try:
            # Get position details
            positions = await self.db.get_all_open_positions()
            position = next((p for p in positions if p['id'] == position_id), None)
            
            if not position:
                return False
            
            # Calculate PnL
            direction = position['direction']
            entry_price = position['entry_price']
            
            if direction == 'LONG':
                pnl_percentage = ((current_price - entry_price) / entry_price) * 100
            else:  # SHORT
                pnl_percentage = ((entry_price - current_price) / entry_price) * 100
            
            pnl_value = (pnl_percentage / 100) * (position['quantity'] * entry_price)
            
            # Update position
            success = await self.db.update_position(
                position_id,
                current_price=current_price,
                pnl=pnl_value,
                pnl_percentage=pnl_percentage,
                status='CLOSED_MANUAL',
                closed_at=datetime.now().isoformat()
            )
            
            if success:
                logger.info(f"Position closed manually: ID {position_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error closing position manually: {e}")
            return False

# Test function
async def test_position_monitor():
    """Test position monitoring"""
    print("🧪 Testing Position Monitor...")
    
    # Mock database and client
    db = DatabaseManager("test_monitor.db")
    
    # Create test position
    position_id = db.add_position(
        user_id=123456789,
        symbol='BTCUSDT',
        direction='LONG',
        entry_price=67500.0,
        take_profit=70000.0,
        stop_loss=65000.0,
        quantity=0.001,
        confidence=85.0
    )
    
    print(f"✅ Test position created: {position_id}")
    
    # Test position manager
    manager = PositionManager(db)
    new_position = await manager.create_position(
        user_id=123456789,
        symbol='ETHUSDT',
        direction='SHORT',
        entry_price=3800.0,
        take_profit=3600.0,
        stop_loss=4000.0,
        quantity=0.1,
        confidence=75.0
    )
    
    print(f"✅ New position created: {new_position}")
    
    # Test position closure
    closed = await manager.close_position_manually(new_position, 3700.0)
    print(f"✅ Position closure: {'Success' if closed else 'Failed'}")
    
    # Cleanup
    import os
    os.remove("test_monitor.db")
    print("✅ Test completed")

if __name__ == "__main__":
    asyncio.run(test_position_monitor())

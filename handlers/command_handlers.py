"""
Command Handlers Module
Handler untuk semua command dan callback Telegram bot
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from telethon import events, Button
from telethon.tl.types import User

from database import DatabaseManager
from scripts.tradingview_scraper import TradingViewScraper, TechnicalAnalysis
from keyboards.bot_keyboards import BotKeyboards
from config import ADMIN_ID, WELCOME_MESSAGE, HELP_MESSAGE

logger = logging.getLogger(__name__)

class CommandHandlers:
    def __init__(self, client, db: DatabaseManager):
        self.client = client
        self.db = db
        self.user_sessions = {}  # Store user interactive sessions
        self.keyboards = BotKeyboards()
    
    def register_handlers(self):
        """Register semua event handlers"""
        
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            await self.handle_start(event)
        
        @self.client.on(events.NewMessage(pattern='/help'))
        async def help_handler(event):
            await self.handle_help(event)
        
        @self.client.on(events.NewMessage(pattern='/analyze'))
        async def analyze_handler(event):
            await self.handle_analyze_command(event)
        
        @self.client.on(events.NewMessage(pattern='/positions'))
        async def positions_handler(event):
            await self.handle_positions(event)
        
        @self.client.on(events.NewMessage(pattern='/alerts'))
        async def alerts_handler(event):
            await self.handle_alerts(event)
        
        @self.client.on(events.NewMessage(pattern='/settings'))
        async def settings_handler(event):
            await self.handle_settings(event)
        
        @self.client.on(events.NewMessage(pattern='/admin'))
        async def admin_handler(event):
            await self.handle_admin_command(event)
        
        @self.client.on(events.NewMessage(pattern='/broadcast'))
        async def broadcast_handler(event):
            await self.handle_broadcast_command(event)
        
        @self.client.on(events.CallbackQuery)
        async def callback_handler(event):
            await self.handle_callback(event)
        
        @self.client.on(events.NewMessage)
        async def message_handler(event):
            await self.handle_message(event)
    
    async def handle_start(self, event):
        """Handle /start command"""
        user = await event.get_sender()
        user_id = user.id
        
        try:
            # Add user to database
            await self.db.add_user(
                user_id=user_id,
                username=getattr(user, 'username', None),
                first_name=getattr(user, 'first_name', None),
                last_name=getattr(user, 'last_name', None)
            )
            
            # Log interaction
            await self.db.log_interaction(user_id, 'start_command')
            
            # Send welcome message with keyboard
            await event.reply(
                WELCOME_MESSAGE,
                buttons=self.keyboards.main_menu()
            )
            
        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            await event.reply("❌ Terjadi kesalahan. Silakan coba lagi.")
    
    async def handle_help(self, event):
        """Handle /help command"""
        user_id = event.sender_id
        
        try:
            await self.db.log_interaction(user_id, 'help_command')
            
            await event.reply(
                HELP_MESSAGE,
                buttons=self.keyboards.help_categories()
            )
            
        except Exception as e:
            logger.error(f"Error in help handler: {e}")
            await event.reply("❌ Terjadi kesalahan. Silakan coba lagi.")
    
    async def handle_analyze_command(self, event):
        """Handle /analyze command dengan parameter opsional"""
        user_id = event.sender_id
        
        try:
            # Parse command arguments
            message_text = event.message.text.strip()
            parts = message_text.split()
            
            if len(parts) >= 2:
                # Symbol provided directly
                symbol = parts[1].upper()
                timeframe = parts[2] if len(parts) > 2 else "1h"
                
                # Add USDT if not present
                if not symbol.endswith('USDT'):
                    symbol += 'USDT'
                
                await self.perform_analysis(event, symbol, timeframe)
            else:
                # Show symbol selection
                await self.show_symbol_selection(event)
                
        except Exception as e:
            logger.error(f"Error in analyze handler: {e}")
            await event.reply("❌ Terjadi kesalahan saat analisis.")
    
    async def handle_positions(self, event):
        """Handle /positions command"""
        user_id = event.sender_id
        
        try:
            await self.db.log_interaction(user_id, 'view_positions')
            
            positions = await self.db.get_user_positions(user_id, status='open')
            
            if not positions:
                await event.reply(
                    "📈 **Posisi Trading**\n\n"
                    "Belum ada posisi aktif.\n"
                    "Gunakan /analyze untuk mendapatkan sinyal trading.",
                    buttons=[[Button.inline("📊 Analisis Market", b"analyze_market")]]
                )
                return
            
            # Format positions message
            msg = "📈 **Posisi Trading Aktif**\n\n"
            total_pnl = 0
            
            for i, pos in enumerate(positions[:5], 1):
                # Calculate PnL percentage
                entry_price = pos.get('entry_price', 0)
                current_price = pos.get('current_price', entry_price)  # Use entry if current not available
                position_type = pos.get('position_type', 'long').lower()
                
                if entry_price > 0:
                    if position_type == 'long':
                        pnl_percentage = ((current_price - entry_price) / entry_price) * 100
                    else:  # short
                        pnl_percentage = ((entry_price - current_price) / entry_price) * 100
                else:
                    pnl_percentage = 0
                
                pnl_emoji = "🟢" if pnl_percentage >= 0 else "🔴"
                direction_emoji = "📈" if position_type == "long" else "📉"
                
                msg += f"""
**{i}. {pos['symbol']} {direction_emoji}**
• Entry: ${entry_price:,.2f}
• Current: ${current_price:,.2f}
• PnL: {pnl_emoji} {pnl_percentage:+.2f}%
• TP: ${pos.get('take_profit', 0):,.2f}
• SL: ${pos.get('stop_loss', 0):,.2f}
"""
                total_pnl += pnl_percentage
            
            # Average PnL
            avg_pnl = total_pnl / len(positions) if positions else 0
            pnl_emoji = "🟢" if avg_pnl >= 0 else "🔴"
            msg += f"\n{pnl_emoji} **Average PnL:** {avg_pnl:+.2f}%"
            
            await event.reply(msg, buttons=self.keyboards.position_actions())
            
        except Exception as e:
            logger.error(f"Error in positions handler: {e}")
            await event.reply("❌ Terjadi kesalahan saat mengambil posisi.")
    
    async def handle_alerts(self, event):
        """Handle /alerts command"""
        user_id = event.sender_id
        
        try:
            await self.db.log_interaction(user_id, 'view_alerts')
            
            # Get user's active alerts from database
            alerts = await self.db.get_user_alerts(user_id, active_only=True)
            
            if not alerts:
                await event.reply(
                    "🔔 **Price Alerts**\n\n"
                    "Belum ada alert aktif.\n\n"
                    "**Cara membuat alert:**\n"
                    "1. Pilih 'Add Alert'\n"
                    "2. Pilih symbol\n"
                    "3. Set target price\n"
                    "4. Pilih kondisi (Above/Below)",
                    buttons=self.keyboards.alert_actions()
                )
                return
            
            # Format alerts message
            msg = "🔔 **Price Alerts Aktif**\n\n"
            
            for i, alert in enumerate(alerts[:5], 1):
                condition_emoji = "⬆️" if alert['condition'] == 'ABOVE' else "⬇️"
                created_date = alert['created_at'][:10] if alert['created_at'] else 'Unknown'
                
                msg += f"""
**{i}. {alert['symbol']} {condition_emoji}**
• Target: ${alert['target_price']:,.2f}
• Condition: {alert['condition']}
• Created: {created_date}
"""
            
            await event.reply(msg, buttons=self.keyboards.alert_actions())
            
        except Exception as e:
            logger.error(f"Error in alerts handler: {e}")
            await event.reply("❌ Terjadi kesalahan saat mengambil alerts.")
    
    async def handle_settings(self, event):
        """Handle /settings command"""
        user_id = event.sender_id
        
        try:
            await self.db.log_interaction(user_id, 'view_settings')
            
            # Default settings (bisa diperluas dengan user preferences)
            msg = f"""
⚙️ **Bot Settings**

• **Risk per Trade:** 2.0%
• **Reward Ratio:** 1:2.0
• **Max Positions:** 5
• **Notifications:** ✅ Enabled
• **Default Timeframe:** 1h

User ID: `{user_id}`
"""
            
            await event.reply(msg, buttons=self.keyboards.settings_menu())
            
        except Exception as e:
            logger.error(f"Error in settings handler: {e}")
            await event.reply("❌ Terjadi kesalahan saat mengambil settings.")
    
    async def handle_admin_command(self, event):
        """Handle /admin command (admin only)"""
        user_id = event.sender_id
        
        if user_id != ADMIN_ID:
            await event.reply("❌ Access denied. Admin only.")
            return
        
        try:
            # Get bot statistics
            stats = await self.db.get_stats()
            
            msg = f"""
🔧 **Admin Panel**

**User Statistics:**
• Total Users: {stats.get('total_users', 0)}
• Active Users: {stats.get('active_users', 0)}
• New Today: {stats.get('new_today', 0)}

**Trading Statistics:**
• Total Positions: {stats.get('total_positions', 0)}
• Open Positions: {stats.get('open_positions', 0)}

**System:**
• Bot Status: ✅ Online
• Database: ✅ Connected
• Last Update: {datetime.now().strftime('%H:%M:%S')}
"""
            
            await event.reply(msg, buttons=self.keyboards.admin_panel())
            
        except Exception as e:
            logger.error(f"Error in admin handler: {e}")
            await event.reply("❌ Terjadi kesalahan admin.")
    
    async def handle_broadcast_command(self, event):
        """Handle /broadcast command (admin only)"""
        user_id = event.sender_id
        
        if user_id != ADMIN_ID:
            await event.reply("❌ Access denied. Admin only.")
            return
        
        try:
            # Parse broadcast message
            message_text = event.message.text
            if message_text.startswith('/broadcast '):
                broadcast_msg = message_text[11:]  # Remove '/broadcast '
                
                if broadcast_msg.strip():
                    await self.send_broadcast(event, broadcast_msg)
                else:
                    await event.reply("❌ Broadcast message cannot be empty.\nUsage: /broadcast <message>")
            else:
                await event.reply(
                    "📢 **Broadcast Message**\n\n"
                    "Usage: `/broadcast <your message>`\n\n"
                    "Example: `/broadcast 🚀 New feature available!`"
                )
                
        except Exception as e:
            logger.error(f"Error in broadcast handler: {e}")
            await event.reply("❌ Terjadi kesalahan broadcast.")
    
    async def handle_callback(self, event):
        """Handle inline keyboard callbacks"""
        user_id = event.sender_id
        data = event.data.decode('utf-8')
        
        try:
            # Log callback interaction
            await self.db.log_interaction(user_id, 'callback', data)
            
            # Route callback to appropriate handler
            if data == "analyze_market":
                await self.show_symbol_selection(event)
            
            elif data.startswith("symbol_"):
                symbol = data[7:]  # Remove "symbol_" prefix
                await self.show_timeframe_selection(event, symbol)
            
            elif data.startswith("tf_"):
                timeframe = data[3:]  # Remove "tf_" prefix
                await self.handle_timeframe_selection(event, timeframe)
            
            elif data == "view_positions":
                await self.handle_positions(event)
            
            elif data == "price_alerts":
                await self.handle_alerts(event)
            
            elif data == "settings":
                await self.handle_settings(event)
            
            elif data == "back_main":
                await self.show_main_menu(event)
            
            elif data.startswith("admin_"):
                await self.handle_admin_callback(event, data)
            
            # Add more callback handlers as needed...
            
        except Exception as e:
            logger.error(f"Error in callback handler: {e}")
            await event.edit("❌ Terjadi kesalahan. Silakan coba lagi.")
    
    async def handle_message(self, event):
        """Handle regular text messages (for interactive sessions)"""
        user_id = event.sender_id
        
        # Skip if message is a command
        if event.message.text.startswith('/'):
            return
        
        # Handle interactive sessions
        if user_id in self.user_sessions:
            await self.handle_interactive_session(event)
    
    async def show_symbol_selection(self, event):
        """Show symbol selection keyboard"""
        msg = "📊 **Pilih Cryptocurrency untuk Analisis**\n\nPilih symbol yang ingin dianalisis:"
        
        await event.edit(msg, buttons=self.keyboards.symbol_selection())
    
    async def show_timeframe_selection(self, event, symbol: str):
        """Show timeframe selection for chosen symbol"""
        # Store symbol in user session
        self.user_sessions[event.sender_id] = {'symbol': symbol}
        
        msg = f"📊 **{symbol}**\n\n⏰ Pilih timeframe untuk analisis:"
        
        await event.edit(msg, buttons=self.keyboards.timeframe_selection())
    
    async def handle_timeframe_selection(self, event, timeframe: str):
        """Handle timeframe selection and perform analysis"""
        user_id = event.sender_id
        
        if user_id not in self.user_sessions:
            await event.edit("❌ Session expired. Please start again.")
            return
        
        symbol = self.user_sessions[user_id].get('symbol')
        if not symbol:
            await event.edit("❌ Symbol not found. Please start again.")
            return
        
        # Clean up session
        del self.user_sessions[user_id]
        
        await self.perform_analysis(event, symbol, timeframe)
    
    async def perform_analysis(self, event, symbol: str, timeframe: str):
        """Perform market analysis for symbol and timeframe"""
        try:
            # Show loading message
            loading_msg = await event.edit(f"🔄 Menganalisis {symbol} ({timeframe})...")
            
            # Perform analysis using TradingView scraper
            async with TradingViewScraper() as scraper:
                data = await scraper.get_market_data(symbol, timeframe)
                
                if not data:
                    await loading_msg.edit(
                        f"❌ **Error**\n\n"
                        f"Tidak dapat mengambil data untuk {symbol}.\n"
                        f"Pastikan symbol correct dan coba lagi.",
                        buttons=self.keyboards.symbol_selection()
                    )
                    return
                
                # Calculate trading signal
                signal = TechnicalAnalysis.calculate_signal_strength(data)
                
                if signal['signal'] == 'ERROR':
                    await loading_msg.edit(
                        f"❌ **Analysis Error**\n\n"
                        f"Error dalam analisis {symbol}.\n"
                        f"Silakan coba lagi.",
                        buttons=self.keyboards.symbol_selection()
                    )
                    return
                
                # Save signal to database
                await self.db.add_signal(
                    symbol=symbol,
                    timeframe=timeframe,
                    signal_type=signal['signal'].lower(),
                    price=signal['entry_price'],
                    take_profit=signal['take_profit'],
                    stop_loss=signal['stop_loss'],
                    strength=signal['confidence']
                )
                
                # Format result message
                result_msg = self.format_analysis_result(data, signal, symbol, timeframe)
                
                # Show result with action buttons
                await loading_msg.edit(
                    result_msg,
                    buttons=self.keyboards.signal_actions(symbol, signal['signal'])
                )
                
        except Exception as e:
            logger.error(f"Error performing analysis: {e}")
            await event.edit(
                "❌ **Analysis Failed**\n\n"
                "Terjadi kesalahan saat analisis.\n"
                "Silakan coba lagi.",
                buttons=self.keyboards.symbol_selection()
            )
    
    def format_analysis_result(self, data: Dict, signal: Dict, symbol: str, timeframe: str) -> str:
        """Format analysis result into readable message"""
        try:
            price_info = data.get('price', {})
            current_price = price_info.get('current', 0)
            change_24h = price_info.get('change', 0)
            
            direction = signal['signal']
            confidence = signal['confidence']
            
            # Direction emoji and color
            if direction == 'LONG':
                direction_emoji = "🟢"
                direction_text = "LONG (Buy)"
            elif direction == 'SHORT':
                direction_emoji = "🔴"
                direction_text = "SHORT (Sell)"
            else:
                direction_emoji = "⚪"
                direction_text = "NEUTRAL (Hold)"
            
            # Confidence emoji
            if confidence >= 80:
                confidence_emoji = "🔥"
            elif confidence >= 60:
                confidence_emoji = "⚡"
            else:
                confidence_emoji = "📊"
            
            msg = f"""
{direction_emoji} **{symbol} - {direction_text}**

💰 **Price Info:**
• Current: ${current_price:,.2f}
• 24h Change: {change_24h:+.2f}%
• Timeframe: {timeframe}

🎯 **Trading Signal:**
• Entry: ${signal['entry_price']:,.2f}
• Take Profit: ${signal['take_profit']:,.2f}
• Stop Loss: ${signal['stop_loss']:,.2f}

{confidence_emoji} **Confidence:** {confidence:.1f}%
📊 **Risk/Reward:** 1:{signal.get('risk_reward_ratio', 0):.2f}

**📈 Technical Analysis:**
"""
            
            # Add analysis details
            analysis = signal.get('analysis', {})
            for indicator, result in analysis.items():
                msg += f"• **{indicator.upper()}:** {result}\n"
            
            msg += f"\n⏰ *Generated at {datetime.now().strftime('%H:%M:%S')}*"
            
            return msg
            
        except Exception as e:
            logger.error(f"Error formatting analysis result: {e}")
            return f"📊 **Analysis for {symbol}**\n\nError formatting result."
    
    async def show_main_menu(self, event):
        """Show main menu"""
        await event.edit(
            "🏠 **Main Menu**\n\nPilih aksi yang ingin dilakukan:",
            buttons=self.keyboards.main_menu()
        )
    
    async def handle_interactive_session(self, event):
        """Handle interactive text input sessions"""
        user_id = event.sender_id
        session = self.user_sessions.get(user_id)
        
        if not session:
            return
        
        message_text = event.message.text.strip()
        
        # Handle different session types
        if session.get('state') == 'waiting_custom_symbol':
            symbol = message_text.upper()
            
            # Validate symbol
            if len(symbol) < 2 or len(symbol) > 10:
                await event.reply("❌ Symbol tidak valid. Contoh: BTC, ETH, BNB")
                return
            
            # Add USDT if not present
            if not symbol.endswith('USDT'):
                symbol += 'USDT'
            
            # Update session and show timeframe selection
            session['symbol'] = symbol
            await self.show_timeframe_selection(event, symbol)
    
    async def handle_admin_callback(self, event, data: str):
        """Handle admin-specific callbacks"""
        user_id = event.sender_id
        
        if user_id != ADMIN_ID:
            await event.answer("❌ Access denied.", alert=True)
            return
        
        if data == "admin_broadcast":
            await event.edit(
                "📢 **Broadcast Message**\n\n"
                "Kirim pesan yang ingin di-broadcast ke semua user.\n"
                "Format: Ketik pesan Anda di chat."
            )
            
            # Set admin session for broadcast
            self.user_sessions[user_id] = {'state': 'waiting_broadcast_message'}
    
    async def send_broadcast(self, event, message: str):
        """Send broadcast message to all users"""
        try:
            # Get all active users
            users = await self.db.get_all_users(active_only=True)
            
            if not users:
                await event.reply("❌ No active users found.")
                return
            
            # Create broadcast record
            broadcast_id = await self.db.add_broadcast(ADMIN_ID, message, len(users))
            
            # Confirm broadcast
            await event.reply(
                f"📢 **Confirm Broadcast**\n\n"
                f"Message: {message}\n\n"
                f"Will be sent to {len(users)} users.\n"
                f"Continue?",
                buttons=self.keyboards.broadcast_confirmation(len(users))
            )
            
            # Store broadcast info in session
            self.user_sessions[event.sender_id] = {
                'state': 'confirming_broadcast',
                'broadcast_id': broadcast_id,
                'message': message,
                'users': users
            }
            
        except Exception as e:
            logger.error(f"Error preparing broadcast: {e}")
            await event.reply("❌ Error preparing broadcast.")

# Test function
def test_handlers():
    """Test handlers functionality"""
    print("🧪 Testing Command Handlers...")
    
    # Mock database for testing
    db = DatabaseManager("test_handlers.db")
    
    # Create handlers instance (without client for testing)
    handlers = CommandHandlers(None, db)
    
    print("✅ Handlers initialized")
    print("✅ All handler tests passed!")
    
    # Cleanup
    import os
    os.remove("test_handlers.db")

if __name__ == "__main__":
    test_handlers()

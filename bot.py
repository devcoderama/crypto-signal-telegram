"""
Main Bot Module
Entry point untuk Crypto Trading Bot dengan struktur modular
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_ID
from database import DatabaseManager
from handlers.command_handlers import CommandHandlers
from handlers.position_monitor import PositionMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crypto_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class CryptoTradingBot:
    def __init__(self):
        self.client = None
        self.db = None
        self.handlers = None
        self.monitor = None
        self.is_running = False
    
    async def initialize(self):
        """Initialize bot components"""
        try:
            logger.info("🚀 Initializing Crypto Trading Bot...")
            
            # Initialize Telegram client
            self.client = TelegramClient('crypto_bot_session', API_ID, API_HASH)
            
            # Initialize database
            self.db = DatabaseManager()
            await self.db.init_database()
            logger.info("✅ Database initialized")
            
            # Initialize command handlers
            self.handlers = CommandHandlers(self.client, self.db)
            self.handlers.register_handlers()
            logger.info("✅ Command handlers registered")
            
            # Initialize position monitor
            self.monitor = PositionMonitor(self.client, self.db)
            logger.info("✅ Position monitor initialized")
            
            logger.info("🎉 Bot initialization completed")
            
        except Exception as e:
            logger.error(f"❌ Error initializing bot: {e}")
            raise
    
    async def start(self):
        """Start the bot"""
        try:
            # Initialize components
            await self.initialize()
            
            # Start Telegram client
            await self.client.start(bot_token=BOT_TOKEN)
            logger.info("✅ Telegram client started")
            
            # Get bot info
            me = await self.client.get_me()
            logger.info(f"🤖 Bot started as @{me.username} (ID: {me.id})")
            
            # Send startup notification to admin
            await self.send_startup_notification()
            
            # Start position monitoring in background
            asyncio.create_task(self.monitor.start_monitoring())
            logger.info("🔄 Position monitoring started")
            
            self.is_running = True
            logger.info("🟢 Crypto Trading Bot is now running!")
            
            # Keep the bot running
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def send_startup_notification(self):
        """Send startup notification to admin"""
        try:
            # Get bot statistics
            stats = await self.db.get_stats()
            
            startup_msg = f"""
🚀 **Crypto Trading Bot Started**

**System Status:**
• Bot: ✅ Online
• Database: ✅ Connected
• Monitoring: ✅ Active

**Statistics:**
• Total Users: {stats.get('total_users', 0)}
• Active Users: {stats.get('active_users', 0)}
• Open Positions: {stats.get('open_positions', 0)}

**Startup Time:** {asyncio.get_event_loop().time()}

Bot is ready to serve users! 🎯
"""
            
            await self.client.send_message(ADMIN_ID, startup_msg)
            logger.info("✅ Startup notification sent to admin")
            
        except Exception as e:
            logger.error(f"Error sending startup notification: {e}")
    
    async def cleanup(self):
        """Cleanup resources on shutdown"""
        try:
            logger.info("🛑 Shutting down bot...")
            
            # Stop position monitoring
            if self.monitor:
                self.monitor.stop_monitoring()
            
            # Send shutdown notification to admin
            if self.client and self.is_running:
                try:
                    shutdown_msg = "🛑 **Crypto Trading Bot Shutdown**\n\nBot has been stopped."
                    await self.client.send_message(ADMIN_ID, shutdown_msg)
                except:
                    pass
            
            # Close Telegram client
            if self.client:
                await self.client.disconnect()
            
            logger.info("✅ Bot shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main entry point"""
    bot = CryptoTradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

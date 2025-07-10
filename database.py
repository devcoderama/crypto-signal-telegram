"""
Database module for the modular crypto trading bot.
Handles all database operations using SQLite with async support.
"""

import sqlite3
import asyncio
import aiosqlite
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from config import DATABASE_PATH

# Setup logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Async database manager for the crypto trading bot."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()
    
    async def init_database(self):
        """Initialize database with required tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settings TEXT DEFAULT '{}',
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Positions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    symbol TEXT NOT NULL,
                    position_type TEXT NOT NULL, -- 'long' or 'short'
                    entry_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    take_profit REAL,
                    stop_loss REAL,
                    current_price REAL,
                    pnl REAL DEFAULT 0,
                    status TEXT DEFAULT 'open', -- 'open', 'closed', 'tp_hit', 'sl_hit'
                    timeframe TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Price alerts table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    symbol TEXT NOT NULL,
                    alert_type TEXT NOT NULL, -- 'price_above', 'price_below'
                    target_price REAL NOT NULL,
                    current_price REAL,
                    message TEXT,
                    is_triggered INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Signals history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS signals_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    signal_type TEXT NOT NULL, -- 'long', 'short', 'neutral'
                    price REAL NOT NULL,
                    rsi REAL,
                    macd REAL,
                    macd_signal REAL,
                    ma_short REAL,
                    ma_long REAL,
                    bb_upper REAL,
                    bb_lower REAL,
                    volume REAL,
                    strength INTEGER, -- 1-5 signal strength
                    take_profit REAL,
                    stop_loss REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Broadcasts table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    message TEXT NOT NULL,
                    total_users INTEGER DEFAULT 0,
                    successful_sends INTEGER DEFAULT 0,
                    failed_sends INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            # User interactions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    interaction_type TEXT NOT NULL, -- 'command', 'callback', 'message'
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    # Users management
    async def add_user(self, user_id: int, username: str = None, 
                      first_name: str = None, last_name: str = None) -> bool:
        """Add or update user in database."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, last_active)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (user_id, username, first_name, last_name))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def get_all_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all users."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM users"
                if active_only:
                    query += " WHERE is_active = 1"
                
                async with db.execute(query) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def update_user_activity(self, user_id: int) -> bool:
        """Update user's last activity timestamp."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating user activity {user_id}: {e}")
            return False
    
    # Positions management
    async def add_position(self, user_id: int, symbol: str, position_type: str,
                          entry_price: float, quantity: float, timeframe: str,
                          take_profit: float = None, stop_loss: float = None) -> Optional[int]:
        """Add new trading position."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO positions 
                    (user_id, symbol, position_type, entry_price, quantity, timeframe, take_profit, stop_loss)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, symbol, position_type, entry_price, quantity, timeframe, take_profit, stop_loss))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding position: {e}")
            return None
    
    async def get_user_positions(self, user_id: int, status: str = 'open') -> List[Dict[str, Any]]:
        """Get user's positions by status."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM positions 
                    WHERE user_id = ? AND status = ?
                    ORDER BY created_at DESC
                """, (user_id, status)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user positions: {e}")
            return []
    
    async def update_position(self, position_id: int, **kwargs) -> bool:
        """Update position with given parameters."""
        try:
            if not kwargs:
                return False
            
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [position_id]
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f"""
                    UPDATE positions SET {set_clause} WHERE id = ?
                """, values)
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating position {position_id}: {e}")
            return False
    
    async def close_position(self, position_id: int, close_price: float, 
                           status: str = 'closed') -> bool:
        """Close a trading position."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get position details first
                async with db.execute(
                    "SELECT * FROM positions WHERE id = ?", (position_id,)
                ) as cursor:
                    position = await cursor.fetchone()
                    
                if not position:
                    return False
                
                # Calculate PnL
                entry_price = position[4]  # entry_price column
                quantity = position[5]     # quantity column
                position_type = position[3] # position_type column
                
                if position_type == 'long':
                    pnl = (close_price - entry_price) * quantity
                else:  # short
                    pnl = (entry_price - close_price) * quantity
                
                # Update position
                await db.execute("""
                    UPDATE positions 
                    SET current_price = ?, pnl = ?, status = ?, closed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (close_price, pnl, status, position_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error closing position {position_id}: {e}")
            return False
    
    # Alerts management
    async def add_alert(self, user_id: int, symbol: str, alert_type: str,
                       target_price: float, message: str = None) -> Optional[int]:
        """Add price alert."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO alerts 
                    (user_id, symbol, alert_type, target_price, message)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, symbol, alert_type, target_price, message))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding alert: {e}")
            return None
    
    async def get_user_alerts(self, user_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get user's alerts."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM alerts WHERE user_id = ?"
                params = [user_id]
                
                if active_only:
                    query += " AND is_triggered = 0"
                
                query += " ORDER BY created_at DESC"
                
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user alerts: {e}")
            return []
    
    async def get_all_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts for monitoring."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM alerts 
                    WHERE is_triggered = 0
                    ORDER BY created_at ASC
                """) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def trigger_alert(self, alert_id: int, current_price: float) -> bool:
        """Mark alert as triggered."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE alerts 
                    SET is_triggered = 1, current_price = ?, triggered_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (current_price, alert_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error triggering alert {alert_id}: {e}")
            return False
    
    async def remove_alert(self, alert_id: int, user_id: int = None) -> bool:
        """Remove alert."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = "DELETE FROM alerts WHERE id = ?"
                params = [alert_id]
                
                if user_id:
                    query += " AND user_id = ?"
                    params.append(user_id)
                
                await db.execute(query, params)
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing alert {alert_id}: {e}")
            return False
    
    # Signals history
    async def add_signal(self, symbol: str, timeframe: str, signal_type: str,
                        price: float, **technical_data) -> Optional[int]:
        """Add signal to history."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO signals_history 
                    (symbol, timeframe, signal_type, price, rsi, macd, macd_signal,
                     ma_short, ma_long, bb_upper, bb_lower, volume, strength, 
                     take_profit, stop_loss)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol, timeframe, signal_type, price,
                    technical_data.get('rsi'), technical_data.get('macd'),
                    technical_data.get('macd_signal'), technical_data.get('ma_short'),
                    technical_data.get('ma_long'), technical_data.get('bb_upper'),
                    technical_data.get('bb_lower'), technical_data.get('volume'),
                    technical_data.get('strength', 3), technical_data.get('take_profit'),
                    technical_data.get('stop_loss')
                ))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding signal: {e}")
            return None
    
    async def get_recent_signals(self, symbol: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent signals."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                query = "SELECT * FROM signals_history"
                params = []
                
                if symbol:
                    query += " WHERE symbol = ?"
                    params.append(symbol)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
            return []
    
    # Broadcasts
    async def add_broadcast(self, admin_id: int, message: str, 
                           total_users: int = 0) -> Optional[int]:
        """Add broadcast record."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO broadcasts (admin_id, message, total_users)
                    VALUES (?, ?, ?)
                """, (admin_id, message, total_users))
                await db.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error adding broadcast: {e}")
            return None
    
    async def update_broadcast_stats(self, broadcast_id: int, 
                                   successful: int, failed: int) -> bool:
        """Update broadcast statistics."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE broadcasts 
                    SET successful_sends = ?, failed_sends = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (successful, failed, broadcast_id))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating broadcast stats: {e}")
            return False
    
    # User interactions
    async def log_interaction(self, user_id: int, interaction_type: str, 
                            data: str = None) -> bool:
        """Log user interaction."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO user_interactions (user_id, interaction_type, data)
                    VALUES (?, ?, ?)
                """, (user_id, interaction_type, data))
                await db.commit()
                return True
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
            return False
    
    # Statistics
    async def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                stats = {}
                
                # Users count
                async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                    stats['total_users'] = (await cursor.fetchone())[0]
                
                async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1") as cursor:
                    stats['active_users'] = (await cursor.fetchone())[0]
                
                # Positions count
                async with db.execute("SELECT COUNT(*) FROM positions") as cursor:
                    stats['total_positions'] = (await cursor.fetchone())[0]
                
                async with db.execute("SELECT COUNT(*) FROM positions WHERE status = 'open'") as cursor:
                    stats['open_positions'] = (await cursor.fetchone())[0]
                
                # Alerts count
                async with db.execute("SELECT COUNT(*) FROM alerts WHERE is_triggered = 0") as cursor:
                    stats['active_alerts'] = (await cursor.fetchone())[0]
                
                # Signals count
                async with db.execute("SELECT COUNT(*) FROM signals_history") as cursor:
                    stats['total_signals'] = (await cursor.fetchone())[0]
                
                return stats
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    async def get_all_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions for monitoring."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("""
                    SELECT * FROM positions 
                    WHERE status = 'open'
                    ORDER BY created_at ASC
                """) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all open positions: {e}")
            return []
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts for monitoring."""
        return await self.get_all_active_alerts()
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics for admin."""
        return await self.get_stats()

# Global database instance
db_manager = DatabaseManager()

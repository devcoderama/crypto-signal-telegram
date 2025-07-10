"""
Keyboard Module
Inline keyboards untuk Telegram bot
"""

from telethon import Button
from typing import List, Dict, Any

class BotKeyboards:
    
    @staticmethod
    def main_menu() -> List[List[Button]]:
        """Main menu keyboard"""
        return [
            [
                Button.inline("📊 Analisis Market", b"analyze_market"),
                Button.inline("📈 Posisi Aktif", b"view_positions")
            ],
            [
                Button.inline("🔔 Price Alerts", b"price_alerts"),
                Button.inline("⚙️ Settings", b"settings")
            ],
            [
                Button.inline("🆘 Help", b"help"),
                Button.inline("📊 Market Screener", b"screener")
            ]
        ]
    
    @staticmethod
    def symbol_selection() -> List[List[Button]]:
        """Keyboard untuk pilihan symbol populer"""
        return [
            [
                Button.inline("₿ BTC", b"symbol_BTCUSDT"),
                Button.inline("Ξ ETH", b"symbol_ETHUSDT"),
                Button.inline("🔸 BNB", b"symbol_BNBUSDT")
            ],
            [
                Button.inline("⚡ SOL", b"symbol_SOLUSDT"),
                Button.inline("🔗 LINK", b"symbol_LINKUSDT"),
                Button.inline("🌊 ADA", b"symbol_ADAUSDT")
            ],
            [
                Button.inline("💎 XRP", b"symbol_XRPUSDT"),
                Button.inline("🦄 UNI", b"symbol_UNIUSDT"),
                Button.inline("📊 DOT", b"symbol_DOTUSDT")
            ],
            [
                Button.inline("✏️ Input Manual", b"input_custom_symbol"),
                Button.inline("↩️ Back", b"back_main")
            ]
        ]
    
    @staticmethod
    def timeframe_selection() -> List[List[Button]]:
        """Keyboard untuk pilihan timeframe"""
        return [
            [
                Button.inline("1m", b"tf_1m"),
                Button.inline("5m", b"tf_5m"),
                Button.inline("15m", b"tf_15m")
            ],
            [
                Button.inline("30m", b"tf_30m"),
                Button.inline("1h", b"tf_1h"),
                Button.inline("4h", b"tf_4h")
            ],
            [
                Button.inline("1d", b"tf_1d"),
                Button.inline("1w", b"tf_1w")
            ],
            [
                Button.inline("↩️ Back", b"back_symbol")
            ]
        ]
    
    @staticmethod
    def signal_actions(symbol: str, direction: str) -> List[List[Button]]:
        """Keyboard untuk aksi setelah mendapat sinyal"""
        return [
            [
                Button.inline(f"📈 Open {direction}", f"open_position_{symbol}_{direction}"),
                Button.inline("🔄 Refresh", f"refresh_{symbol}")
            ],
            [
                Button.inline("🔔 Set Alert", f"set_alert_{symbol}"),
                Button.inline("📊 Detail Analysis", f"detail_{symbol}")
            ],
            [
                Button.inline("🔙 Pilih Symbol Lain", b"analyze_market"),
                Button.inline("🏠 Main Menu", b"back_main")
            ]
        ]
    
    @staticmethod
    def position_actions() -> List[List[Button]]:
        """Keyboard untuk manajemen posisi"""
        return [
            [
                Button.inline("🔄 Refresh", b"refresh_positions"),
                Button.inline("❌ Close All", b"close_all_positions")
            ],
            [
                Button.inline("📊 P&L Summary", b"pnl_summary"),
                Button.inline("📈 Add Position", b"analyze_market")
            ],
            [
                Button.inline("🏠 Main Menu", b"back_main")
            ]
        ]
    
    @staticmethod
    def position_detail(position_id: int) -> List[List[Button]]:
        """Keyboard untuk detail posisi individual"""
        return [
            [
                Button.inline("❌ Close Position", f"close_position_{position_id}"),
                Button.inline("✏️ Edit TP/SL", f"edit_position_{position_id}")
            ],
            [
                Button.inline("↩️ Back to Positions", b"view_positions")
            ]
        ]
    
    @staticmethod
    def alert_actions() -> List[List[Button]]:
        """Keyboard untuk manajemen alerts"""
        return [
            [
                Button.inline("➕ Add Alert", b"add_alert"),
                Button.inline("📋 View All", b"view_alerts")
            ],
            [
                Button.inline("🗑️ Delete Alert", b"delete_alert"),
                Button.inline("🔄 Refresh", b"refresh_alerts")
            ],
            [
                Button.inline("🏠 Main Menu", b"back_main")
            ]
        ]
    
    @staticmethod
    def alert_condition() -> List[List[Button]]:
        """Keyboard untuk kondisi alert"""
        return [
            [
                Button.inline("⬆️ Above (Naik ke)", b"condition_above"),
                Button.inline("⬇️ Below (Turun ke)", b"condition_below")
            ],
            [
                Button.inline("↩️ Cancel", b"price_alerts")
            ]
        ]
    
    @staticmethod
    def settings_menu() -> List[List[Button]]:
        """Keyboard untuk settings"""
        return [
            [
                Button.inline("💰 Risk Settings", b"risk_settings"),
                Button.inline("📊 Default Timeframe", b"timeframe_settings")
            ],
            [
                Button.inline("🔔 Notifications", b"notification_settings"),
                Button.inline("📈 Max Positions", b"position_settings")
            ],
            [
                Button.inline("🏠 Main Menu", b"back_main")
            ]
        ]
    
    @staticmethod
    def risk_percentage_selection() -> List[List[Button]]:
        """Keyboard untuk pilihan risk percentage"""
        return [
            [
                Button.inline("1%", b"risk_1"),
                Button.inline("2%", b"risk_2"),
                Button.inline("3%", b"risk_3")
            ],
            [
                Button.inline("5%", b"risk_5"),
                Button.inline("10%", b"risk_10"),
                Button.inline("✏️ Custom", b"risk_custom")
            ],
            [
                Button.inline("↩️ Back", b"settings")
            ]
        ]
    
    @staticmethod
    def confirmation(action: str, data: str = "") -> List[List[Button]]:
        """Keyboard konfirmasi untuk aksi penting"""
        return [
            [
                Button.inline("✅ Yes", f"confirm_{action}_{data}"),
                Button.inline("❌ No", f"cancel_{action}")
            ]
        ]
    
    @staticmethod
    def admin_panel() -> List[List[Button]]:
        """Keyboard khusus admin"""
        return [
            [
                Button.inline("📊 Bot Statistics", b"admin_stats"),
                Button.inline("👥 User Management", b"admin_users")
            ],
            [
                Button.inline("📢 Broadcast Message", b"admin_broadcast"),
                Button.inline("📈 Trading Stats", b"admin_trading")
            ],
            [
                Button.inline("🔧 System Info", b"admin_system"),
                Button.inline("📋 Logs", b"admin_logs")
            ],
            [
                Button.inline("🏠 Main Menu", b"back_main")
            ]
        ]
    
    @staticmethod
    def broadcast_confirmation(total_users: int) -> List[List[Button]]:
        """Keyboard konfirmasi broadcast"""
        return [
            [
                Button.inline(f"📢 Send to {total_users} users", b"confirm_broadcast"),
                Button.inline("❌ Cancel", b"cancel_broadcast")
            ]
        ]
    
    @staticmethod
    def market_screener_actions() -> List[List[Button]]:
        """Keyboard untuk market screener"""
        return [
            [
                Button.inline("🔥 Top Gainers", b"screener_gainers"),
                Button.inline("📉 Top Losers", b"screener_losers")
            ],
            [
                Button.inline("💎 High Volume", b"screener_volume"),
                Button.inline("⚡ Strong Signals", b"screener_signals")
            ],
            [
                Button.inline("🔄 Refresh", b"screener_refresh"),
                Button.inline("🏠 Main Menu", b"back_main")
            ]
        ]
    
    @staticmethod
    def pagination(current_page: int, total_pages: int, data_type: str) -> List[List[Button]]:
        """Keyboard untuk pagination"""
        buttons = []
        
        # Navigation buttons
        nav_buttons = []
        if current_page > 1:
            nav_buttons.append(Button.inline("◀️ Previous", f"page_{data_type}_{current_page-1}"))
        
        nav_buttons.append(Button.inline(f"{current_page}/{total_pages}", f"current_page"))
        
        if current_page < total_pages:
            nav_buttons.append(Button.inline("Next ▶️", f"page_{data_type}_{current_page+1}"))
        
        if nav_buttons:
            buttons.append(nav_buttons)
        
        # Back button
        buttons.append([Button.inline("↩️ Back", f"back_{data_type}")])
        
        return buttons
    
    @staticmethod
    def quick_actions() -> List[List[Button]]:
        """Quick action buttons untuk power users"""
        return [
            [
                Button.inline("⚡ Quick BTC", b"quick_BTCUSDT_1h"),
                Button.inline("⚡ Quick ETH", b"quick_ETHUSDT_1h")
            ],
            [
                Button.inline("📊 Market Overview", b"market_overview"),
                Button.inline("🔔 All Alerts", b"view_alerts")
            ]
        ]
    
    @staticmethod
    def help_categories() -> List[List[Button]]:
        """Keyboard untuk kategori bantuan"""
        return [
            [
                Button.inline("🎯 Trading Signals", b"help_signals"),
                Button.inline("📈 Position Management", b"help_positions")
            ],
            [
                Button.inline("🔔 Price Alerts", b"help_alerts"),
                Button.inline("⚙️ Settings Guide", b"help_settings")
            ],
            [
                Button.inline("📊 Technical Analysis", b"help_technical"),
                Button.inline("💡 Tips & Tricks", b"help_tips")
            ],
            [
                Button.inline("🏠 Main Menu", b"back_main")
            ]
        ]

# Utility functions for keyboard management
class KeyboardUtils:
    
    @staticmethod
    def add_back_button(buttons: List[List[Button]], back_action: str = "back_main") -> List[List[Button]]:
        """Add back button to existing keyboard"""
        buttons.append([Button.inline("↩️ Back", back_action.encode())])
        return buttons
    
    @staticmethod
    def create_dynamic_symbol_keyboard(symbols: List[str], prefix: str = "symbol") -> List[List[Button]]:
        """Create dynamic symbol keyboard from list"""
        buttons = []
        
        # Group symbols in rows of 3
        for i in range(0, len(symbols), 3):
            row = []
            for symbol in symbols[i:i+3]:
                # Extract display name (remove USDT suffix for display)
                display_name = symbol.replace('USDT', '')
                row.append(Button.inline(display_name, f"{prefix}_{symbol}".encode()))
            buttons.append(row)
        
        # Add back button
        buttons.append([Button.inline("↩️ Back", b"back_main")])
        
        return buttons
    
    @staticmethod
    def create_numbered_list_keyboard(items: List[Dict], prefix: str, max_per_page: int = 5) -> List[List[Button]]:
        """Create numbered list keyboard for selections"""
        buttons = []
        
        for i, item in enumerate(items[:max_per_page], 1):
            display_text = f"{i}. {item.get('display', item.get('symbol', 'Item'))}"
            callback_data = f"{prefix}_{item.get('id', i)}"
            buttons.append([Button.inline(display_text, callback_data.encode())])
        
        return buttons

# Test function
def test_keyboards():
    """Test keyboard generation"""
    print("🧪 Testing Keyboard Generation...")
    
    keyboards = BotKeyboards()
    
    # Test main menu
    main_menu = keyboards.main_menu()
    print(f"✅ Main menu: {len(main_menu)} rows")
    
    # Test symbol selection
    symbol_kb = keyboards.symbol_selection()
    print(f"✅ Symbol selection: {len(symbol_kb)} rows")
    
    # Test timeframe selection
    timeframe_kb = keyboards.timeframe_selection()
    print(f"✅ Timeframe selection: {len(timeframe_kb)} rows")
    
    # Test dynamic keyboard
    symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
    dynamic_kb = KeyboardUtils.create_dynamic_symbol_keyboard(symbols)
    print(f"✅ Dynamic keyboard: {len(dynamic_kb)} rows")
    
    print("🎉 All keyboard tests passed!")

if __name__ == "__main__":
    test_keyboards()

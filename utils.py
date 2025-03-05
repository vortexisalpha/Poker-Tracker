import tkinter as tk
from tkinter import messagebox

def center_window(window, parent=None):
    """Center a window on the screen or relative to parent"""
    window.update_idletasks()
    
    if parent:
        x = parent.winfo_x() + (parent.winfo_width() - window.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - window.winfo_height()) // 2
    else:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - window.winfo_width()) // 2
        y = (screen_height - window.winfo_height()) // 2
    
    window.geometry(f"+{x}+{y}")

def show_message(title, message, parent=None):
    """Show an information message dialog"""
    return messagebox.showinfo(title, message, parent=parent)

def show_error(title, message, parent=None):
    """Show an error message dialog"""
    return messagebox.showerror(title, message, parent=parent)

def show_warning(title, message, parent=None):
    """Show a warning message dialog"""
    return messagebox.showwarning(title, message, parent=parent)

def format_currency(amount, symbol="£"):
    """Format a number as currency"""
    return f"{symbol}{amount:.2f}"

def calculate_player_stats(player_id, sessions):
    """Calculate stats for a player across all sessions"""
    total_sessions = 0
    total_buyins = 0
    total_cashouts = 0
    
    for session in sessions:
        for player in session["players"]:
            if player["id"] == player_id:
                total_sessions += 1
                total_buyins += player["buyin"] + player.get("rebuys", 0)
                total_cashouts += player.get("cashout", 0)
    
    profit = total_cashouts - total_buyins
    avg_profit = profit / total_sessions if total_sessions > 0 else 0
    
    return {
        "sessions": total_sessions,
        "buyins": total_buyins,
        "cashouts": total_cashouts,
        "profit": profit,
        "avg_profit": avg_profit
    }

def validate_decimal_input(value):
    """Validate that input is a valid decimal number"""
    if value == "":
        return True
    try:
        float(value)
        return True
    except ValueError:
        return False

def debug_log(message):
    """Print debug information with timestamp"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[DEBUG {timestamp}] {message}") 
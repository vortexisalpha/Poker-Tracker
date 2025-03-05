import os
import json
import customtkinter as ctk
from PIL import Image
import tkinter as tk
from session_manager import SessionManager
from player_manager import PlayerManager
from google_sheets import GoogleSheetsManager
import utils

# Set appearance mode and default color theme
ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class PokerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        with open('config.json', 'r') as f:
            self.config = json.load(f)
        
        # Set up window properties
        self.title(self.config["app_name"])
        self.geometry("1100x700")
        self.minsize(900, 600)
        
        # Initialize managers
        self.player_manager = PlayerManager(self)
        self.session_manager = SessionManager(self, self.player_manager)
        
        try:
            self.sheets_manager = GoogleSheetsManager(
                self.config["google_credentials_file"],
                self.config["google_sheet_name"]
            )
        except Exception as e:
            print(f"Google Sheets integration failed: {e}")
            self.sheets_manager = None
        
        # Create layout first
        self.create_ui()
        
        # Then load saved data after UI exists
        self.data_file = self.config["data_file"]
        self.load_data()
        
        # Auto-save on close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        # Configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)  # Content column should expand
        self.grid_rowconfigure(0, weight=1)  # Row should expand vertically
        
        # Create navigation frame
        self.navigation_frame = ctk.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(5, weight=1)
        
        # Load logo image
        if os.path.exists("assets/logo.png"):
            self.logo_image = ctk.CTkImage(light_image=Image.open("assets/logo.png"),
                                          dark_image=Image.open("assets/logo.png"),
                                          size=(40, 40))
            self.logo_label = ctk.CTkLabel(self.navigation_frame, image=self.logo_image, text="")
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # App name label
        self.app_name = ctk.CTkLabel(self.navigation_frame, text=self.config["app_name"],
                                    font=ctk.CTkFont(size=20, weight="bold"))
        self.app_name.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Navigation buttons
        self.sessions_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                           text="Sessions", command=self.show_sessions_view)
        self.sessions_button.grid(row=2, column=0, sticky="ew")
        
        self.players_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                          text="Players", command=self.show_players_view)
        self.players_button.grid(row=3, column=0, sticky="ew")
        
        self.stats_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                        text="Statistics", command=self.show_stats_view)
        self.stats_button.grid(row=4, column=0, sticky="ew")
        
        # Settings button at bottom
        self.settings_button = ctk.CTkButton(self.navigation_frame, corner_radius=0, height=40,
                                           text="Settings", command=self.show_settings_view)
        self.settings_button.grid(row=6, column=0, sticky="ew", padx=20, pady=20)
        
        # Create main frame for content with proper expansion
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Configure main_frame to expand with window
        self.main_frame.grid_columnconfigure(0, weight=1)  # Content should expand horizontally
        self.main_frame.grid_rowconfigure(0, weight=1)  # Content should expand vertically
        
        # Initialize views (frames)
        self.sessions_view = self.session_manager.create_view(self.main_frame)
        self.players_view = self.player_manager.create_view(self.main_frame)
        self.stats_view = self.create_stats_view()
        self.settings_view = self.create_settings_view()
        
        # Show default view (sessions)
        self.show_sessions_view()
    
    def show_sessions_view(self):
        self.hide_all_frames()
        self.sessions_view.grid(row=0, column=0, sticky="nsew")
        self.sessions_button.configure(fg_color=self.config["accent_color"])
    
    def show_players_view(self):
        self.hide_all_frames()
        self.players_view.grid(row=0, column=0, sticky="nsew")
        self.players_button.configure(fg_color=self.config["accent_color"])
    
    def show_stats_view(self):
        self.hide_all_frames()
        self.stats_view.grid(row=0, column=0, sticky="nsew")
        self.stats_button.configure(fg_color=self.config["accent_color"])
    
    def show_settings_view(self):
        self.hide_all_frames()
        self.settings_view.grid(row=0, column=0, sticky="nsew")
        self.settings_button.configure(fg_color=self.config["accent_color"])
    
    def hide_all_frames(self):
        for frame in [self.sessions_view, self.players_view, self.stats_view, self.settings_view]:
            frame.grid_forget()
        
        for button in [self.sessions_button, self.players_button, self.stats_button, self.settings_button]:
            button.configure(fg_color="transparent")
    
    def create_stats_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(2, weight=1)  # Make stats container expandable
        
        # Header
        header = ctk.CTkLabel(frame, text="Statistics", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Stats content will be populated by the session manager
        # We'll add a refresh button and some stats display
        refresh_button = ctk.CTkButton(frame, text="Refresh Stats", 
                                      command=self.update_stats)
        refresh_button.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        # Container for stats - make it fill available space
        stats_container = ctk.CTkFrame(frame)
        stats_container.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        stats_container.grid_columnconfigure(0, weight=1)
        stats_container.grid_rowconfigure(0, weight=1)
        
        self.stats_container = stats_container
        
        return frame
    
    def create_settings_view(self):
        frame = ctk.CTkFrame(self.main_frame)
        frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header = ctk.CTkLabel(frame, text="Settings", font=ctk.CTkFont(size=24, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Appearance settings
        appearance_frame = ctk.CTkFrame(frame)
        appearance_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        appearance_label = ctk.CTkLabel(appearance_frame, text="Appearance Mode:", 
                                       font=ctk.CTkFont(weight="bold"))
        appearance_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        appearance_combobox = ctk.CTkComboBox(appearance_frame, values=["Light", "Dark", "System"])
        appearance_combobox.grid(row=0, column=1, padx=20, pady=10)
        appearance_combobox.set("Dark")
        appearance_combobox.configure(command=self.change_appearance_mode)
        
        # Google Sheets settings
        gsheets_frame = ctk.CTkFrame(frame)
        gsheets_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        gsheets_label = ctk.CTkLabel(gsheets_frame, text="Google Sheets:", 
                                    font=ctk.CTkFont(weight="bold"))
        gsheets_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        sync_button = ctk.CTkButton(gsheets_frame, text="Sync with Google Sheets", 
                                   command=self.sync_to_sheets)
        sync_button.grid(row=0, column=1, padx=20, pady=10)
        
        # Data management
        data_frame = ctk.CTkFrame(frame)
        data_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        data_label = ctk.CTkLabel(data_frame, text="Data Management:", 
                                 font=ctk.CTkFont(weight="bold"))
        data_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        export_button = ctk.CTkButton(data_frame, text="Export Data", 
                                     command=self.export_data)
        export_button.grid(row=0, column=1, padx=20, pady=10)
        
        import_button = ctk.CTkButton(data_frame, text="Import Data", 
                                     command=self.import_data)
        import_button.grid(row=0, column=2, padx=20, pady=10)
        
        # Payment settings
        payment_frame = ctk.CTkFrame(frame)
        payment_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        payment_title = ctk.CTkLabel(payment_frame, text="Payment Settings", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        payment_title.grid(row=0, column=0, padx=20, pady=10, sticky="w", columnspan=2)
        
        # PayPal Client ID
        api_key_label = ctk.CTkLabel(payment_frame, text="PayPal Client ID:")
        api_key_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        
        paypal_client_id_var = tk.StringVar(value=self.config.get("paypal_client_id", ""))
        api_key_entry = ctk.CTkEntry(payment_frame, width=300, textvariable=paypal_client_id_var)
        api_key_entry.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        
        # PayPal Client Secret
        client_secret_label = ctk.CTkLabel(payment_frame, text="PayPal Client Secret:")
        client_secret_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        
        paypal_client_secret_var = tk.StringVar(value=self.config.get("paypal_client_secret", ""))
        client_secret_entry = ctk.CTkEntry(payment_frame, width=300, textvariable=paypal_client_secret_var)
        client_secret_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        
        # PayPal Mode
        mode_label = ctk.CTkLabel(payment_frame, text="PayPal Mode:")
        mode_label.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        
        paypal_mode_var = tk.StringVar(value=self.config.get("paypal_mode", "sandbox"))
        mode_combobox = ctk.CTkComboBox(payment_frame, values=["sandbox", "live"], variable=paypal_mode_var)
        mode_combobox.grid(row=3, column=1, padx=20, pady=10, sticky="w")
        
        # Bank account name
        bank_name_label = ctk.CTkLabel(payment_frame, text="Bank Account Name:")
        bank_name_label.grid(row=4, column=0, padx=20, pady=10, sticky="w")
        
        bank_name_var = tk.StringVar(value=self.config.get("bank_account_name", ""))
        bank_name_entry = ctk.CTkEntry(payment_frame, width=300, textvariable=bank_name_var)
        bank_name_entry.grid(row=4, column=1, padx=20, pady=10, sticky="w")
        
        # Enable payments toggle
        payments_enabled_label = ctk.CTkLabel(payment_frame, text="Enable Payments:")
        payments_enabled_label.grid(row=5, column=0, padx=20, pady=10, sticky="w")
        
        payments_enabled_var = tk.BooleanVar(value=self.config.get("payment_enabled", False))
        payments_enabled_switch = ctk.CTkSwitch(payment_frame, text="", variable=payments_enabled_var)
        payments_enabled_switch.grid(row=5, column=1, padx=20, pady=10, sticky="w")
        
        # Save payment settings
        def save_payment_settings():
            self.config["paypal_client_id"] = paypal_client_id_var.get()
            self.config["paypal_client_secret"] = paypal_client_secret_var.get()
            self.config["paypal_mode"] = paypal_mode_var.get()
            self.config["bank_account_name"] = bank_name_var.get()
            self.config["payment_enabled"] = payments_enabled_var.get()
            
            # Save to config file
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            
            # Reinitialize payment manager if needed
            if hasattr(self.session_manager, "payment_enabled"):
                self.session_manager.payment_enabled = self.config["payment_enabled"]
                if self.config["payment_enabled"]:
                    from paypal_integration import PayPalPaymentManager
                    self.session_manager.payment_manager = PayPalPaymentManager(
                        self.config["paypal_client_id"],
                        self.config["paypal_client_secret"],
                        self.config["paypal_mode"],
                        app=self  # Pass app reference here
                    )
            
            utils.show_message("Settings Saved", "Payment settings have been saved.")
        
        save_payment_btn = ctk.CTkButton(payment_frame, text="Save Payment Settings", 
                                       command=save_payment_settings)
        save_payment_btn.grid(row=6, column=0, padx=20, pady=20, columnspan=2)
        
        return frame
    
    def change_appearance_mode(self, mode):
        ctk.set_appearance_mode(mode)
    
    def sync_to_sheets(self):
        if self.sheets_manager:
            try:
                utils.debug_log("Starting Google Sheets sync...")
                player_data = self.player_manager.get_all_players()
                session_data = self.session_manager.get_all_sessions()
                
                utils.debug_log(f"Syncing {len(player_data)} players and {len(session_data)} sessions")
                
                # Print out the sheet name we're connecting to
                utils.debug_log(f"Connecting to sheet: {self.config['google_sheet_name']}")
                
                self.sheets_manager.update_sheets(player_data, session_data)
                utils.show_message("Success", "Data synchronized with Google Sheets successfully!")
                
                # Show the user where to find the sheet
                utils.show_message("Sheet Location", 
                                 "Your data has been uploaded to Google Sheets.\n\n"
                                 "To view it, go to Google Drive in your browser and look for a spreadsheet "
                                 f"named '{self.config['google_sheet_name']}'.")
                
            except Exception as e:
                error_message = f"Failed to sync with Google Sheets: {str(e)}"
                utils.debug_log(error_message)
                utils.show_error("Sync Error", error_message)
        else:
            utils.show_error("Not Available", "Google Sheets integration is not available.")
    
    def update_stats(self):
        # Clear existing stats
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        # Get stats data
        players = self.player_manager.get_all_players()
        sessions = self.session_manager.get_all_sessions()
        
        if not players:
            no_data = ctk.CTkLabel(self.stats_container, text="No player data available")
            no_data.grid(row=0, column=0, padx=20, pady=20)
            return
            
        # Create a scrollable frame for player stats - make it fill available space
        player_stats_frame = ctk.CTkScrollableFrame(self.stats_container, label_text="Player Stats")
        player_stats_frame.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
        
        # Configure columns with appropriate weights
        for i in range(6):  # For the 6 columns you have
            player_stats_frame.grid_columnconfigure(i, weight=1 if i in [0, 4, 5] else 0)
            # Columns with text that should expand have weight=1, numeric columns have weight=0
        
        # Headers
        headers = ["Player", "Sessions", "Total Buy-ins", "Total Cash-outs", "Profit/Loss", "Avg. Profit Per Session"]
        for i, header in enumerate(headers):
            lbl = ctk.CTkLabel(player_stats_frame, text=header, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Player stats
        for i, player in enumerate(players):
            name_lbl = ctk.CTkLabel(player_stats_frame, text=player["name"])
            name_lbl.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            
            # Calculate player stats
            player_sessions = 0
            total_buyins = 0
            total_cashouts = 0
            
            for session in sessions:
                for p in session["players"]:
                    if p["id"] == player["id"]:
                        player_sessions += 1
                        total_buyins += p["buyin"]
                        total_cashouts += p["cashout"]
            
            profit = total_cashouts - total_buyins
            avg_profit = profit / player_sessions if player_sessions > 0 else 0
            
            sessions_lbl = ctk.CTkLabel(player_stats_frame, text=str(player_sessions))
            sessions_lbl.grid(row=i+1, column=1, padx=10, pady=5, sticky="w")
            
            buyins_lbl = ctk.CTkLabel(player_stats_frame, text=f"£{total_buyins:.2f}")
            buyins_lbl.grid(row=i+1, column=2, padx=10, pady=5, sticky="w")
            
            cashouts_lbl = ctk.CTkLabel(player_stats_frame, text=f"£{total_cashouts:.2f}")
            cashouts_lbl.grid(row=i+1, column=3, padx=10, pady=5, sticky="w")
            
            profit_lbl = ctk.CTkLabel(player_stats_frame, 
                                     text=f"£{profit:.2f}", 
                                     text_color="green" if profit >= 0 else "red")
            profit_lbl.grid(row=i+1, column=4, padx=10, pady=5, sticky="w")
            
            avg_lbl = ctk.CTkLabel(player_stats_frame, 
                                  text=f"£{avg_profit:.2f}", 
                                  text_color="green" if avg_profit >= 0 else "red")
            avg_lbl.grid(row=i+1, column=5, padx=10, pady=5, sticky="w")
    
    def export_data(self):
        data = {
            "players": self.player_manager.get_all_players(),
            "sessions": self.session_manager.get_all_sessions()
        }
        
        filepath = tk.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Export Poker Tracker Data"
        )
        
        if filepath:
            try:
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=4)
                utils.show_message("Success", "Data exported successfully!")
            except Exception as e:
                utils.show_error("Export Error", f"Failed to export data: {str(e)}")
    
    def import_data(self):
        filepath = tk.filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Import Poker Tracker Data"
        )
        
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if "players" in data and "sessions" in data:
                    self.player_manager.load_players(data["players"])
                    self.session_manager.load_sessions(data["sessions"])
                    utils.show_message("Success", "Data imported successfully!")
                    self.show_sessions_view()  # Refresh view
                else:
                    utils.show_error("Import Error", "Invalid data format.")
            except Exception as e:
                utils.show_error("Import Error", f"Failed to import data: {str(e)}")
    
    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                if "players" in data:
                    self.player_manager.load_players(data["players"])
                if "sessions" in data:
                    self.session_manager.load_sessions(data["sessions"])
                if "current_session" in data:
                    self.session_manager.set_current_session(data["current_session"])
            except Exception as e:
                print(f"Error loading data: {e}")
    
    def save_data(self):
        data = {
            "players": self.player_manager.get_all_players(),
            "sessions": self.session_manager.get_all_sessions(),
            "current_session": self.session_manager.get_current_session()
        }
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def on_close(self):
        self.save_data()
        self.destroy()

if __name__ == "__main__":
    app = PokerApp()
    app.mainloop() 
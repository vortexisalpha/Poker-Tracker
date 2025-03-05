import customtkinter as ctk
from tkinter import messagebox
import datetime
import uuid
import utils
import tkinter as tk
from paypal_integration import PayPalPaymentManager
from PIL import Image
import io

class SessionManager:
    def __init__(self, app, player_manager):
        self.app = app
        self.player_manager = player_manager
        self.sessions = []
        self.current_session = None
        
        # Initialize PayPal payment manager - pass app as parameter
        paypal_client_id = self.app.config.get("paypal_client_id")
        paypal_client_secret = self.app.config.get("paypal_client_secret")
        paypal_mode = self.app.config.get("paypal_mode", "sandbox")
        self.payment_enabled = self.app.config.get("payment_enabled", False)
        if self.payment_enabled:
            self.payment_manager = PayPalPaymentManager(
                paypal_client_id, 
                paypal_client_secret,
                paypal_mode,
                app=self.app  # Pass app reference here
            )
        else:
            self.payment_manager = None
    
    def create_view(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid_columnconfigure(0, weight=1)
        
        # Ensure rows are properly weighted
        frame.grid_rowconfigure(1, weight=0)  # Current session frame (fixed height)
        frame.grid_rowconfigure(3, weight=1)  # Sessions list (expandable)
        
        # Header with new session button
        header_frame = ctk.CTkFrame(frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        header_frame.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(header_frame, text="Poker Sessions", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        new_session_btn = ctk.CTkButton(header_frame, text="+ New Session", 
                                      command=self.create_new_session)
        new_session_btn.grid(row=0, column=1, sticky="e", padx=10, pady=10)
        
        # Current session display - keep fixed height but expand horizontally
        self.current_session_frame = ctk.CTkFrame(frame)
        self.current_session_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.current_session_frame.grid_columnconfigure(0, weight=1)  # Make content expand horizontally
        
        # Previous sessions list - expand to fill available space
        history_label = ctk.CTkLabel(frame, text="Session History", font=ctk.CTkFont(size=16, weight="bold"))
        history_label.grid(row=2, column=0, sticky="nw", padx=20, pady=(20, 0))
        
        sessions_frame = ctk.CTkScrollableFrame(frame)
        sessions_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=20)
        sessions_frame.grid_columnconfigure(0, weight=1)  # Make content expand horizontally
        
        self.sessions_frame = sessions_frame
        
        # Update the views
        self.refresh_current_session()
        self.refresh_sessions_list()
        
        return frame
    
    def refresh_current_session(self):
        # Clear current session frame
        for widget in self.current_session_frame.winfo_children():
            widget.destroy()
            
        if not self.current_session:
            no_session = ctk.CTkLabel(self.current_session_frame, 
                                    text="No active session. Start a new session to begin tracking.")
            no_session.pack(padx=20, pady=20)
            return
            
        # Configure grid for current session
        self.current_session_frame.grid_columnconfigure(0, weight=1)
        
        # Session header
        header_frame = ctk.CTkFrame(self.current_session_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        date_formatted = datetime.datetime.fromisoformat(self.current_session["date"]).strftime("%B %d, %Y")
        
        session_title = ctk.CTkLabel(header_frame, 
                                   text=f"Current Session: {self.current_session['name']} - {date_formatted}", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        session_title.grid(row=0, column=0, sticky="w")
        
        # Action buttons
        actions_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e")
        
        add_player_btn = ctk.CTkButton(actions_frame, text="Add Player", width=100,
                                     command=self.show_add_player_to_session)
        add_player_btn.grid(row=0, column=0, padx=5)
        
        end_session_btn = ctk.CTkButton(actions_frame, text="End Session", width=100,
                                      command=self.end_current_session)
        end_session_btn.grid(row=0, column=1, padx=5)
        
        # Player list
        players_frame = ctk.CTkFrame(self.current_session_frame)
        players_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # Column headers
        headers = ["Player", "Buy-in", "Rebuys", "Total In", "Cash Out", "Profit/Loss", "Actions"]
        for i, header in enumerate(headers):
            lbl = ctk.CTkLabel(players_frame, text=header, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Player rows
        session_total_buyin = 0
        session_total_cashout = 0
        
        for i, player in enumerate(self.current_session["players"]):
            player_obj = self.player_manager.get_player_by_id(player["id"])
            if not player_obj:
                continue  # Skip if player was deleted
                
            name_lbl = ctk.CTkLabel(players_frame, text=player_obj["name"])
            name_lbl.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            
            buyin_lbl = ctk.CTkLabel(players_frame, text=f"£{player['buyin']:.2f}")
            buyin_lbl.grid(row=i+1, column=1, padx=10, pady=5, sticky="w")
            
            rebuys = player.get('rebuys', 0)
            rebuys_lbl = ctk.CTkLabel(players_frame, text=f"£{rebuys:.2f}")
            rebuys_lbl.grid(row=i+1, column=2, padx=10, pady=5, sticky="w")
            
            total_in = player['buyin'] + rebuys
            total_in_lbl = ctk.CTkLabel(players_frame, text=f"£{total_in:.2f}")
            total_in_lbl.grid(row=i+1, column=3, padx=10, pady=5, sticky="w")
            
            cashout = player.get('cashout', 0)
            cashout_lbl = ctk.CTkLabel(players_frame, text=f"£{cashout:.2f}")
            cashout_lbl.grid(row=i+1, column=4, padx=10, pady=5, sticky="w")
            
            profit = cashout - total_in
            profit_color = "green" if profit >= 0 else "red"
            profit_lbl = ctk.CTkLabel(players_frame, text=f"£{profit:.2f}", text_color=profit_color)
            profit_lbl.grid(row=i+1, column=5, padx=10, pady=5, sticky="w")
            
            # Action buttons for player
            player_actions = ctk.CTkFrame(players_frame, fg_color="transparent")
            player_actions.grid(row=i+1, column=6, padx=10, pady=5)
            
            edit_btn = ctk.CTkButton(player_actions, text="Edit", width=60,
                                   command=lambda p=player, idx=i: self.show_edit_player_in_session(p, idx))
            edit_btn.grid(row=0, column=0, padx=5)
            
            remove_btn = ctk.CTkButton(player_actions, text="Remove", width=60, fg_color="#E74C3C",
                                     command=lambda p=player, idx=i: self.remove_player_from_session(idx))
            remove_btn.grid(row=0, column=1, padx=5)
            
            # Update session totals
            session_total_buyin += total_in
            session_total_cashout += cashout
        
        # Session summary
        summary_frame = ctk.CTkFrame(self.current_session_frame)
        summary_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        summary_lbl = ctk.CTkLabel(summary_frame, text="Session Summary:", 
                                  font=ctk.CTkFont(weight="bold"))
        summary_lbl.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        total_buyin_lbl = ctk.CTkLabel(summary_frame, text=f"Total Buy-ins: £{session_total_buyin:.2f}")
        total_buyin_lbl.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        total_cashout_lbl = ctk.CTkLabel(summary_frame, text=f"Total Cash-outs: £{session_total_cashout:.2f}")
        total_cashout_lbl.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        
        balance = session_total_cashout - session_total_buyin
        balance_color = "green" if balance >= 0 else "red"
        balance_text = "Balance (should be zero): "
        balance_lbl = ctk.CTkLabel(summary_frame, text=f"{balance_text}£{balance:.2f}", 
                                 text_color=balance_color)
        balance_lbl.grid(row=0, column=3, padx=10, pady=5, sticky="w")
    
    def refresh_sessions_list(self):
        # Clear sessions list
        for widget in self.sessions_frame.winfo_children():
            widget.destroy()
            
        # If there are no completed sessions
        if not self.sessions:
            no_sessions = ctk.CTkLabel(self.sessions_frame, 
                                     text="No completed sessions yet.")
            no_sessions.grid(row=0, column=0, padx=20, pady=20)
            return
            
        # Create list of sessions
        for i, session in enumerate(self.sessions):
            session_frame = ctk.CTkFrame(self.sessions_frame)
            session_frame.grid(row=i, column=0, sticky="ew", padx=10, pady=5)
            session_frame.grid_columnconfigure(1, weight=1)
            
            date_formatted = datetime.datetime.fromisoformat(session["date"]).strftime("%B %d, %Y")
            
            # Session info
            name_lbl = ctk.CTkLabel(session_frame, 
                                  text=f"{session['name']} - {date_formatted}", 
                                  font=ctk.CTkFont(weight="bold"))
            name_lbl.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            # Calculate session details
            player_count = len(session["players"])
            total_buyin = sum(p["buyin"] + p.get("rebuys", 0) for p in session["players"])
            total_cashout = sum(p.get("cashout", 0) for p in session["players"])
            
            details_lbl = ctk.CTkLabel(session_frame, 
                                     text=f"Players: {player_count} | Total: £{total_buyin:.2f}")
            details_lbl.grid(row=0, column=1, padx=10, pady=5, sticky="w")
            
            # Action buttons
            actions_frame = ctk.CTkFrame(session_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=2, padx=10, pady=5, sticky="e")
            
            view_btn = ctk.CTkButton(actions_frame, text="View", width=60,
                                   command=lambda s=session: self.view_session_details(s))
            view_btn.grid(row=0, column=0, padx=5)
            
            delete_btn = ctk.CTkButton(actions_frame, text="Delete", width=60, fg_color="#E74C3C",
                                     command=lambda s=session, idx=i: self.delete_session(idx))
            delete_btn.grid(row=0, column=1, padx=5)
    
    def create_new_session(self):
        if self.current_session:
            utils.show_error("Active Session", "You already have an active session. End the current session before starting a new one.")
            return
        
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("New Poker Session")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        utils.center_window(dialog, self.app)
        
        # Session name
        name_label = ctk.CTkLabel(dialog, text="Session Name:")
        name_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")
        
        name_entry = ctk.CTkEntry(dialog, width=200)
        name_entry.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="ew")
        name_entry.insert(0, f"Poker Night {datetime.datetime.now().strftime('%m/%d/%Y')}")
        name_entry.focus()
        
        # Create session function
        def create_session():
            name = name_entry.get().strip()
            if not name:
                utils.show_error("Error", "Session name cannot be empty", parent=dialog)
                return
            
            session = {
                "id": str(uuid.uuid4()),
                "name": name,
                "date": datetime.datetime.now().isoformat(),
                "players": []
            }
            
            self.current_session = session
            self.refresh_current_session()
            dialog.destroy()
            
            # Prompt to add players
            self.show_add_player_to_session()
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=100, 
                                 command=dialog.destroy)
        cancel_btn.grid(row=0, column=0, padx=10)
        
        create_btn = ctk.CTkButton(button_frame, text="Create Session", width=100, 
                                 command=create_session)
        create_btn.grid(row=0, column=1, padx=10)
    
    def show_add_player_to_session(self):
        if not self.current_session:
            utils.show_error("Error", "No active session.")
            return
        
        # Get available players (not already in the session)
        current_player_ids = [p["id"] for p in self.current_session["players"]]
        available_players = [p for p in self.player_manager.get_all_players() 
                            if p["id"] not in current_player_ids]
        
        if not available_players:
            utils.show_message("No Players", "All players are already in this session. Create new players first.")
            return
        
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Add Player to Session")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.grab_set()
        
        utils.center_window(dialog, self.app)
        
        # Player selection
        player_label = ctk.CTkLabel(dialog, text="Select Player:")
        player_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")
        
        player_var = ctk.StringVar()
        player_names = [p["name"] for p in available_players]
        player_combobox = ctk.CTkComboBox(dialog, values=player_names, variable=player_var)
        player_combobox.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="ew")
        
        if player_names:
            player_combobox.set(player_names[0])
        
        # Buy-in amount
        buyin_label = ctk.CTkLabel(dialog, text="Buy-in Amount:")
        buyin_label.grid(row=1, column=0, padx=20, pady=(20, 0), sticky="w")
        
        # Use a tkinter.StringVar to track input changes
        buyin_var = tk.StringVar(value="10.00")  # Changed default from 100 to 10
        
        # Create a custom validation command 
        vcmd = (dialog.register(utils.validate_decimal_input), '%P')
        
        buyin_entry = ctk.CTkEntry(dialog, textvariable=buyin_var)
        # Remove validation on the entry widget as it might be too restrictive
        # Just validate when submitting
        buyin_entry.grid(row=1, column=1, padx=20, pady=(20, 0), sticky="ew")
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=100, 
                                 command=dialog.destroy)
        cancel_btn.grid(row=0, column=0, padx=10)
        
        def add_player():
            player_name = player_var.get()
            
            try:
                buy_in = float(buyin_var.get())
                if buy_in <= 0:
                    utils.show_error("Invalid Buy-in", "Buy-in amount must be greater than 0.", parent=dialog)
                    return
            except ValueError:
                utils.show_error("Invalid Buy-in", "Please enter a valid buy-in amount.", parent=dialog)
                return
            
            # Find selected player
            selected_player = None
            for p in available_players:
                if p["name"] == player_name:
                    selected_player = p
                    break
            
            if not selected_player:
                utils.show_error("Error", "Please select a player.", parent=dialog)
                return
            
            # Add player to session
            self.current_session["players"].append({
                "id": selected_player["id"],
                "buyin": buy_in,
                "rebuys": 0,
                "cashout": 0
            })
            
            # Refresh view
            self.refresh_current_session()
            dialog.destroy()
        
        add_btn = ctk.CTkButton(button_frame, text="Add Player", width=100, 
                              command=add_player)
        add_btn.grid(row=0, column=1, padx=10)
    
    def show_edit_player_in_session(self, player, player_index):
        if not self.current_session:
            return
        
        player_obj = self.player_manager.get_player_by_id(player["id"])
        if not player_obj:
            utils.show_error("Error", "Player not found")
            return
        
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Edit Player: {player_obj['name']}")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        utils.center_window(dialog, self.app)
        
        # Buy-in amount
        buyin_label = ctk.CTkLabel(dialog, text="Buy-in Amount (£):")
        buyin_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")
        
        buyin_entry = ctk.CTkEntry(dialog, width=200)
        buyin_entry.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="ew")
        buyin_entry.insert(0, f"{player['buyin']:.2f}")
        
        # Rebuys amount
        rebuys_label = ctk.CTkLabel(dialog, text="Rebuys Amount (£):")
        rebuys_label.grid(row=1, column=0, padx=20, pady=(20, 0), sticky="w")
        
        rebuys_entry = ctk.CTkEntry(dialog, width=200)
        rebuys_entry.grid(row=1, column=1, padx=20, pady=(20, 0), sticky="ew")
        rebuys_entry.insert(0, f"{player.get('rebuys', 0):.2f}")
        
        # Cash-out amount
        cashout_label = ctk.CTkLabel(dialog, text="Cash-out Amount (£):")
        cashout_label.grid(row=2, column=0, padx=20, pady=(20, 0), sticky="w")
        
        cashout_entry = ctk.CTkEntry(dialog, width=200)
        cashout_entry.grid(row=2, column=1, padx=20, pady=(20, 0), sticky="ew")
        cashout_entry.insert(0, f"{player.get('cashout', 0):.2f}")
        
        # Update player function
        def update_player_in_session():
            try:
                buyin = float(buyin_entry.get())
                rebuys = float(rebuys_entry.get())
                cashout = float(cashout_entry.get())
                
                if buyin < 0 or rebuys < 0 or cashout < 0:
                    raise ValueError("Values cannot be negative")
                
            except ValueError as e:
                utils.show_error("Error", f"Invalid amount: {str(e)}", parent=dialog)
                return
            
            # Update player in session
            self.current_session["players"][player_index].update({
                "buyin": buyin,
                "rebuys": rebuys,
                "cashout": cashout
            })
            
            self.refresh_current_session()
            dialog.destroy()
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=100, 
                                 command=dialog.destroy)
        cancel_btn.grid(row=0, column=0, padx=10)
        
        update_btn = ctk.CTkButton(button_frame, text="Update", width=100, 
                                 command=update_player_in_session)
        update_btn.grid(row=0, column=1, padx=10)
    
    def remove_player_from_session(self, player_index):
        if not self.current_session:
            return
        
        player = self.current_session["players"][player_index]
        player_obj = self.player_manager.get_player_by_id(player["id"])
        
        if not player_obj:
            player_name = "Unknown Player"
        else:
            player_name = player_obj["name"]
        
        confirm = messagebox.askyesno("Remove Player", 
                                     f"Are you sure you want to remove {player_name} from the session?")
        
        if confirm:
            self.current_session["players"].pop(player_index)
            self.refresh_current_session()
    
    def end_current_session(self):
        if not self.current_session:
            utils.show_error("No Active Session", "There is no active session to end.")
            return
        
        # Calculate balance
        total_buyin = sum(p["buyin"] + p.get("rebuys", 0) for p in self.current_session["players"])
        total_cashout = sum(p.get("cashout", 0) for p in self.current_session["players"])
        balance = total_cashout - total_buyin
        
        if abs(balance) > 0.01:  # Allow a small rounding error
            confirm = messagebox.askyesno("Unbalanced Session", 
                                        f"The session is unbalanced by £{balance:.2f}. "
                                        f"Are you sure you want to end it?")
            if not confirm:
                return
        
        # Add to completed sessions and clear current
        self.current_session["status"] = "completed"
        current_session = self.current_session
        self.sessions.append(current_session)
        self.current_session = None
        
        # Refresh views
        self.refresh_current_session()
        self.refresh_sessions_list()
        
        # Ask if user wants to show payment/distribution QR codes
        if self.payment_enabled:
            action = messagebox.askyesnocancel(
                "Session Ended", 
                "Session has ended successfully. Would you like to:\n\n"
                "Yes = Collect payments from players who lost money\n"
                "No = Distribute winnings to players who won money\n"
                "Cancel = Do nothing"
            )
            
            if action is True:  # Yes - Collect payments
                self.show_payment_qr_codes(current_session)
            elif action is False:  # No - Distribute winnings
                self.show_distribution_qr_codes(current_session)
    
    def view_session_details(self, session):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title(f"Session Details: {session['name']}")
        dialog.geometry("700x500")
        dialog.resizable(True, True)  # Allow dialog to be resized
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        utils.center_window(dialog, self.app)
        
        # Configure dialog grid to be expandable
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)  # Let the player list expand
        
        # Session header
        date_formatted = datetime.datetime.fromisoformat(session["date"]).strftime("%B %d, %Y")
        
        header = ctk.CTkLabel(dialog, text=f"{session['name']} - {date_formatted}",
                            font=ctk.CTkFont(size=18, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Players frame - make it fill available space
        players_frame = ctk.CTkScrollableFrame(dialog)
        players_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Headers
        headers = ["Player", "Buy-in", "Rebuys", "Total In", "Cash Out", "Profit/Loss"]
        for i, header in enumerate(headers):
            lbl = ctk.CTkLabel(players_frame, text=header, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, padx=10, pady=5, sticky="w")
        
        # Player rows
        total_buyin = 0
        total_rebuys = 0
        total_cashout = 0
        
        for i, player in enumerate(session["players"]):
            player_obj = self.player_manager.get_player_by_id(player["id"])
            if not player_obj:
                player_name = "Unknown Player"
            else:
                player_name = player_obj["name"]
                
            name_lbl = ctk.CTkLabel(players_frame, text=player_name)
            name_lbl.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            
            buyin_lbl = ctk.CTkLabel(players_frame, text=f"£{player['buyin']:.2f}")
            buyin_lbl.grid(row=i+1, column=1, padx=10, pady=5, sticky="w")
            
            rebuys = player.get('rebuys', 0)
            rebuys_lbl = ctk.CTkLabel(players_frame, text=f"£{rebuys:.2f}")
            rebuys_lbl.grid(row=i+1, column=2, padx=10, pady=5, sticky="w")
            
            total_in = player['buyin'] + rebuys
            total_in_lbl = ctk.CTkLabel(players_frame, text=f"£{total_in:.2f}")
            total_in_lbl.grid(row=i+1, column=3, padx=10, pady=5, sticky="w")
            
            cashout = player.get('cashout', 0)
            cashout_lbl = ctk.CTkLabel(players_frame, text=f"£{cashout:.2f}")
            cashout_lbl.grid(row=i+1, column=4, padx=10, pady=5, sticky="w")
            
            profit = cashout - total_in
            profit_color = "green" if profit >= 0 else "red"
            profit_lbl = ctk.CTkLabel(players_frame, text=f"£{profit:.2f}", text_color=profit_color)
            profit_lbl.grid(row=i+1, column=5, padx=10, pady=5, sticky="w")
            
            # Update totals
            total_buyin += player['buyin']
            total_rebuys += rebuys
            total_cashout += cashout
        
        # Summary frame
        summary_frame = ctk.CTkFrame(dialog)
        summary_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        
        total_players = len(session["players"])
        total_in = total_buyin + total_rebuys
        balance = total_cashout - total_in
        
        summary_info = (
            f"Total Players: {total_players}  |  "
            f"Total Buy-ins: £{total_buyin:.2f}  |  "
            f"Total Rebuys: £{total_rebuys:.2f}  |  "
            f"Total In: £{total_in:.2f}  |  "
            f"Total Cash-out: £{total_cashout:.2f}  |  "
            f"Balance: £{balance:.2f}"
        )
        
        summary_lbl = ctk.CTkLabel(summary_frame, text=summary_info)
        summary_lbl.pack(padx=10, pady=10)
        
        # Close button
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=3, column=0, pady=20)
        
        if self.payment_enabled:
            payment_btn = ctk.CTkButton(button_frame, text="Collect Payments", width=140,
                                      command=lambda: self.show_payment_qr_codes(session))
            payment_btn.grid(row=0, column=0, padx=10)
            
            distribute_btn = ctk.CTkButton(button_frame, text="Distribute Winnings", width=140,
                                         command=lambda: self.show_distribution_qr_codes(session))
            distribute_btn.grid(row=0, column=1, padx=10)
        
        close_btn = ctk.CTkButton(button_frame, text="Close", width=100, 
                                command=dialog.destroy)
        close_btn.grid(row=0, column=2, padx=10)
    
    def delete_session(self, session_index):
        confirm = messagebox.askyesno("Delete Session", 
                                     "Are you sure you want to delete this session?\nThis action cannot be undone.")
        
        if confirm:
            self.sessions.pop(session_index)
            self.refresh_sessions_list()
    
    def get_all_sessions(self):
        all_sessions = self.sessions.copy()
        if self.current_session:
            all_sessions.append(self.current_session)
        return all_sessions
    
    def get_current_session(self):
        return self.current_session
    
    def set_current_session(self, session):
        self.current_session = session
        # Only refresh UI if it has been created already
        if hasattr(self, 'current_session_frame'):
            self.refresh_current_session()
    
    def load_sessions(self, sessions):
        # Filter out any possible current session
        self.sessions = [s for s in sessions if s.get("status") != "current"]
        
        # Check for a current session
        current_sessions = [s for s in sessions if s.get("status") == "current"]
        if current_sessions:
            self.current_session = current_sessions[0]
        
        # Refresh views if they exist
        if hasattr(self, 'current_session_frame'):
            self.refresh_current_session()
        if hasattr(self, 'sessions_frame'):
            self.refresh_sessions_list()
    
    def show_payment_qr_codes(self, session):
        """Show payment QR codes for players who owe money"""
        if not self.payment_enabled or not self.payment_manager:
            utils.show_error("Payments Disabled", 
                           "Payment functionality is not enabled. Please add your PayPal credentials in settings.")
            return
        
        # Find players with negative balance
        debtors = []
        bank_account_name = self.app.config.get("bank_account_name", "Bank Account")
        
        for player in session["players"]:
            player_obj = self.player_manager.get_player_by_id(player["id"])
            if not player_obj:
                continue
            
            total_in = player["buyin"] + player.get("rebuys", 0)
            cashout = player.get("cashout", 0)
            profit = cashout - total_in
            
            if profit < 0:  # Player owes money
                debtors.append({
                    "name": player_obj["name"],
                    "amount": abs(profit),
                    "id": player["id"]
                })
        
        if not debtors:
            utils.show_message("No Payments Needed", 
                             "There are no players who need to make a payment.")
            return
        
        # Create payment links and QR codes
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Payment QR Codes")
        dialog.geometry("800x600")
        dialog.resizable(True, True)
        dialog.grab_set()
        
        utils.center_window(dialog, self.app)
        
        # Configure dialog grid
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkLabel(dialog, text="Payment QR Codes", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Create a scrollable frame for the QR codes
        qr_frame = ctk.CTkScrollableFrame(dialog)
        qr_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Set column weights
        num_cols = 3  # Show 3 QR codes per row
        for i in range(num_cols):
            qr_frame.grid_columnconfigure(i, weight=1)
        
        row = 0
        col = 0
        
        # Generate QR codes for each debtor
        for debtor in debtors:
            player_frame = ctk.CTkFrame(qr_frame)
            player_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Add player name and amount
            name_label = ctk.CTkLabel(player_frame, text=debtor["name"], 
                                    font=ctk.CTkFont(weight="bold"))
            name_label.pack(pady=(10, 0))
            
            amount_label = ctk.CTkLabel(player_frame, text=f"Owes: £{debtor['amount']:.2f}")
            amount_label.pack(pady=(0, 10))
            
            # Create payment link and QR code
            session_name = session.get("name", "Poker Session")
            date = session.get("date", "").split("T")[0]
            description = f"Payment for {session_name} on {date}"
            
            payment_url = self.payment_manager.create_payment_link(
                debtor["amount"], 
                description, 
                debtor["name"]
            )
            
            if payment_url:
                qr_data = self.payment_manager.generate_qr_code(payment_url)
                
                if qr_data:
                    # Convert QR code to CTkImage
                    img = Image.open(io.BytesIO(qr_data))
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 150))
                    
                    # Display QR code
                    qr_label = ctk.CTkLabel(player_frame, image=ctk_img, text="")
                    qr_label.pack(pady=10)
                    
                    # Keep a reference to avoid garbage collection
                    player_frame.image = ctk_img
                    
                    # Add payment link
                    link_text = ctk.CTkTextbox(player_frame, height=20, width=200, wrap="word")
                    link_text.insert("1.0", payment_url)
                    link_text.configure(state="disabled")
                    link_text.pack(pady=(0, 10), padx=10)
                    
                    # To pay label
                    pay_label = ctk.CTkLabel(player_frame, text=f"Pay to: {bank_account_name}")
                    pay_label.pack(pady=(0, 10))
                else:
                    error_label = ctk.CTkLabel(player_frame, text="Failed to generate QR code")
                    error_label.pack(pady=10)
            else:
                error_label = ctk.CTkLabel(player_frame, text="Failed to create payment link")
                error_label.pack(pady=10)
            
            # Move to next column or row
            col += 1
            if col >= num_cols:
                col = 0
                row += 1
        
        # Close button
        close_btn = ctk.CTkButton(dialog, text="Close", width=100, 
                                command=dialog.destroy)
        close_btn.grid(row=2, column=0, pady=20)
    
    def show_distribution_qr_codes(self, session):
        """Show QR codes for distributing winnings to profitable players"""
        if not self.payment_enabled or not self.payment_manager:
            utils.show_error("Payments Disabled", 
                           "Payment functionality is not enabled. Please add your PayPal credentials in settings.")
            return
        
        # Find players with positive balance (winners)
        winners = []
        bank_account_name = self.app.config.get("bank_account_name", "Bank Account")
        
        for player in session["players"]:
            player_obj = self.player_manager.get_player_by_id(player["id"])
            if not player_obj:
                continue
            
            total_in = player["buyin"] + player.get("rebuys", 0)
            cashout = player.get("cashout", 0)
            profit = cashout - total_in
            
            if profit > 0:  # Player won money
                winners.append({
                    "name": player_obj["name"],
                    "amount": profit,
                    "id": player["id"],
                    "email": player_obj.get("email", "")  # Get email if available
                })
        
        if not winners:
            utils.show_message("No Distributions Needed", 
                             "There are no players who won money in this session.")
            return
        
        # Create distribution links and QR codes
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Distribution QR Codes")
        dialog.geometry("800x600")
        dialog.resizable(True, True)
        dialog.grab_set()
        
        utils.center_window(dialog, self.app)
        
        # Configure dialog grid
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkLabel(dialog, text="Distribute Winnings", 
                            font=ctk.CTkFont(size=18, weight="bold"))
        header.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Create a scrollable frame for the QR codes
        qr_frame = ctk.CTkScrollableFrame(dialog)
        qr_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Set column weights
        num_cols = 3  # Show 3 QR codes per row
        for i in range(num_cols):
            qr_frame.grid_columnconfigure(i, weight=1)
        
        row = 0
        col = 0
        
        # Generate QR codes for each winner
        for winner in winners:
            player_frame = ctk.CTkFrame(qr_frame)
            player_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Add player name and amount
            name_label = ctk.CTkLabel(player_frame, text=winner["name"], 
                                    font=ctk.CTkFont(weight="bold"))
            name_label.pack(pady=(10, 0))
            
            amount_label = ctk.CTkLabel(player_frame, text=f"Wins: £{winner['amount']:.2f}")
            amount_label.pack(pady=(0, 10))
            
            # Create email input field
            email_frame = ctk.CTkFrame(player_frame, fg_color="transparent")
            email_frame.pack(fill="x", padx=10, pady=(0, 5))
            
            email_label = ctk.CTkLabel(email_frame, text="Email:")
            email_label.pack(side="left", padx=(0, 5))
            
            email_var = tk.StringVar(value=winner.get("email", ""))
            email_entry = ctk.CTkEntry(email_frame, width=140, textvariable=email_var)
            email_entry.pack(side="left", fill="x", expand=True)
            
            # Store the email variable for later use
            winner["email_var"] = email_var
            
            # Create a container for the QR code and related content
            qr_container = ctk.CTkFrame(player_frame, fg_color="transparent")
            qr_container.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Function to generate payment link and QR code
            def generate_qr(winner_data, container):
                email = winner_data["email_var"].get().strip()
                if not email:
                    utils.show_error("Email Required", f"Please enter an email for {winner_data['name']}")
                    return
                
                # Clear existing content in QR container
                for widget in container.winfo_children():
                    widget.destroy()
                
                session_name = session.get("name", "Poker Session")
                date = session.get("date", "").split("T")[0]
                description = f"Winnings from {session_name} on {date}"
                
                # Create payment link to email
                payment_url = self.payment_manager.create_email_payment_link(
                    winner_data["amount"], 
                    email,
                    description
                )
                
                if payment_url:
                    qr_data = self.payment_manager.generate_qr_code(payment_url)
                    
                    if qr_data:
                        # Convert QR code to CTkImage
                        img = Image.open(io.BytesIO(qr_data))
                        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 150))
                        
                        # Display QR code
                        qr_label = ctk.CTkLabel(container, image=ctk_img, text="")
                        qr_label.pack(pady=10)
                        
                        # Keep a reference to avoid garbage collection
                        container.image = ctk_img
                        
                        # Add payment link
                        link_text = ctk.CTkTextbox(container, height=20, width=200, wrap="word")
                        link_text.insert("1.0", payment_url)
                        link_text.configure(state="disabled")
                        link_text.pack(pady=(0, 10), padx=10)
                        
                        # Payment instruction
                        pay_label = ctk.CTkLabel(container, 
                                              text=f"Send £{winner_data['amount']:.2f} to {email}")
                        pay_label.pack(pady=(0, 10))
                        
                        # Status message
                        status_label = ctk.CTkLabel(container, text="QR Code Generated!", 
                                                  text_color="green")
                        status_label.pack(pady=(0, 5))
                    else:
                        error_label = ctk.CTkLabel(container, text="Failed to generate QR code")
                        error_label.pack(pady=10)
                else:
                    error_label = ctk.CTkLabel(container, text="Failed to create payment link")
                    error_label.pack(pady=10)
            
            # Generate QR button
            generate_btn = ctk.CTkButton(player_frame, text="Generate QR", 
                                       command=lambda w=winner, c=qr_container: generate_qr(w, c))
            generate_btn.pack(pady=10)
            
            # Move to next column or row
            col += 1
            if col >= num_cols:
                col = 0
                row += 1
        
        # Close button
        close_btn = ctk.CTkButton(dialog, text="Close", width=100, 
                                command=dialog.destroy)
        close_btn.grid(row=2, column=0, pady=20) 
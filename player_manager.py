import customtkinter as ctk
import uuid
import utils
import tkinter as tk
import datetime

class PlayerManager:
    def __init__(self, app):
        self.app = app
        self.players = []
    
    def create_view(self, parent):
        frame = ctk.CTkFrame(parent)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)  # Make players list expandable
        
        # Header with add player button
        header_frame = ctk.CTkFrame(frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        header_frame.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(header_frame, text="Players", font=ctk.CTkFont(size=24, weight="bold"))
        title.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        add_button = ctk.CTkButton(header_frame, text="+ Add Player", 
                                 command=lambda: self.show_add_player())
        add_button.grid(row=0, column=1, sticky="e", padx=10, pady=10)
        
        # Players list - make it fill available space
        players_frame = ctk.CTkScrollableFrame(frame)
        players_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        players_frame.grid_columnconfigure(0, weight=1)  # First column (player name) should expand
        
        self.players_frame = players_frame
        self.refresh_players_view()
        
        return frame
    
    def refresh_players_view(self):
        # Clear all widgets
        for widget in self.players_frame.winfo_children():
            widget.destroy()
            
        if not self.players:
            no_players = ctk.CTkLabel(self.players_frame, text="No players yet. Add your first player!")
            no_players.grid(row=0, column=0, padx=20, pady=20)
            return
            
        # Add headers
        headers = ["Name", "Email", "Phone", "Actions"]
        for i, header in enumerate(headers):
            lbl = ctk.CTkLabel(self.players_frame, text=header, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=i, padx=10, pady=(0, 10), sticky="w")
        
        # Add player rows
        for i, player in enumerate(self.players):
            # Calculate player stats from sessions
            total_sessions = 0
            total_profit = 0
            
            if hasattr(self.app, 'session_manager'):
                sessions = self.app.session_manager.get_all_sessions()
                for session in sessions:
                    for p in session["players"]:
                        if p["id"] == player["id"]:
                            total_sessions += 1
                            total_profit += (p["cashout"] - p["buyin"])
            
            # Player name
            name_lbl = ctk.CTkLabel(self.players_frame, text=player["name"])
            name_lbl.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            
            # Email
            email_lbl = ctk.CTkLabel(self.players_frame, text=player.get("email", ""))
            email_lbl.grid(row=i+1, column=1, padx=10, pady=5, sticky="w")
            
            # Phone
            phone_lbl = ctk.CTkLabel(self.players_frame, text=player.get("phone", ""))
            phone_lbl.grid(row=i+1, column=2, padx=10, pady=5, sticky="w")
            
            # Actions buttons
            actions_frame = ctk.CTkFrame(self.players_frame, fg_color="transparent")
            actions_frame.grid(row=i+1, column=3, padx=10, pady=5)
            
            edit_btn = ctk.CTkButton(actions_frame, text="Edit", width=60,
                                   command=lambda p=player: self.show_edit_player_dialog(p))
            edit_btn.grid(row=0, column=0, padx=5)
            
            delete_btn = ctk.CTkButton(actions_frame, text="Delete", width=60, fg_color="#E74C3C",
                                     command=lambda p=player: self.confirm_delete_player(p))
            delete_btn.grid(row=0, column=1, padx=5)
    
    def show_add_player(self):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Add New Player")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal
        
        utils.center_window(dialog, self.app)
        
        # Setup grid
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_columnconfigure(1, weight=1)
        
        # Name field
        name_label = ctk.CTkLabel(dialog, text="Player Name:")
        name_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="e")
        
        name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(dialog, width=200, textvariable=name_var)
        name_entry.grid(row=0, column=1, padx=20, pady=(20, 10), sticky="w")
        name_entry.focus_set()  # Set focus
        
        # Email field (new)
        email_label = ctk.CTkLabel(dialog, text="Email (for payments):")
        email_label.grid(row=1, column=0, padx=20, pady=10, sticky="e")
        
        email_var = tk.StringVar()
        email_entry = ctk.CTkEntry(dialog, width=200, textvariable=email_var)
        email_entry.grid(row=1, column=1, padx=20, pady=10, sticky="w")
        
        # Phone field
        phone_label = ctk.CTkLabel(dialog, text="Phone:")
        phone_label.grid(row=2, column=0, padx=20, pady=10, sticky="e")
        
        phone_var = tk.StringVar()
        phone_entry = ctk.CTkEntry(dialog, width=200, textvariable=phone_var)
        phone_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")
        
        # Note field
        note_label = ctk.CTkLabel(dialog, text="Notes:")
        note_label.grid(row=3, column=0, padx=20, pady=10, sticky="ne")
        
        note_text = ctk.CTkTextbox(dialog, width=200, height=60)
        note_text.grid(row=3, column=1, padx=20, pady=10, sticky="w")
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Save function
        def save_player():
            name = name_var.get().strip()
            email = email_var.get().strip()  # Get email
            phone = phone_var.get().strip()
            note = note_text.get("1.0", tk.END).strip()
            
            if not name:
                utils.show_error("Input Error", "Player name is required", parent=dialog)
                return
            
            # Create player
            new_player = {
                "id": str(uuid.uuid4()),
                "name": name,
                "email": email,  # Add email
                "phone": phone,
                "note": note,
                "created_at": datetime.datetime.now().isoformat()
            }
            
            # Add to player list
            self.players.append(new_player)
            
            # Refresh view
            self.refresh_players_view()
            
            # Close dialog
            dialog.destroy()
        
        # Buttons
        save_btn = ctk.CTkButton(button_frame, text="Save", width=100, command=save_player)
        save_btn.grid(row=0, column=0, padx=10)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=100, 
                                 command=dialog.destroy)
        cancel_btn.grid(row=0, column=1, padx=10)
    
    def show_edit_player_dialog(self, player):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Edit Player")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        utils.center_window(dialog, self.app)
        
        # Player name
        name_label = ctk.CTkLabel(dialog, text="Player Name:")
        name_label.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")
        
        name_entry = ctk.CTkEntry(dialog, width=200)
        name_entry.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="ew")
        name_entry.insert(0, player["name"])
        name_entry.focus()
        
        # Update player function
        def update_player():
            name = name_entry.get().strip()
            if not name:
                utils.show_error("Error", "Player name cannot be empty", parent=dialog)
                return
            
            # Update player data
            for p in self.players:
                if p["id"] == player["id"]:
                    p["name"] = name
                    break
            
            self.refresh_players_view()
            dialog.destroy()
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=100, 
                                 command=dialog.destroy)
        cancel_btn.grid(row=0, column=0, padx=10)
        
        update_btn = ctk.CTkButton(button_frame, text="Update", width=100, 
                                 command=update_player)
        update_btn.grid(row=0, column=1, padx=10)
    
    def confirm_delete_player(self, player):
        dialog = ctk.CTkToplevel(self.app)
        dialog.title("Confirm Delete")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()  # Make dialog modal
        
        # Center the dialog
        utils.center_window(dialog, self.app)
        
        # Warning message
        msg = ctk.CTkLabel(dialog, 
                        text=f"Are you sure you want to delete player '{player['name']}'?\n"
                             f"This will not remove the player from existing sessions.")
        msg.pack(pady=(20, 0), padx=20)
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel", width=100, 
                                 command=dialog.destroy)
        cancel_btn.grid(row=0, column=0, padx=10)
        
        delete_btn = ctk.CTkButton(button_frame, text="Delete", width=100, 
                                 fg_color="#E74C3C", command=lambda: self.delete_player(player, dialog))
        delete_btn.grid(row=0, column=1, padx=10)
    
    def delete_player(self, player, dialog):
        self.players = [p for p in self.players if p["id"] != player["id"]]
        self.refresh_players_view()
        dialog.destroy()
    
    def get_all_players(self):
        return self.players
    
    def get_player_by_id(self, player_id):
        for player in self.players:
            if player["id"] == player_id:
                return player
        return None
    
    def load_players(self, players):
        self.players = players
        if hasattr(self, 'players_frame'):
            self.refresh_players_view() 
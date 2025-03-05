import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import utils
import os
import json

class GoogleSheetsManager:
    def __init__(self, credentials_file=None, sheet_name=None):
        # Try to get from environment variable if not provided
        self.sheet_name = sheet_name or os.environ.get("GOOGLE_SHEET_NAME")
        
        # Load credentials from environment variable if file not provided
        self.credentials_file = credentials_file
        
        if not credentials_file and "GOOGLE_CREDENTIALS_JSON" in os.environ:
            try:
                # Create temporary credentials file from environment variable
                import tempfile
                credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
                temp_file.write(credentials_json.encode())
                temp_file.close()
                self.credentials_file = temp_file.name
            except Exception as e:
                utils.debug_log(f"Failed to create credentials from environment: {str(e)}")
        
        # Set up the scope
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Connect to Google Sheets
        self.connect()
    
    def connect(self):
        """Connect to Google Sheets API"""
        try:
            utils.debug_log(f"Connecting to Google Sheets using credentials from {self.credentials_file}")
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, self.scope)
            self.client = gspread.authorize(credentials)
            
            # Try to open the spreadsheet, create it if it doesn't exist
            try:
                utils.debug_log(f"Attempting to open spreadsheet: {self.sheet_name}")
                self.spreadsheet = self.client.open(self.sheet_name)
                utils.debug_log(f"Successfully opened spreadsheet")
                
                # Verify required worksheets exist
                self.verify_worksheets()
            except gspread.SpreadsheetNotFound:
                utils.debug_log(f"Spreadsheet not found. Creating new one: {self.sheet_name}")
                self.spreadsheet = self.client.create(self.sheet_name)
                utils.debug_log(f"New spreadsheet created successfully")
                
                # Initialize the sheets
                self.initialize_sheets()
        except Exception as e:
            error_msg = f"Failed to connect to Google Sheets: {str(e)}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
    
    def verify_worksheets(self):
        """Verify all required worksheets exist, create them if not"""
        utils.debug_log("Verifying required worksheets exist")
        
        required_sheets = ["Players", "Sessions", "Session Details"]
        existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()]
        
        for sheet_name in required_sheets:
            if sheet_name not in existing_sheets:
                utils.debug_log(f"Creating missing worksheet: {sheet_name}")
                self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=10)
                
                # Initialize headers
                if sheet_name == "Players":
                    sheet = self.spreadsheet.worksheet(sheet_name)
                    sheet.update('A1:E1', [['Player ID', 'Name', 'Total Sessions', 'Total Buy-ins', 'Total Profit']])
                elif sheet_name == "Sessions":
                    sheet = self.spreadsheet.worksheet(sheet_name)
                    sheet.update('A1:F1', [['Session ID', 'Name', 'Date', 'Players', 'Total Buy-ins', 'Total Cash-outs']])
                elif sheet_name == "Session Details":
                    sheet = self.spreadsheet.worksheet(sheet_name)
                    sheet.update('A1:H1', [['Session ID', 'Player ID', 'Player Name', 'Buy-in', 'Rebuys', 'Total In', 'Cash-out', 'Profit/Loss']])
        
        utils.debug_log("Worksheet verification complete")
    
    def initialize_sheets(self):
        """Initialize the worksheets needed for the poker tracker"""
        utils.debug_log("Initializing worksheets")
        
        # Delete the default Sheet1 if it exists
        try:
            default_sheet = self.spreadsheet.worksheet("Sheet1")
            self.spreadsheet.del_worksheet(default_sheet)
            utils.debug_log("Deleted default Sheet1")
        except:
            utils.debug_log("Default Sheet1 not found or couldn't be deleted")
        
        # Create players sheet
        try:
            utils.debug_log("Creating Players worksheet")
            players_sheet = self.spreadsheet.add_worksheet(title="Players", rows=1000, cols=10)
            players_sheet.update('A1:E1', [['Player ID', 'Name', 'Total Sessions', 'Total Buy-ins', 'Total Profit']])
            utils.debug_log("Players worksheet created successfully")
        except Exception as e:
            utils.debug_log(f"Error creating Players sheet: {e}")
        
        # Create sessions sheet
        try:
            utils.debug_log("Creating Sessions worksheet")
            sessions_sheet = self.spreadsheet.add_worksheet(title="Sessions", rows=1000, cols=10)
            sessions_sheet.update('A1:F1', [['Session ID', 'Name', 'Date', 'Players', 'Total Buy-ins', 'Total Cash-outs']])
            utils.debug_log("Sessions worksheet created successfully")
        except Exception as e:
            utils.debug_log(f"Error creating Sessions sheet: {e}")
        
        # Create session details sheet
        try:
            utils.debug_log("Creating Session Details worksheet")
            details_sheet = self.spreadsheet.add_worksheet(title="Session Details", rows=1000, cols=10)
            details_sheet.update('A1:H1', [['Session ID', 'Player ID', 'Player Name', 'Buy-in', 'Rebuys', 'Total In', 'Cash-out', 'Profit/Loss']])
            utils.debug_log("Session Details worksheet created successfully")
        except Exception as e:
            utils.debug_log(f"Error creating Session Details sheet: {e}")
    
    def update_sheets(self, players, sessions):
        """Update all sheets with the current data"""
        utils.debug_log("Starting update of all sheets")
        
        # Verify sheets exist before updating
        self.verify_worksheets()
        
        try:
            utils.debug_log(f"Updating Players sheet with {len(players)} players")
            self.update_players_sheet(players, sessions)
            utils.debug_log("Players sheet updated successfully")
            
            utils.debug_log(f"Updating Sessions sheet with {len(sessions)} sessions")
            self.update_sessions_sheet(sessions)
            utils.debug_log("Sessions sheet updated successfully")
            
            utils.debug_log("Updating Session Details sheet")
            self.update_session_details_sheet(players, sessions)
            utils.debug_log("Session Details sheet updated successfully")
            
            utils.debug_log("All sheets updated successfully")
        except Exception as e:
            error_msg = f"Error updating sheets: {str(e)}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
    
    def update_players_sheet(self, players, sessions):
        """Update the Players sheet with current player data"""
        utils.debug_log(f"Getting Players worksheet")
        try:
            players_sheet = self.spreadsheet.worksheet("Players")
        except Exception as e:
            error_msg = f"Failed to get Players worksheet: {str(e)}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
        
        # Clear existing data (except header)
        try:
            utils.debug_log(f"Clearing existing data from Players sheet")
            rows = players_sheet.row_count
            if rows > 1:
                players_sheet.delete_rows(2, rows)
            utils.debug_log(f"Cleared {rows-1} rows from Players sheet")
        except Exception as e:
            error_msg = f"Error clearing Players sheet: {str(e)}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
        
        # Calculate player stats
        utils.debug_log(f"Calculating player stats")
        player_stats = []
        for player in players:
            total_sessions = 0
            total_buyins = 0
            total_cashouts = 0
            
            for session in sessions:
                for p in session["players"]:
                    if p["id"] == player["id"]:
                        total_sessions += 1
                        total_buyins += p["buyin"] + p.get("rebuys", 0)
                        total_cashouts += p.get("cashout", 0)
            
            profit = total_cashouts - total_buyins
            
            player_stats.append([
                player["id"], 
                player["name"], 
                total_sessions, 
                total_buyins, 
                profit
            ])
        
        # Update the sheet
        utils.debug_log(f"Appending {len(player_stats)} rows of player data")
        if player_stats:
            try:
                players_sheet.append_rows(player_stats)
                utils.debug_log(f"Successfully appended player data")
            except Exception as e:
                error_msg = f"Error appending player data: {str(e)}"
                utils.debug_log(error_msg)
                raise Exception(error_msg)
        else:
            utils.debug_log("No player data to append")
    
    def update_sessions_sheet(self, sessions):
        """Update the Sessions sheet with current session data"""
        utils.debug_log(f"Getting Sessions worksheet")
        try:
            sessions_sheet = self.spreadsheet.worksheet("Sessions")
        except Exception as e:
            error_msg = f"Failed to get Sessions worksheet: {str(e)}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
        
        # Clear existing data (except header)
        try:
            utils.debug_log(f"Clearing existing data from Sessions sheet")
            rows = sessions_sheet.row_count
            if rows > 1:
                sessions_sheet.delete_rows(2, rows)
            utils.debug_log(f"Cleared {rows-1} rows from Sessions sheet")
        except Exception as e:
            error_msg = f"Error clearing Sessions sheet: {str(e)}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
        
        # Format session data
        utils.debug_log(f"Formatting session data")
        session_data = []
        for session in sessions:
            date = datetime.datetime.fromisoformat(session["date"]).strftime("%Y-%m-%d")
            players_count = len(session["players"])
            total_buyin = sum(p["buyin"] + p.get("rebuys", 0) for p in session["players"])
            total_cashout = sum(p.get("cashout", 0) for p in session["players"])
            
            session_data.append([
                session["id"],
                session["name"],
                date,
                players_count,
                total_buyin,
                total_cashout
            ])
        
        # Update the sheet
        utils.debug_log(f"Appending {len(session_data)} rows of session data")
        if session_data:
            try:
                sessions_sheet.append_rows(session_data)
                utils.debug_log(f"Successfully appended session data")
            except Exception as e:
                error_msg = f"Error appending session data: {str(e)}"
                utils.debug_log(error_msg)
                raise Exception(error_msg)
        else:
            utils.debug_log("No session data to append")
    
    def update_session_details_sheet(self, players, sessions):
        """Update the Session Details sheet with detailed session data"""
        utils.debug_log(f"Getting Session Details worksheet")
        try:
            details_sheet = self.spreadsheet.worksheet("Session Details")
        except Exception as e:
            error_msg = f"Failed to get Session Details worksheet: {str(e)}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
        
        # Clear existing data (except header)
        try:
            utils.debug_log(f"Clearing existing data from Session Details sheet")
            rows = details_sheet.row_count
            if rows > 1:
                details_sheet.delete_rows(2, rows)
            utils.debug_log(f"Cleared {rows-1} rows from Session Details sheet")
        except Exception as e:
            error_msg = f"Error clearing Session Details sheet: {str(e)}"
            utils.debug_log(error_msg)
            raise Exception(error_msg)
        
        # Create a mapping of player IDs to names
        utils.debug_log(f"Creating player ID to name mapping")
        player_names = {player["id"]: player["name"] for player in players}
        
        # Format session details data
        utils.debug_log(f"Formatting session details data")
        details_data = []
        for session in sessions:
            for player in session["players"]:
                player_name = player_names.get(player["id"], "Unknown Player")
                rebuys = player.get("rebuys", 0)
                cashout = player.get("cashout", 0)
                total_in = player["buyin"] + rebuys
                profit = cashout - total_in
                
                details_data.append([
                    session["id"],
                    player["id"],
                    player_name,
                    player["buyin"],
                    rebuys,
                    total_in,
                    cashout,
                    profit
                ])
        
        # Update the sheet
        utils.debug_log(f"Appending {len(details_data)} rows of session details data")
        if details_data:
            try:
                details_sheet.append_rows(details_data)
                utils.debug_log(f"Successfully appended session details data")
            except Exception as e:
                error_msg = f"Error appending session details data: {str(e)}"
                utils.debug_log(error_msg)
                raise Exception(error_msg)
        else:
            utils.debug_log("No session details data to append") 
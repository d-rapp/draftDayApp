import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Define the scope and credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(f"creds/academic-oasis-450821-s1-cc04b16567e3.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheet
sheet = client.open("drafted_players").sheet1

# Function to fetch drafted players data from Google Sheet
def fetch_drafted_players():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# Function to save drafted players to Google Sheet
def save_drafted_players(drafted_players):
    existing_data = fetch_drafted_players()
    new_data = pd.DataFrame(drafted_players)
    updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    sheet.update([updated_data.columns.values.tolist()] + updated_data.values.tolist())

# Function to remove an existing player based on full_name
def remove_player(full_name):
    existing_data = fetch_drafted_players()
    updated_data = existing_data[existing_data.full_name != full_name]
    sheet.update([updated_data.columns.values.tolist()] + updated_data.values.tolist())

# # Example usage
# if __name__ == "__main__":
#     # Fetch drafted players
#     drafted_players = fetch_drafted_players()
#     print("Drafted Players:", drafted_players)

#     # Save new drafted players
#     new_drafted_players = [s
#         {"team_name": "Rappendola"
#          , "full_name": "Dan Rapp"
#          , "position": "WR"
#          , "nominated_by": "Rappendola"
#          , "nomination_amount": 10
#          , "draft_amount": 10}
#     ]
#     save_drafted_players(new_drafted_players)
#     print("New drafted players saved.")

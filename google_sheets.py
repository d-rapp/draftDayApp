import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
import pandas as pd

#needed for deployment
credentials_info = st.secrets["gcp_service_account"]
creds = service_account.Credentials.from_service_account_info(credentials_info)

# Define the scope and credentials
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# uncomment for local dev. 
# creds = ServiceAccountCredentials.from_json_keyfile_name(f"creds/academic-oasis-450821-s1-cc04b16567e3.json", scope)
client = gspread.authorize(creds)

# Open the Google Sheet
drafted_player_doc = client.open("drafted_players").sheet1
team_names_doc = client.open("team_names").sheet1

# Function to fetch drafted players data from Google Sheet
def fetch_drafted_players():
    data = drafted_player_doc.get_all_records()
    df = pd.DataFrame(data)
    return df

# Function to save drafted players to Google Sheet
def save_drafted_players(drafted_players):
    existing_data = fetch_drafted_players()
    new_data = pd.DataFrame(drafted_players)
    updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    drafted_player_doc.update([updated_data.columns.values.tolist()] + updated_data.values.tolist())

# Function to remove an existing player based on full_name
def remove_player(full_name):
    cell = drafted_player_doc.find(full_name)
    if cell:
        drafted_player_doc.delete_rows(cell.row)

def get_team_names():
    data = team_names_doc.get_all_records()
    df = pd.DataFrame(data)
    return df

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

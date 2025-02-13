import streamlit as st
import requests
import pandas as pd
import json
import os

# Function to fetch NFL player data from Sleeper API
def fetch_nfl_players():
    local_file = "localData/nfl_players.json"
    
    if os.path.exists(local_file):
        with open(local_file, "r") as f:
            players = json.load(f)
    else:
        url = "https://api.sleeper.app/v1/players/nfl"
        response = requests.get(url)
        data = response.json()
        players = [player for player in data.values() if player['active'] and player['position'] in ["WR", "RB", "QB", "TE"]]
        with open(local_file, "w") as f:
            json.dump(players, f)
    
    return players

# Load team names from local file
def load_team_names():
    local_file = "localData/team_names.json"
    
    if os.path.exists(local_file):
        with open(local_file, "r") as f:
            team_names = json.load(f)
        team_names_df = pd.DataFrame(team_names, columns=["team_name"])
    else:
        st.error("The file 'team_names.json' does not exist.")
        team_names_df = pd.DataFrame(columns=["team_name"])
    
    return team_names_df

# Function to display player data in a table
def display_players(players):
    # Load drafted players from local file
    drafted_players = []
    if os.path.exists("localData/drafted_players.json"):
        with open("localData/drafted_players.json", "r") as f:
            for line in f:
                drafted_data = json.loads(line)
                drafted_players.append(drafted_data["full_name"])

    # Filter out drafted players
    players = [player for player in players if player['full_name'] not in drafted_players]

    # Sort players by search_rank
    players = sorted(players, key=lambda player: player.get('search_rank', float('inf')) if player.get('search_rank') is not None else float('inf'))
    df = pd.DataFrame(players)
    st.dataframe(df)

# Function to save drafted players to a local file
def save_drafted_players(drafted_players, team_name):
    with open("localData/drafted_players.json", "a") as f:
        for player in drafted_players:
            drafted_data = {
                "team_name": team_name,
                "full_name": player['full_name'],
                "nominated_by": player['nominated_by'],
                "nomination_amount": player['nomination_amount'],
                "draft_amount": player['draft_amount']
            }
            json.dump(drafted_data, f)
            f.write("\n")

# Streamlit app layout
st.title("NFL Fantasy Football Draft Tracker", anchor="top")
team_names = load_team_names()
players = fetch_nfl_players()
# Filter players by position
positions = list(set(player['position'] for player in players))
selected_position = st.selectbox("Filter by position:", ["All"] + positions)
search_name = st.text_input("Search by player name:")
if search_name:
    players = [player for player in players if search_name.lower() in player['full_name'].lower()]
if selected_position != "All":
    players = [player for player in players if player['position'] == selected_position]

display_players(players)
# Function to handle drafting a player
def draft_player(player):
    st.write(f"Drafting player: {player['full_name']}")
    nominated_by = st.selectbox("Nominated by:", team_names['team_name'])
    nomination_amount = st.number_input("Nomination amount:", min_value=1, step=1)
    draft_amount = st.number_input("Winning draft amount:", min_value=1, step=1)
    team_name = st.selectbox("Winning team name:", team_names['team_name'])

    if st.button("Confirm Draft"):
        drafted_player = {
            "full_name": player['full_name'],
            "nominated_by": nominated_by,
            "nomination_amount": nomination_amount,
            "draft_amount": draft_amount,
            "team_name": team_name
        }
        save_drafted_players([drafted_player], team_name)
        st.success(f"{player['full_name']} drafted by {team_name} for ${draft_amount}")

# Select a player from the dataframe
# selected_player_index = st.selectbox("Select a player to draft:", range(len(players)), format_func=lambda idx: players[idx]['full_name'])
selected_player_index = st.selectbox("Select a player to draft:", range(len(players)), format_func=lambda idx: players[idx]['full_name'])
if selected_player_index is not None:
    draft_player(players[selected_player_index])


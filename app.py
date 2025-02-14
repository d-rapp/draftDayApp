import streamlit as st
import requests
import pandas as pd
import json
import os
import google_sheets as gs

# FILE_ID = "1U4-2l8u9b1Sr1aX3WFbAL-HQ_UsiiEoh"
# DRIVE_URL = f"https://drive.google.com/uc?id={FILE_ID}"

# Function to fetch NFL player data from Sleeper API
def fetch_nfl_players():
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    data = response.json()
    players = [player for player in data.values() if player['active'] and player['position'] in ["WR", "RB", "QB", "TE"]]
    players_df = pd.DataFrame(players)

    return players_df

def fetch_player_weekly_stats(player_id, season):
    url = f"https://api.sleeper.com/projections/nfl/player/{player_id}?season_type=regular&season={season}&grouping=week"
    # url = f"https://api.sleeper.com/stats/nfl/player/{player_id}?season_type=regular&season={season}"
    response = requests.get(url)
    data = response.json()
    
    return data

def fetch_player_season_stats(player_id, season):
    url = f"https://api.sleeper.com/stats/nfl/player/{player_id}?season_type=regular&season={season}"
    response = requests.get(url)
    data = response.json()
    
    return data

# Function to fetch and process player stats into a DataFrame
def fetch_and_process_player_stats(player_id, season):
    url = f"https://api.sleeper.com/stats/nfl/player/{player_id}?season_type=regular&season={season}"
    response = requests.get(url)
    data = response.json()
    
    # Extract stats information
    stats = data.get('stats', {})
    stats_df = pd.DataFrame([stats])
    
    return stats_df

# Load team names from local file
# def load_team_names():
#     local_file = "team_names.json"
    
#     if os.path.exists(local_file):
#         with open(local_file, "r") as f:
#             team_names = json.load(f)
#         team_names_df = pd.DataFrame(team_names, columns=["team_name"])
#     else:
#         st.error("The file 'team_names.json' does not exist.")
#         team_names_df = pd.DataFrame(columns=["team_name"])
    
#     return team_names_df

def filter_players(players):
    # Load drafted players from Google Sheets
    drafted_players = gs.fetch_drafted_players()
    # Convert players to DataFrame
    players_df = pd.DataFrame(players)
    # Filter out drafted players
    filtered_players_df = players_df[~players_df['full_name'].isin(drafted_players['full_name'])]

    return filtered_players_df

# Function to display player data in a table
def display_players(players_df):
    players_df = filter_players(players_df)
    # Sort players by search_rank
    players_df = players_df.sort_values(by='search_rank', na_position='last')
    st.dataframe(players_df, column_order=["full_name", "position", "team", "search_rank"])

# Function to save drafted players to a local file
def save_drafted_players(drafted_players, team_name):
    # with open("localData/drafted_players.json", "a") as f:
    for player in drafted_players:
        drafted_data = {
            "team_name": team_name,
            "full_name": player['full_name'],
            "position": player['position'],
            "nominated_by": player['nominated_by'],
            "nomination_amount": player['nomination_amount'],
            "draft_amount": player['draft_amount']
        }
    gs.save_drafted_players([drafted_data])
        #   json.dump(drafted_data, f)
        #     f.write("\n")

# Function to calculate remaining budget for each team
def calculate_remaining_budget(initial_budget=200):
    team_names = gs.get_team_names()
    team_budgets = {team: initial_budget for team in team_names['team_name']}
    
    drafted_players = gs.fetch_drafted_players#[json.loads(line) for line in f]
    for player in drafted_players:
        team_budgets[player['team_name']] -= player['draft_amount']
    
    return team_budgets

# Function to aggregate total spend and count of players per position by team name
def aggregate_draft_data():
    drafted_players = gs.fetch_drafted_players()
    team_data = {}
    for _, player in drafted_players.iterrows():
        team_name = player['team_name']
        if team_name not in team_data:
            team_data[team_name] = {
                "Total Spend": 0,
                "Player Count": 0,
                "Positions": {}
            }
        team_data[team_name]["Total Spend"] += player['draft_amount']
        team_data[team_name]["Player Count"] += 1
        position = player['position']
        if position in team_data[team_name]["Positions"]:
            team_data[team_name]["Positions"][position] += 1
        else:
            team_data[team_name]["Positions"][position] = 1
    
    aggregated_data = []
    for team_name, data in team_data.items():
        row = {
            "Team Name": team_name,
            "Remaining $$$": 200 - data["Total Spend"],
            "Total Spend": data["Total Spend"],
            "Player Count": data["Player Count"]
        }
        row.update(data["Positions"])
        aggregated_data.append(row)
    
    aggregated_df = pd.DataFrame(aggregated_data)
    return aggregated_df

# Function to handle drafting a player
def draft_player(player_df):
    player = player_df.iloc[0]
    st.write(f"Drafting player: {player['full_name']}")
    st.image(f"https://sleepercdn.com/content/nfl/players/{player['player_id']}.jpg")
    
    # Fetch and display player stats
    stats_df = fetch_and_process_player_stats(player['player_id'], "2024")
    st.dataframe(stats_df)
    
    nominated_by = st.selectbox("Nominated by:", team_names['team_name'])
    nomination_amount = st.number_input("Nomination amount:", min_value=1, step=1)
    draft_amount = st.number_input("Winning draft amount:", min_value=1, step=1)
    team_name = st.selectbox("Winning team name:", team_names['team_name'])

    if st.button("Confirm Draft"):
        drafted_player = {
            "full_name": player['full_name'],
            "position": player['position'],
            "nominated_by": nominated_by,
            "nomination_amount": nomination_amount,
            "draft_amount": draft_amount,
            "team_name": team_name
        }
        save_drafted_players([drafted_player], team_name)
        st.success(f"{player['full_name']} drafted by {team_name} for ${draft_amount}")


# Streamlit app layout
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Draft Day App", "Yahoo Players"])

if page == "Home":
    st.title("NFL Fantasy Football Draft Tracker")
    team_names = gs.get_team_names() #load_team_names()
    players = fetch_nfl_players()
    # Filter players by position
    positions = list(players['position'].unique())
    selected_position = st.selectbox("Filter by position:", ["All"] + positions)
    search_name = st.text_input("Search by player name:")
    if search_name:
        players = players[players['full_name'].str.contains(search_name, case=False)]
    if selected_position != "All":
        players = players[players['position'] == selected_position]

    display_players(players)
    
    # Display remaining budget for each team
    st.subheader("Team Budget and Positions")
    # team_budgets = calculate_remaining_budget()
    # budget_df = pd.DataFrame(list(team_budgets.items()), columns=["Team Name", "Remaining Budget"]).transpose()
    # st.dataframe(budget_df)

    st.dataframe(aggregate_draft_data(),hide_index=True)

    # Select a player from the dataframe
    players = filter_players(players)
    players = players.sort_values(by='search_rank', na_position='last')
    selected_player_index = st.selectbox("Select a player to draft:", players.index, format_func=lambda idx: players.loc[idx, 'full_name'])
    if selected_player_index is not None:
        draft_player(players.loc[[selected_player_index]])

elif page == "Draft Day App":
    import draftDayApp
    draftDayApp.run()

elif page == "Yahoo Players":
    import yahooPlayers
    yahooPlayers.run()


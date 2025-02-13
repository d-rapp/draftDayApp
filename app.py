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
def load_team_names():
    local_file = "team_names.json"
    
    if os.path.exists(local_file):
        with open(local_file, "r") as f:
            team_names = json.load(f)
        team_names_df = pd.DataFrame(team_names, columns=["team_name"])
    else:
        st.error("The file 'team_names.json' does not exist.")
        team_names_df = pd.DataFrame(columns=["team_name"])
    
    return team_names_df

def filter_players(players):
    # Load drafted players from local file
    drafted_players = []
    if os.path.exists("localData/drafted_players.json"):
        with open("localData/drafted_players.json", "r") as f:
            for line in f:
                drafted_data = json.loads(line)
                drafted_players.append(drafted_data["full_name"])

    # Filter out drafted players
    players = [player for player in players if player['full_name'] not in drafted_players]

    return players

# Function to display player data in a table
def display_players(players):
    players = filter_players(players)
    # Sort players by search_rank
    players = sorted(players, key=lambda player: player.get('search_rank', float('inf')) if player.get('search_rank') is not None else float('inf'))
    df = pd.DataFrame(players)
    st.dataframe(df.head(6), column_order=["full_name", "position", "team"
                                   , "yahoo_id", "rotoworld_id", "espn_id", "swish_id", "player_id", "fantasy_data_id", "sportsradar_id"
                                   , "search_rank"],hide_index=True)

# Function to save drafted players to a local file
def save_drafted_players(drafted_players, team_name):
    with open("localData/drafted_players.json", "a") as f:
        for player in drafted_players:
            drafted_data = {
                "team_name": team_name,
                "full_name": player['full_name'],
                "position": player['position'],
                "nominated_by": player['nominated_by'],
                "nomination_amount": player['nomination_amount'],
                "draft_amount": player['draft_amount']
            }
            json.dump(drafted_data, f)
            f.write("\n")

# Function to calculate remaining budget for each team
def calculate_remaining_budget(initial_budget=200):
    team_names = load_team_names()
    team_budgets = {team: initial_budget for team in team_names['team_name']}
    
    if os.path.exists("localData/drafted_players.json"):
        with open("localData/drafted_players.json", "r") as f:
            drafted_players = [json.loads(line) for line in f]
            for player in drafted_players:
                team_budgets[player['team_name']] -= player['draft_amount']
    
    return team_budgets

# Function to aggregate total spend and count of players per position by team name
def aggregate_draft_data():
    if os.path.exists("localData/drafted_players.json"):
        with open("localData/drafted_players.json", "r") as f:
            drafted_players = [json.loads(line) for line in f]
        
        team_data = {}
        for player in drafted_players:
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
                "Remaining $$$": 200-data["Total Spend"],
                "Total Spend": data["Total Spend"],
                "Player Count": data["Player Count"]
            }
            row.update(data["Positions"])
            aggregated_data.append(row)
        
        aggregated_df = pd.DataFrame(aggregated_data)
        return aggregated_df
    else:
        st.error("The file 'drafted_players.json' does not exist.")
        return pd.DataFrame(columns=["Team Name", "Total Spend", "Player Count"])

# Streamlit app layout
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Draft Day App", "Yahoo Players"])

if page == "Home":
    st.title("NFL Fantasy Football Draft Tracker")
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
    
    # Display remaining budget for each team
    st.subheader("Team Budget and Positions")
    # team_budgets = calculate_remaining_budget()
    # budget_df = pd.DataFrame(list(team_budgets.items()), columns=["Team Name", "Remaining Budget"]).transpose()
    # st.dataframe(budget_df)

    st.dataframe(aggregate_draft_data(),hide_index=True)

    # Function to handle drafting a player
    def draft_player(player):
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
            #st.experimental_rerun()  # Refresh the data

    # Select a player from the dataframe
    players = filter_players(players)
    players = sorted(players, key=lambda player: player.get('search_rank', float('inf')) if player.get('search_rank') is not None else float('inf'))
    selected_player_index = st.selectbox("Select a player to draft:", range(len(players)), format_func=lambda idx: players[idx]['full_name'])
    if selected_player_index is not None:
        draft_player(players[selected_player_index])

elif page == "Draft Day App":
    import draftDayApp
    draftDayApp.run()

elif page == "Yahoo Players":
    import yahooPlayers
    yahooPlayers.run()


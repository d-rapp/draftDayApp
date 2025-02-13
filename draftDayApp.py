import json
import pandas as pd
import streamlit as st

def run():
    st.title("Drafted Players Information")

    # Load drafted players data
    with open('localData/drafted_players.json', 'r') as f:
        drafted_players = [json.loads(line) for line in f]

    # Convert drafted players to DataFrame
    df_drafted_players = pd.DataFrame(drafted_players)

    # Display the DataFrame in Streamlit app
    st.dataframe(df_drafted_players)

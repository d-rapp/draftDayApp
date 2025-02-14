import json
import pandas as pd
import streamlit as st
import google_sheets as gs

def run():
    st.title("Drafted Players Information")

    # Load drafted players data
    df_drafted_players = gs.fetch_drafted_players()

    if df_drafted_players.empty == False:

    # Display the DataFrame in Streamlit app
        st.dataframe(df_drafted_players)

    

        # Select a player to remove
        selected_player = st.selectbox("Select a player to remove:", df_drafted_players['full_name'])

        # Button to remove the selected player
        if st.button("Remove Player"):
            gs.remove_player(selected_player)
            st.success(f"Player {selected_player} removed.")
            # Refresh the data
            df_drafted_players = gs.fetch_drafted_players()
            st.dataframe(df_drafted_players)
    elif df_drafted_players.empty == True:
        st.write("No drafted players found.")

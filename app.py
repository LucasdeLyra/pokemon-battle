# app.py
# --- RESPONSIBILITY: The main landing page of the application. ---

import streamlit as st

st.set_page_config(
    page_title="Streamlit Pokémon Battle Simulator",
    page_icon="🔥",
    layout="wide"
)

st.title("Welcome to the Pokémon Battle Simulator! 🎮")

st.markdown("""
This application is a turn-based Pokémon battle simulator built with Streamlit.
You can build your own custom team and face off against an AI opponent.

### How to Play:
1.  **Navigate to the `Team Selection` page** using the sidebar on the left.
2.  **Choose up to 6 Pokémon** to form your team.
3.  For each Pokémon you select, **you must choose exactly 4 moves**.
4.  Once your team is ready, click the **'Confirm Team'** button.
5.  **Go to the `Battle` page** to start the fight!

Good luck, Trainer!
""")

st.image("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png", width=200)
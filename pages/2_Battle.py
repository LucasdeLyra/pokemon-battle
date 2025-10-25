# pages/2_Battle.py
# --- RESPONSIBILITY: Runs the main battle simulation. ---

import streamlit as st
import random
import copy

from utils.data_loader import load_all_data_from_csvs
POKEMON_DATA, MOVES = load_all_data_from_csvs()
from utils.game_logic import initialize_game, check_game_over
from utils.ui import battle_interface

st.markdown("""
<style>
    header, footer {visibility: hidden;}


    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
    }   
</style>
""",unsafe_allow_html=True)

# --- Custom Initialization for Battle Page ---
def initialize_battle():
    """Initializes a battle, using a custom team if available."""
    # If the player hasn't created a team, use the old random method.
    if 'player_team' not in st.session_state or not st.session_state.player_team:
        st.warning("No custom team found. Generating a random team for you.")
        initialize_game() # This function from game_logic creates a full 6v6 random battle
        return

    # If a custom team exists, use it and generate only the AI's team.
    ai_names = random.sample([name for name, data in POKEMON_DATA.items() if data.get('moves')], 6)
    st.session_state.ai_team = [copy.deepcopy(POKEMON_DATA[name]) for name in ai_names]

    # Initialize current HP for both teams
    for p in st.session_state.player_team + st.session_state.ai_team:
        p["current_hp"] = p["hp"]
        # Ensure AI Pokémon have 4 moves
        if p in st.session_state.ai_team and p.get("moves") and len(p["moves"]) > 4:
            p["moves"] = random.sample(sorted(p["moves"]), 4)

    st.session_state.log = [f"Your {len(st.session_state.player_team)} Pokémon face the opponent!"]
    st.session_state.player_active_idx = 0
    st.session_state.ai_active_idx = 0
    st.session_state.game_over = False
    st.session_state.winner = None

# --- MAIN APP ---
st.set_page_config(page_title="Pokémon Battle", layout="wide")

st.markdown("""
<style>
    .stButton>button { height: 4em; font-size: 1.1em; }
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #FF4B4B , #7FFF7F); }
</style>
""", unsafe_allow_html=True)

if not POKEMON_DATA or not MOVES:
    st.error("Failed to load game data. The application cannot start.")
    st.stop()

if 'log' not in st.session_state:
    initialize_battle()

if st.session_state.get('player_team', []) == []:
    st.error("You must build a team on the 'Team Selection' page before you can battle!")
    st.stop()


if st.session_state.game_over:
    st.header(f"Game Over! {st.session_state.winner} won the battle!")
    st.balloons()
    if st.button("Start a New Battle"):
        initialize_battle()
        st.rerun()
else:
    left_col, right_col = st.columns([0.7, 0.3], gap="large")
    with left_col:
        battle_interface()
    with right_col:
        st.subheader("Battle Log")
        log_container = st.container(height=600)
        for msg in reversed(st.session_state.log):
            log_container.markdown(f"`{msg}`")
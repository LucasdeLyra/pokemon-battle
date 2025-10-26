import streamlit as st
import random
import copy

from utils.data_loader import load_all_data_from_csvs, load_teams_from_firebase
POKEMON_DATA, MOVES = load_all_data_from_csvs()
from utils.game_logic import initialize_game, check_game_over
from utils.ui import battle_interface

def initialize_battle(selected_team_name=None, teams_dict=None):
    if selected_team_name and selected_team_name != "Random team":
        team_list = teams_dict.get(selected_team_name, {}) if teams_dict else {}
        st.session_state.player_team = []
        for entry in team_list:
            p_name = entry.get('name')
            if not p_name:
                continue
            template = next((v for k, v in POKEMON_DATA.items() if k.lower() == str(p_name).lower()), None)
            if not template:
                continue
            p = copy.deepcopy(template)
            raw_moves = entry.get('moves', []) or []
            validated = [m for m in raw_moves if isinstance(m, str) and m in MOVES]
            p['moves'] = validated
            if entry.get('nickname'):
                p['nickname'] = entry.get('nickname')
            st.session_state.player_team.append(p)
        if not st.session_state.player_team:
            st.warning("Selected team had no valid Pokémon — falling back to a random team.")
            initialize_game()
            return
    else:
        initialize_game()
        return

    ai_names = random.sample([name for name, data in POKEMON_DATA.items() if data.get('moves')], 6)
    st.session_state.ai_team = [copy.deepcopy(POKEMON_DATA[name]) for name in ai_names]

    for p in st.session_state.player_team + st.session_state.ai_team:
        p["current_hp"] = p["hp"]
        if p in st.session_state.ai_team and p.get("moves") and len(p["moves"]) > 4:
            p["moves"] = random.sample(sorted(p["moves"]), 4)

    st.session_state.log = [f"Your {len(st.session_state.player_team)} Pokémon face the opponent!"]
    st.session_state.player_active_idx = 0
    st.session_state.ai_active_idx = 0
    st.session_state.game_over = False
    st.session_state.winner = None

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
    saved_teams = {}
    try:
        saved_teams = load_teams_from_firebase() or {}
    except Exception:
        saved_teams = {}

    options = ["Random team"] + list(saved_teams.keys())
    choice = st.selectbox("Choose which team to use for this battle:", options=options)

    if st.button("Start Battle"):
        if choice == "Random team":
            initialize_battle(selected_team_name="Random team")
        else:
            initialize_battle(selected_team_name=choice, teams_dict=saved_teams)
        if 'player_team' in st.session_state and st.session_state.player_team:
            # build AI team
            ai_names = random.sample([name for name, data in POKEMON_DATA.items() if data.get('moves')], 6)
            st.session_state.ai_team = [copy.deepcopy(POKEMON_DATA[name]) for name in ai_names]
            for p in st.session_state.player_team + st.session_state.ai_team:
                p["current_hp"] = p["hp"]
                if p in st.session_state.ai_team and p.get("moves") and len(p["moves"]) > 4:
                    p["moves"] = random.sample(sorted(p["moves"]), 4)
            st.session_state.log = [f"Your {len(st.session_state.player_team)} Pokémon face the opponent!"]
            st.session_state.player_active_idx = 0
            st.session_state.ai_active_idx = 0
            st.session_state.game_over = False
            st.session_state.winner = None
            st.rerun()

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
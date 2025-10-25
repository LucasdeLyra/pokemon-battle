import streamlit as st
import random
import copy
from data_loader import load_all_data_from_csvs, TYPE_CHART
POKEMON_DATA, MOVES = load_all_data_from_csvs()

def add_to_log(message):
    """Appends a message to the battle log in the session state."""
    st.session_state.log.append(message)

def get_type_effectiveness(attack_type, defense_type):
    """Calculates the damage multiplier based on type matchup."""
    a_type, d_type = attack_type.lower(), defense_type.lower()
    return TYPE_CHART.get(a_type, {}).get(d_type, 1)

def calculate_damage(attacker, defender, move):
    """Calculates the damage for a given attack."""
    eff = get_type_effectiveness(move["type"], defender["type"])
    rand = random.uniform(0.85, 1.0)
    damage = int((((2/5 * 50 + 2) * move["power"] * attacker["attack"] / defender["defense"]) / 50 + 2) * eff * rand)
    return damage, eff

def execute_attack(attacker, defender, move_name, att_name, def_name):
    """Executes a single attack, applies damage, and logs the results."""
    move = MOVES[move_name]
    damage, eff = calculate_damage(attacker, defender, move)
    defender["current_hp"] = max(0, defender["current_hp"] - damage)
    
    add_to_log(f"{att_name}'s {attacker['name']} used {move_name.replace('-', ' ').title()}!")
    if eff > 1: add_to_log("It's super effective!")
    elif 0 < eff < 1: add_to_log("It's not very effective...")
    elif eff == 0: add_to_log(f"It doesn't affect {def_name}'s {defender['name']}...")
    
    if defender["current_hp"] == 0:
        add_to_log(f"{def_name}'s {defender['name']} fainted!")
        return True
    return False

def process_turn(player_move):
    """Processes a full turn: both player's and AI's attacks."""
    player = st.session_state.player_team[st.session_state.player_active_idx]
    ai = st.session_state.ai_team[st.session_state.ai_active_idx]
    ai_move = random.choice(tuple(ai['moves']))
    
    if player["speed"] >= ai["speed"]:
        if execute_attack(player, ai, player_move, "Your", "Opponent's"): return
        if execute_attack(ai, player, ai_move, "Opponent's", "Your"): return
    else:
        if execute_attack(ai, player, ai_move, "Opponent's", "Your"): return
        if execute_attack(player, ai, player_move, "Your", "Opponent's"): return

def check_game_over():
    """Checks if either team has been fully defeated and updates game state."""
    if all(p["current_hp"] == 0 for p in st.session_state.player_team):
        st.session_state.game_over, st.session_state.winner = True, "The AI"
    elif all(p["current_hp"] == 0 for p in st.session_state.ai_team):
        st.session_state.game_over, st.session_state.winner = True, "You"

def initialize_game():
    """Sets up a new game, selecting teams and resetting state."""
    available = [name for name, data in POKEMON_DATA.items() if data.get('moves')]
    if len(available) < 6:
        st.error("Not enough Pokémon with moves to start a 6v6 game!")
        st.stop()
    
    player_names = random.sample(available, 6)
    ai_names = random.sample(available, 6)
    st.session_state.player_team = [copy.deepcopy(POKEMON_DATA[name]) for name in player_names]
    st.session_state.ai_team = [copy.deepcopy(POKEMON_DATA[name]) for name in ai_names]

    for p in st.session_state.player_team + st.session_state.ai_team:
        p["current_hp"] = p["hp"]
        if p.get("moves") and len(p["moves"]) > 4:
            p["moves"] = random.sample(sorted(p["moves"]), 4)
    
    st.session_state.log = ["A new 6v6 battle begins!"]
    st.session_state.player_active_idx = 0
    st.session_state.ai_active_idx = 0
    st.session_state.game_over = False
    st.session_state.winner = None
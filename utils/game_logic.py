import streamlit as st
import random
import copy
from utils.data_loader import load_pokemon_data, load_moves_data, load_type_effectiveness

POKEMON_DATA = load_pokemon_data()
MOVES = load_moves_data()
TYPE_CHART = load_type_effectiveness()

def add_to_log(message):
    st.session_state.log.append(message)

def get_type_effectiveness(attack_type, defense_type):
    a_type = attack_type.lower()
    
    if isinstance(defense_type, list):
        multiplier = 1
        for d_type in defense_type:
            if d_type:
                d_type = d_type.lower()
                type_multiplier = TYPE_CHART.get(a_type, {}).get(d_type, 1)
                if type_multiplier == 0:
                    return 0
                multiplier *= type_multiplier
        return multiplier
    else:
        d_type = defense_type.lower()
        effectiveness = TYPE_CHART.get(a_type, {}).get(d_type, 1)
        return effectiveness

def calculate_damage(attacker, defender, move):
    eff = get_type_effectiveness(move["type"], defender["type"])
    rand = random.uniform(0.85, 1.0)
    
    power = float(move["power"]) if move["power"] is not None else 0
    attack = float(attacker["attack"]) if attacker["attack"] is not None else 1
    defense = float(defender["defense"]) if defender["defense"] is not None else 1
    
    level = 50
    
    base = ((2 * level / 5) + 2) * power * (attack / defense)
    damage = int((base / 50 + 2) * eff * rand)
        
    return max(0, damage), eff

def execute_attack(attacker, defender, move_name, att_name, def_name):
    if move_name.replace('.', '').isdigit():
        id_to_move_name = {str(int(float(str(m_data.get('id'))))): m_name 
                          for m_name, m_data in MOVES.items() 
                          if m_data.get('id') is not None}
        move_name = id_to_move_name.get(str(int(float(move_name))))
        if not move_name:
            return False
            
    move = MOVES[move_name]
    
    if move["power"] is None or not str(move["power"]).strip():
        move["power"] = 0
    else:
        try:
            move["power"] = float(str(move["power"]))
        except (ValueError, TypeError):
            move["power"] = 0
                
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
    player = st.session_state.player_team[st.session_state.player_active_idx]
    ai = st.session_state.ai_team[st.session_state.ai_active_idx]
    
    if not ai.get('moves'):
        add_to_log(f"{ai['name']} has no moves!")
        return
    
    ai_moves = [m for m in ai['moves'] if m]
    if not ai_moves:
        add_to_log(f"{ai['name']} has no valid moves!")
        return
    
    ai_move = random.choice(ai_moves)
    
    if player["speed"] >= ai["speed"]:
        if execute_attack(player, ai, player_move, "Your", "Opponent's"): return
        if execute_attack(ai, player, ai_move, "Opponent's", "Your"): return
    else:
        if execute_attack(ai, player, ai_move, "Opponent's", "Your"): return
        if execute_attack(player, ai, player_move, "Your", "Opponent's"): return

def check_game_over():
    if all(p["current_hp"] == 0 for p in st.session_state.player_team):
        st.session_state.game_over, st.session_state.winner = True, "The AI"
    elif all(p["current_hp"] == 0 for p in st.session_state.ai_team):
        st.session_state.game_over, st.session_state.winner = True, "You"

def initialize_game():
    available = [name for name, data in POKEMON_DATA.items() if data.get('moves')]
    if len(available) < 6:
        st.error("Not enough Pokémon with moves to start a 6v6 game!")
        st.stop()
    
    player_names = random.sample(available, 6)
    ai_names = random.sample(available, 6)
    st.session_state.player_team = [copy.deepcopy(POKEMON_DATA[name]) for name in player_names]
    st.session_state.ai_team = [copy.deepcopy(POKEMON_DATA[name]) for name in ai_names]

    id_to_move_name = {}
    for m_name, m_data in MOVES.items():
        mid = m_data.get('id')
        if mid is not None:
            id_to_move_name[str(mid)] = m_name

    def _normalize_mid(mref):
        try:
            if isinstance(mref, str):
                s = mref.strip()
                if s == '':
                    return s
                if '.' in s:
                    return str(int(float(s)))
                return s
            if isinstance(mref, float) or isinstance(mref, int):
                return str(int(mref))
            return str(mref)
        except Exception:
            return str(mref)

    for p in st.session_state.player_team + st.session_state.ai_team:
        p["current_hp"] = p["hp"]
        raw_moves = p.get('moves', []) or []
        converted = []
        for m in raw_moves:
            mid = _normalize_mid(m)
            name = id_to_move_name.get(mid)
            if name:
                converted.append(name)
        p['moves'] = converted
        if p.get("moves") and len(p["moves"]) > 4:
            p["moves"] = random.sample(sorted(p["moves"]), 4)
    
    st.session_state.log = ["A new 6v6 battle begins!"]
    st.session_state.player_active_idx = 0
    st.session_state.ai_active_idx = 0
    st.session_state.game_over = False
    st.session_state.winner = None
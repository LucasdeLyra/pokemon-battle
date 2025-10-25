# ui.py
# --- RESPONSIBILITY: Renders all Streamlit UI components for the battle. ---

import streamlit as st
import os
from game_logic import process_turn, check_game_over, add_to_log

def display_pokemon_ui(pokemon, is_player):
    """Renders the UI for a single Pokémon (sprite, name, HP bar)."""
    sprite_path = f"assets/sprites/{'back' if is_player else 'front'}/default/male/{pokemon['id']}.png"
    if os.path.exists(sprite_path):
        st.image(sprite_path, width=180 if is_player else 140)
    
    st.subheader(pokemon['name'])
    st.write(f"HP: {pokemon['current_hp']} / {pokemon['hp']}")
    st.progress(pokemon['current_hp'] / pokemon['hp'] if pokemon['hp'] > 0 else 0)

def battle_interface():
    """The main UI function that orchestrates the display of the battle screen."""
    player_active = st.session_state.player_team[st.session_state.player_active_idx]
    ai_active = st.session_state.ai_team[st.session_state.ai_active_idx]

    # --- Auto-switch AI Pokémon if fainted ---
    if ai_active["current_hp"] == 0:
        for i, p in enumerate(st.session_state.ai_team):
            if p["current_hp"] > 0:
                st.session_state.ai_active_idx = i
                add_to_log(f"Opponent sent out {p['name']}!")
                break
    
    # --- Force player to switch if their Pokémon fainted ---
    if player_active["current_hp"] == 0:
        st.warning("Your Pokémon fainted! You must switch.")
        available = [(i, p) for i, p in enumerate(st.session_state.player_team) if p["current_hp"] > 0]
        if not available:
            check_game_over()
            return
        for i, p in available:
            if st.button(f"Go {p['name']}!", key=f"switch_{i}"):
                st.session_state.player_active_idx = i
                add_to_log(f"You sent out {p['name']}!")
                st.rerun()
        return

    # Refresh active Pokémon after potential switches
    player_active = st.session_state.player_team[st.session_state.player_active_idx]
    ai_active = st.session_state.ai_team[st.session_state.ai_active_idx]

    # --- Battle Display Section ---
    with st.container():
        _, opponent_col = st.columns([3, 2])
        with opponent_col:
            display_pokemon_ui(ai_active, is_player=False)
        
        player_col, _ = st.columns([2, 3])
        with player_col:
            display_pokemon_ui(player_active, is_player=True)

    # --- Move Selection Section ---
    st.markdown("---")
    st.write("**Choose your move:**")
    moves = player_active.get("moves", [])
    
    def on_move_click(move):
        process_turn(move)
        check_game_over()
    
    # Create 2x2 grid for moves
    row1 = st.columns(2)
    if len(moves) > 0:
        row1[0].button(moves[0].replace('-', ' ').title(), on_click=on_move_click, args=(moves[0],), use_container_width=True, key="move_0")
    if len(moves) > 1:
        row1[1].button(moves[1].replace('-', ' ').title(), on_click=on_move_click, args=(moves[1],), use_container_width=True, key="move_1")
    
    if len(moves) > 2:
        row2 = st.columns(2)
        row2[0].button(moves[2].replace('-', ' ').title(), on_click=on_move_click, args=(moves[2],), use_container_width=True, key="move_2")
        if len(moves) > 3:
            row2[1].button(moves[3].replace('-', ' ').title(), on_click=on_move_click, args=(moves[3],), use_container_width=True, key="move_3")
import streamlit as st
import pandas as pd
import os

# --- TYPE EFFECTIVENESS DATA ---
TYPE_CHART = {
    'normal': {'rock': 0.5, 'ghost': 0},
    'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5},
    'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2, 'dragon': 0.5},
    'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2, 'dragon': 0.5},
    'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'ground': 2, 'flying': 0.5, 'bug': 0.5, 'rock': 2, 'dragon': 0.5},
    'fighting': {'normal': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2, 'ghost': 0},
    'ground': {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2},
    'flying': {'electric': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2, 'rock': 0.5},
    'psychic': {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'ghost': 1},
    'bug': {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5},
    'rock': {'fire': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2},
    'ghost': {'normal': 0, 'psychic': 2, 'ghost': 2},
    'dragon': {'dragon': 2},
}

@st.cache_data
def load_all_data_from_csvs(assets_path="assets"):
    """Loads all necessary game data from CSV files into structured dictionaries."""
    try:
        pokemon_df = pd.read_csv(os.path.join(assets_path, 'pokemon.csv'))
        types_df = pd.read_csv(os.path.join(assets_path, 'types.csv'))
        stats_df = pd.read_csv(os.path.join(assets_path, 'stats.csv'))
        moves_df = pd.read_csv(os.path.join(assets_path, 'moves.csv'))
        pokemon_types_df = pd.read_csv(os.path.join(assets_path, 'pokemon_types.csv'))
        pokemon_stats_df = pd.read_csv(os.path.join(assets_path, 'pokemon_stats.csv'))
        pokemon_moves_df = pd.read_csv(os.path.join(assets_path, 'pokemon_moves.csv'))
    except FileNotFoundError as e:
        st.error(f"Error loading CSV files: {e}. Ensure the 'assets' folder is present.")
        return {}, {}

    pokemon_df = pokemon_df[pokemon_df['id'] <= 493]
    type_map = types_df.set_index('id')['identifier'].to_dict()
    stat_map = stats_df.set_index('id')['identifier'].to_dict()
    move_map = moves_df.set_index('id')['identifier'].to_dict()

    moves_data = {
        row['identifier']: {'power': int(row['power']), 'type': type_map.get(row['type_id'], 'normal')}
        for _, row in moves_df.iterrows() if pd.notna(row['power'])
    }

    pokemon_data = {}
    for _, p_row in pokemon_df.iterrows():
        pokemon_id = p_row['id']
        p_types = pokemon_types_df[(pokemon_types_df['pokemon_id'] == pokemon_id)]
        p_move_ids = pokemon_moves_df[pokemon_moves_df['pokemon_id'] == pokemon_id]['move_id']
        
        new_pokemon = {"id": pokemon_id, "name": p_row['identifier'].capitalize()}
        new_pokemon['type'] = type_map.get(p_types.iloc[0]['type_id'], 'normal') if not p_types.empty else 'normal'
        new_pokemon['moves'] = set(move_map.get(mid) for mid in p_move_ids if mid in move_map and move_map.get(mid) in moves_data)
        
        p_stats = pokemon_stats_df[pokemon_stats_df['pokemon_id'] == pokemon_id]
        for _, stat_row in p_stats.iterrows():
            stat_name = stat_map.get(stat_row['stat_id'])
            new_pokemon[stat_name] = stat_row['base_stat']
        
        pokemon_data[new_pokemon['name']] = new_pokemon

    return pokemon_data, moves_data

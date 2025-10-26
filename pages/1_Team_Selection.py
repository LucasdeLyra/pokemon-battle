import streamlit as st
import requests
import json
import os
from utils.data_loader import (
    load_pokemon_data,
    load_moves_data,
    get_type_name,
    save_team_to_firebase,
    load_teams_from_firebase,
)

POKEMON_DATA = load_pokemon_data()
MOVES_DATA = load_moves_data()
ITEMS_PER_PAGE = 25

st.set_page_config(layout="wide")

#TODO: Criar as classes bonitinho para utilizar por todos os arquivos
class Pokemon:
    """A class to represent a single, customized Pokémon instance in a team."""
    def __init__(self, name, nickname, moves):
        self.name = name
        self.nickname = nickname
        self.moves = [move for move in moves if move]
        self.sprite_data = POKEMON_DATA[self.name]['sprites']

    def to_dict(self):
        return {"name": self.name, "nickname": self.nickname, "moves": self.moves}

    @classmethod
    def from_dict(cls, data):
        return cls(name=data["name"], nickname=data["nickname"], moves=data["moves"])

TEAMS_FILE = "teams.json"

def load_teams():
    try:
        fb_teams = load_teams_from_firebase()
        if fb_teams:
            return fb_teams
    except Exception:
        pass

    if not os.path.exists(TEAMS_FILE):
        return {}
    with open(TEAMS_FILE, 'r') as f:
        return json.load(f)

def save_teams(teams_data):
    with open(TEAMS_FILE, 'w') as f:
        json.dump(teams_data, f, indent=4)

if 'team' not in st.session_state: st.session_state.team = []
if 'saved_teams' not in st.session_state: st.session_state.saved_teams = load_teams()
if 'current_team_name' not in st.session_state: st.session_state.current_team_name = "My New Team"
if 'selected_pokemon' not in st.session_state: st.session_state.selected_pokemon = None
if 'search_term' not in st.session_state: st.session_state.search_term = ""
if 'pokemon_in_editor' not in st.session_state: st.session_state.pokemon_in_editor = None
if 'active_move_slot' not in st.session_state: st.session_state.active_move_slot = None
if 'circular_move_index' not in st.session_state: st.session_state.circular_move_index = 0
if 'page_number' not in st.session_state: st.session_state.page_number = 0

TYPE_COLORS = { 'normal': '#A8A77A', 'fire': '#EE8130', 'water': '#6390F0', 'electric': '#F7D02C', 'grass': '#7AC74C', 'ice': '#96D9D6', 'fighting': '#C22E28', 'poison': '#A33EA1', 'ground': '#E2BF65', 'flying': '#A98FF3', 'psychic': '#F95587', 'bug': '#A6B91A', 'rock': '#B6A136', 'ghost': '#735797', 'dragon': '#6F35FC', 'dark': '#705746', 'steel': '#B7B7CE', 'fairy': '#D685AD' }


def resolve_type_ref(type_ref):
    if isinstance(type_ref, list):
        resolved = []
        for t in type_ref:
            resolved.append(resolve_type_ref(t))
        flat = []
        for r in resolved:
            if isinstance(r, list):
                flat.extend(r)
            else:
                flat.append(r)
        return flat

    if type_ref is None:
        return 'normal'

    s = str(type_ref).strip()
    if s == '':
        return 'normal'

    cleaned = s.strip('/').strip()
    if cleaned.replace('.', '').isdigit():
        try:
            type_id = str(int(float(cleaned)))
            type_name = get_type_name(type_id)
            return type_name.lower() if type_name else 'normal'
        except Exception:
            return 'normal'

    return s.lower()

def display_types(types):
    if isinstance(types, str): types = [types]
    type_html = ""
    for t in types:
        color = TYPE_COLORS.get(t.lower(), '#777')
        type_html += f'<span style="background-color:{color}; color:white; padding: 4px 10px; margin: 0 2px; border-radius: 5px; font-size: 1em; font-weight: bold;">{t.upper()}</span>'
    return type_html

def select_pokemon(pokemon_name):
    st.session_state.selected_pokemon = pokemon_name
    st.session_state.search_term = pokemon_name
    st.session_state.pokemon_in_editor = {"name": pokemon_name, "nickname": pokemon_name, "moves": ["", "", "", ""]}
    st.session_state.active_move_slot = None
    st.session_state.circular_move_index = 0

def handle_search_change():
    if st.session_state.selected_pokemon and st.session_state.search_term != st.session_state.selected_pokemon:
        st.session_state.selected_pokemon = None
        st.session_state.pokemon_in_editor = None
    st.session_state.page_number = 0


def close_moves_view():
    st.session_state.selected_pokemon = None
    st.session_state.pokemon_in_editor = None
    st.session_state.search_term = ""
    st.session_state.page_number = 0

def set_active_move_slot(slot_index):
    st.session_state.active_move_slot = slot_index
    st.toast(f"Select a move for Slot {slot_index + 1}")

def assign_move(move_name):
    editor_pkm = st.session_state.pokemon_in_editor
    if not editor_pkm: return
    if move_name in editor_pkm["moves"]:
        st.toast(f"'{move_name.capitalize()}' is already selected.")
        return
    target_slot = st.session_state.active_move_slot
    if target_slot is None:
        try: target_slot = editor_pkm["moves"].index("")
        except ValueError:
            target_slot = st.session_state.circular_move_index
            st.session_state.circular_move_index = (st.session_state.circular_move_index + 1) % 4
    st.session_state.pokemon_in_editor["moves"][target_slot] = move_name
    st.session_state.active_move_slot = None

def render_team_management_section():
    saved_team_names = list(st.session_state.saved_teams.keys())
    selected_team_to_load = st.selectbox("Load a saved team", options=saved_team_names, index=None, placeholder="Select a team to load...")
    if selected_team_to_load:
        team_data = st.session_state.saved_teams[selected_team_to_load]
        st.session_state.team = [Pokemon.from_dict(p_data) for p_data in team_data]
        st.session_state.current_team_name = selected_team_to_load
        st.toast(f"Team '{selected_team_to_load}' loaded!")
        st.session_state[st.session_state.selectbox] = None
        st.rerun()

    save_cols = st.columns([3, 1])
    with save_cols[0]: st.text_input("Team Name", key="current_team_name", label_visibility="collapsed")
    with save_cols[1]:
                if st.button("Save Team", use_container_width=True):
                    team_name = st.session_state.current_team_name
                    if not team_name:
                        st.warning("Please enter a name for your team.")
                    elif not st.session_state.team:
                        st.warning("Your team is empty. Add some Pokémon before saving.")
                    else:
                        serializable_team = [p.to_dict() for p in st.session_state.team]
                        st.session_state.saved_teams[team_name] = serializable_team
                        try:
                            save_team_to_firebase(team_name, serializable_team)
                        except Exception as e:
                            st.warning(f"Could not save to Firebase: {e}")
                        save_teams(st.session_state.saved_teams)
                        st.success(f"Team '{team_name}' saved successfully!")

def render_team_section():
    def remove_pokemon(index):
        if 0 <= index < len(st.session_state.team):
            st.session_state.team.pop(index)

    team_cols = st.columns(6)
    for i in range(6):
        with team_cols[i]:
            if i < len(st.session_state.team):
                pokemon = st.session_state.team[i]
                if pokemon.sprite_data and pokemon.sprite_data.get('icon'):
                    sprite_ref = pokemon.sprite_data['icon']
                    local_path = os.path.join('assets', sprite_ref)
                    if os.path.exists(local_path):
                        st.image(local_path, caption=pokemon.nickname)
                st.button("✖️", key=f"remove_{i}", on_click=remove_pokemon, args=(i,), help="Remove from team")
            else:
                st.markdown('<div style="height:90px; width:60px; border: 2px dashed #555; border-radius: 5px;"></div>', unsafe_allow_html=True)


def render_selected_pokemon_section():
    def add_to_team():
        editor_pkm = st.session_state.pokemon_in_editor
        if len(st.session_state.team) >= 6:
            st.warning("Your team is full (6 Pokémon maximum).")
            return
        if editor_pkm:
            editor_pkm['nickname'] = st.session_state.nickname_input
            new_pokemon = Pokemon(name=editor_pkm["name"], nickname=editor_pkm["nickname"], moves=editor_pkm["moves"])
            st.session_state.team.append(new_pokemon)
            st.toast(f"{new_pokemon.nickname} added to your team!")
            
    selected_pokemon_container = st.container(border=True)
    with selected_pokemon_container:
        pkm_editor = st.session_state.pokemon_in_editor
        pkm_data = POKEMON_DATA.get(st.session_state.selected_pokemon) if st.session_state.selected_pokemon else None
        
        main_cols = st.columns([1, 2])

        with main_cols[0]:
            st.text_input("Nickname", value=pkm_editor["nickname"] if pkm_editor else "", key="nickname_input")
            if pkm_data:
                sprite_ref = None
                sprites = pkm_data.get('sprites', {}) if isinstance(pkm_data, dict) else {}
                for key in ('front', 'front_default', 'front_shiny', 'icon'):
                    if sprites.get(key):
                        sprite_ref = sprites.get(key)
                        break

                if sprite_ref:
                    local_path = os.path.join('assets', sprite_ref)
                    if os.path.exists(local_path):
                        st.image(local_path)
            else: st.markdown('<div style="height:96px; width:96px;"></div>', unsafe_allow_html=True)
            st.text_input("Pokemon", key="search_term", on_change=handle_search_change)
        with main_cols[1]:
            aux_empty = st.empty()
            with aux_empty.container():
                aux_cols = st.columns([1, 1])
                if pkm_data:
                    with aux_cols[0]:
                        st.subheader("Moves")
                        for i in range(4):
                            move_name = pkm_editor["moves"][i] if pkm_editor else ""
                            display_text = move_name.replace('-', ' ').capitalize() if move_name else "---"
                            
                            move_cols = st.columns([2,1])
                            with move_cols[0]:
                                st.button(display_text, key=f"move_slot_{i}", on_click=set_active_move_slot, args=(i,), use_container_width=True)
                            with move_cols[1]:
                                if move_name:
                                    move_info = MOVES_DATA.get(move_name, {})
                                    move_type_ref = move_info.get('type')
                                    if move_type_ref:
                                        move_type_name = resolve_type_ref(move_type_ref)
                                        st.markdown(display_types([move_type_name]) if isinstance(move_type_name, str) else display_types(move_type_name), unsafe_allow_html=True)
                                    else:
                                        st.markdown(display_types(pkm_data['type']), unsafe_allow_html=True)
                    with aux_cols[1]:
                        st.subheader("Stats")
                        stats_cols = st.columns(2)
                        with stats_cols[0]:
                            stats_left = {'HP': 'hp', 'Atk': 'attack', 'Def': 'defense'}
                            for stat_name, stat_key in stats_left.items():
                                st.write(f"**{stat_name}**: {pkm_data.get(stat_key, 'N/A')}")
                        with stats_cols[1]:
                            stats_right = {'Spe': 'speed', 'SpA': 'special_attack', 'SpD': 'special_defense'}
                            for stat_name, stat_key in stats_right.items():
                                st.write(f"**{stat_name}**: {pkm_data.get(stat_key, 'N/A')}")
                        st.write("") 
                        if pkm_editor:
                            st.button("Add to Team", on_click=add_to_team, use_container_width=True, type="primary")
                else:
                    aux_empty.empty()
        
def render_pokemon_list_section():
    header_cols = st.columns([0.5, 2, 3, 1, 1, 1, 1, 1, 1, 1])
    headers = ["", "Name", "Types", "HP", "Attack", "Defense", "Special Attack", "Special Defense", "Speed", "Action"]
    for col, header in zip(header_cols, headers): col.markdown(f"**{header}**")
    
    search_query = st.session_state.get("search_term", "").lower()
    matching_pokemon = [p_name for p_name in POKEMON_DATA if search_query in p_name.lower()]
    filtered_pokemon = sorted(matching_pokemon, key=lambda p_name: POKEMON_DATA[p_name].get('id', 0))
    
    start_index = st.session_state.page_number * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    pokemon_to_display = filtered_pokemon[start_index:end_index]
    
    for pkm_name in pokemon_to_display:
        pkm = POKEMON_DATA[pkm_name]
        list_cols = st.columns([0.5, 2, 3, 1, 1, 1, 1, 1, 1, 1])
        if pkm.get('sprites', {}).get('icon'):
            sprite_ref = pkm['sprites']['icon']
            local_path = os.path.join('assets', sprite_ref)
            if os.path.exists(local_path):
                list_cols[0].image(local_path, width=40)
        list_cols[1].write(pkm["name"])
        types = resolve_type_ref(pkm.get("type", []))
        if isinstance(types, str):
            types = [types]
        list_cols[2].markdown(display_types(types), unsafe_allow_html=True)
        list_cols[3].write(pkm.get("hp", "N/A"))
        list_cols[4].write(pkm.get("attack", "N/A"))
        list_cols[5].write(pkm.get("defense", "N/A"))
        list_cols[6].write(pkm.get("special_attack", "N/A"))
        list_cols[7].write(pkm.get("special_defense", "N/A"))
        list_cols[8].write(pkm.get("speed", "N/A"))
        list_cols[9].button("Select", key=f"select_{pkm_name}", on_click=select_pokemon, args=(pkm_name,))

    st.divider()

    page_cols = st.columns([1, 1, 1])
    with page_cols[0]:
        if st.session_state.page_number > 0:
            if st.button("⬅️ Previous"):
                st.session_state.page_number -= 1
                st.rerun()
    with page_cols[2]:
        if end_index < len(filtered_pokemon):
            if st.button("Next ➡️"):
                st.session_state.page_number += 1
                st.rerun()
    with page_cols[1]:
        total_pages = (len(filtered_pokemon) - 1) // ITEMS_PER_PAGE + 1
        if total_pages > 0:
            st.write(f"Page {st.session_state.page_number + 1} of {total_pages}")


def render_pokemon_moves_section():
    pkm_name = st.session_state.selected_pokemon
    aux_columns = st.columns([1, 3])
    raw_moves = POKEMON_DATA.get(pkm_name, {}).get('moves', [])
    if not raw_moves:
        st.write("This Pokémon has no moves available in the dataset.")
        return

    with aux_columns[0]:
        st.button("⬅️ Back to Pokémon List", on_click=close_moves_view)
    with aux_columns[1]:
        move_search_query = st.text_input("Search for a move...").lower()

    move_id_to_name = {}
    for name, mdata in MOVES_DATA.items():
        mid = mdata.get('id')
        if mid is not None:
            move_id_to_name[str(mid)] = name

    def normalize_move_id(mref):
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

    allowed_moves = []
    for m in raw_moves:
        mid = normalize_move_id(m)
        name = move_id_to_name.get(mid)
        if name:
            allowed_moves.append(name)

    seen = set()
    allowed_moves_ordered = []
    for mv in allowed_moves:
        if mv not in seen:
            seen.add(mv)
            allowed_moves_ordered.append(mv)

    filtered_moves = [mv for mv in allowed_moves_ordered if move_search_query in mv.lower()]

    for idx, move_name in enumerate(filtered_moves):
        move_data = MOVES_DATA.get(move_name, {})
        cols = st.columns([2, 1, 1])
        with cols[0]:
            st.write(move_name.replace('-', ' ').capitalize())
        with cols[1]:
            power = move_data.get('power', 0)
            if power > 0:
                st.write(f"Power: {power}")
            else:
                st.write("Power: ---")
        with cols[2]:
            st.button("Select", key=f"select_move_{move_name}_{idx}", on_click=assign_move, args=(move_name,), use_container_width=True)

def main():
    render_team_management_section()
    st.divider()
    render_team_section()
    st.divider()
    render_selected_pokemon_section()
    st.divider()
    list_placeholder = st.empty()
    with list_placeholder.container():
        if st.session_state.selected_pokemon:
            render_pokemon_moves_section()
        else:
            render_pokemon_list_section()
    
if __name__ == "__main__":
    main()
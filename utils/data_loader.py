import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-secrets.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

@st.cache_data(ttl=3600) 
def load_pokemon_data():
    pokemon_ref = db.collection('pokemon')
    pokemon_docs = pokemon_ref.stream()
    
    pokemon_data = {}
    for doc in pokemon_docs:
        pokemon = doc.to_dict()
        pokemon_name = pokemon['name'].capitalize()
        types = []
        for type_id in pokemon.get('types', []):
            type_name = get_type_name(str(type_id))
            if type_name:
                types.append(type_name.lower())
                
        pokemon_data[pokemon_name] = {
            "id": pokemon['id'],
            "name": pokemon_name,
            "type": types, 
            "moves": pokemon['moves'],
            "hp": pokemon['stats']['hp'],
            "attack": pokemon['stats']['attack'],
            "defense": pokemon['stats']['defense'],
            "special_attack": pokemon['stats']['special_attack'],
            "special_defense": pokemon['stats']['special_defense'],
            "speed": pokemon['stats']['speed'],
            "sprites": pokemon['sprites']
        }
    
    return pokemon_data

@st.cache_data(ttl=3600)
def load_moves_data():
    """Load all moves data from Firebase."""
    moves_ref = db.collection('moves')
    moves_docs = moves_ref.stream()
    
    moves_data = {}
    for doc in moves_docs:
        move = doc.to_dict()
        move_type = get_type_name(str(move.get('type')))
        if move_type:
            move_type = move_type.lower()
            
        moves_data[move['name']] = {
            'id': move['id'],
            'power': move['power'],
            'type': move_type 
        }
    
    return moves_data

@st.cache_data(ttl=3600)
def load_type_effectiveness():
    types_ref = db.collection('types')
    types_docs = types_ref.stream()
    
    type_chart = {}
    for doc in types_docs:
        type_data = doc.to_dict()
        type_name = type_data['name'].lower()
        damage_relations = type_data['damage_relations']
        
        effectiveness = {}
        effectiveness = {get_type_name(str(i)).lower(): 1.0 for i in range(1, 19)}
        
        for target_id in damage_relations['double_damage_to']:
            target_type = get_type_name(str(target_id)).lower()
            effectiveness[target_type] = 2.0
            
        for target_id in damage_relations['half_damage_to']:
            target_type = get_type_name(str(target_id)).lower()
            effectiveness[target_type] = 0.5
            
        for target_id in damage_relations['no_damage_to']:
            target_type = get_type_name(str(target_id)).lower()
            effectiveness[target_type] = 0
            
        type_chart[type_name] = effectiveness
    
    return type_chart

@st.cache_data(ttl=3600)
def get_type_name(type_id):
    type_id = str(type_id).strip('/')
    if not type_id or not type_id.strip(): 
        return 'normal'
    
    type_doc = db.collection('types').document(type_id).get()
    if type_doc.exists:
        type_name = type_doc.to_dict()['name']
        return type_name
    else:
        return 'normal'

def get_pokemon_sprite_url(pokemon_name, front=True):
    pokemon_name = pokemon_name.lower()
    pokemon_data = next(
        (p for p in load_pokemon_data().values() if p['name'].lower() == pokemon_name),
        None
    )
    
    if pokemon_data:
        return pokemon_data['sprites']['front'] if front else pokemon_data['sprites']['back']
    return None

def get_pokemon_icon_url(pokemon_name):
    pokemon_name = pokemon_name.lower()
    pokemon_data = next(
        (p for p in load_pokemon_data().values() if p['name'].lower() == pokemon_name),
        None
    )
    
    if pokemon_data:
        return pokemon_data['sprites']['icon']
    return None

def load_all_data_from_csvs(assets_path="assets"):
    """Depreacted: olhe os commits antigos para entender melhor"""
    pokemon_data = load_pokemon_data()
    moves_data = load_moves_data()
    return pokemon_data, moves_data


def save_team_to_firebase(team_name: str, team_data: list, user_id: str = None):
    teams_ref = db.collection('teams')
    doc_id = f"{user_id}_" + team_name if user_id else team_name
    doc_id = str(doc_id).replace('/', '_')
    payload = {
        'name': team_name,
        'team': team_data,
        'user_id': user_id,
        'updated_at': firestore.SERVER_TIMESTAMP,
    }
    teams_ref.document(doc_id).set(payload)


def load_teams_from_firebase(user_id: str = None):
    teams_ref = db.collection('teams')
    teams = {}
    if user_id:
        docs = teams_ref.where('user_id', '==', user_id).stream()
    else:
        docs = teams_ref.stream()

    for doc in docs:
        data = doc.to_dict()
        name = data.get('name') or doc.id
        teams[name] = data.get('team', [])

    return teams

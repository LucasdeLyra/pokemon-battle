import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import os
from pathlib import Path
from typing import Dict, List
from config import get_firebase_config

# Initialize Firebase with config from environment variables
cred = credentials.Certificate(get_firebase_config())
firebase_admin.initialize_app(cred)
db = firestore.client()

class FirebaseDataLoader:
    def __init__(self):
        self.assets_path = Path("assets")
        self.stat_names = {
            1: "hp",
            2: "attack",
            3: "defense",
            4: "special_attack",
            5: "special_defense",
            6: "speed"
        }

    def load_types(self):

        types_df = pd.read_csv(self.assets_path / "types.csv")
        efficacy_df = pd.read_csv(self.assets_path / "type_efficacy.csv")
        
        # Process type efficacy
        type_relations = {}
        for _, row in efficacy_df.iterrows():
            damage_factor = row['damage_factor'] / 100
            damage_type_id = int(row['damage_type_id'])
            target_type_id = int(row['target_type_id'])
            
            if damage_type_id not in type_relations:
                type_relations[damage_type_id] = {
                    'double_damage_to': [],
                    'half_damage_to': [],
                    'no_damage_to': []
                }
            
            if damage_factor == 2:
                type_relations[damage_type_id]['double_damage_to'].append(target_type_id)
            elif damage_factor == 0.5:
                type_relations[damage_type_id]['half_damage_to'].append(target_type_id)
            elif damage_factor == 0:
                type_relations[damage_type_id]['no_damage_to'].append(target_type_id)

        # Upload types
        types_ref = db.collection('types')
        for _, type_row in types_df.iterrows():
            type_id = int(type_row['id'])
            type_data = {
                'id': str(type_id),
                'name': str(type_row['identifier']),
                'damage_relations': {
                    'double_damage_to': [int(x) for x in type_relations.get(type_id, {'double_damage_to': []})['double_damage_to']],
                    'half_damage_to': [int(x) for x in type_relations.get(type_id, {'half_damage_to': []})['half_damage_to']],
                    'no_damage_to': [int(x) for x in type_relations.get(type_id, {'no_damage_to': []})['no_damage_to']]
                }
            }
            types_ref.document(str(type_id)).set(type_data)

    def load_moves(self):
        print("Loading moves...")
        moves_df = pd.read_csv(self.assets_path / "moves.csv")
        moves_ref = db.collection('moves')
        
        for _, move in moves_df.iterrows():
            move_data = {
                'id': str(int(move['id'])),
                'name': str(move['identifier']),
                'type': str(int(move['type_id'])),
                'power': int(move['power']) if not pd.isna(move['power']) else 0,
            }
            moves_ref.document(str(move['id'])).set(move_data)

    def load_pokemon(self):
        pokemon_df = pd.read_csv(self.assets_path / "pokemon.csv")[:493]
        pokemon_stats_df = pd.read_csv(self.assets_path / "pokemon_stats.csv")
        pokemon_types_df = pd.read_csv(self.assets_path / "pokemon_types.csv")
        pokemon_moves_df = pd.read_csv(self.assets_path / "pokemon_moves.csv")

        # Process Pokemon data
        pokemon_ref = db.collection('pokemon')

        for _, pokemon in pokemon_df.iterrows():
            pokemon_id = str(pokemon['id'])
            
            # Get stats
            stats = {}
            pokemon_stats = pokemon_stats_df[pokemon_stats_df['pokemon_id'] == pokemon['id']]
            for _, stat in pokemon_stats.iterrows():
                stat_name = self.stat_names[int(stat['stat_id'])]
                stats[stat_name] = int(stat['base_stat'])

            # Get types
            types = pokemon_types_df[pokemon_types_df['pokemon_id'] == pokemon['id']]['type_id'].tolist()
            
            # Get moves
            pokemon_moves = pokemon_moves_df[pokemon_moves_df['pokemon_id'] == pokemon['id']]
            moves_list = [str(move['move_id']) for _, move in pokemon_moves.iterrows()]
            
            # Create sprite and icon paths
            sprite_front = f"sprites/front/default/{pokemon_id}.png"
            sprite_back = f"sprites/back/{pokemon_id}.png"
            icon = f"icons/{pokemon_id}.png"

            # Create Pokemon document
            pokemon_data = {
                'id': pokemon_id,
                'name': pokemon['identifier'],
                'stats': stats,
                'types': [str(t) for t in types],
                'moves': moves_list,
                'sprites': {
                    'front': sprite_front,
                    'back': sprite_back,
                    'icon': icon
                }
            }
            pokemon_ref.document(pokemon_id).set(pokemon_data)

    def load_all_data(self):
        #self.load_types()
        #self.load_moves()
        self.load_pokemon()

if __name__ == "__main__":
    loader = FirebaseDataLoader()
    loader.load_all_data()
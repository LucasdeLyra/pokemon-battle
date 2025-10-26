# app.py
# --- RESPONSIBILITY: The main landing page of the application. ---
import streamlit as st

st.set_page_config(
    page_title="Streamlit Pokémon Battle Simulator",
    page_icon="🔥",
    layout="wide"
)

st.title("Boas vindas ao simulador de batalha pokemon")

st.markdown("""
Como jogar:
1) Crie uma equipe de Pokémon na página "Team Selection".
2) Clique em Battle e vença todos com sua equipe!

PS: Se não quiser usar uma equipe, pode ir direto ao "Battle" e usar um time gerado aleatoriamente.
""")


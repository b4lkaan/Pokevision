import json
import streamlit as st

@st.cache_data
def load_data():
    """
    Loads the Pokémon data from a JSON file.
    """
    with open("combined_database.json", "r", encoding="utf-8") as file:
        return json.load(file)

def get_unique_types(data):
    """
    Extracts a sorted list of unique Pokémon types.
    Assumes each Pokémon has a "types" list.
    """
    types = set()
    for pokemon in data.get("pokemon", []):
        for t in pokemon.get("types", []):
            types.add(t)
    return sorted(list(types))

def get_unique_regions(data):
    """
    Extracts a sorted list of unique regions from the Pokémon data.
    Assumes each Pokémon has a "region" field.
    """
    regions = set()
    for pokemon in data.get("pokemon", []):
        region = pokemon.get("region")
        if region:
            regions.add(region)
    return sorted(list(regions))

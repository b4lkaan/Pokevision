import json
import time
from tqdm import tqdm
import requests
import requests_cache

# Setup caching for API requests.
# Responses are cached in an SQLite database ('pokeapi_cache.sqlite') for 24 hours.
session = requests_cache.CachedSession('pokeapi_cache', backend='sqlite', expire_after=86400)

# Base API URL
POKEAPI_URL = "https://pokeapi.co/api/v2/"

def fetch_data(url: str) -> dict:
    """
    Fetches JSON data from a given API URL with error handling and caching.
    
    :param url: The API endpoint URL.
    :return: Parsed JSON data (as a dictionary) or None if request fails.
    """
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            # Optionally, you can print if the response was loaded from cache:
            # print(f"Cache hit for {url}: {getattr(response, 'from_cache', False)}")
            return response.json()
        else:
            print(f"Error: Failed to fetch {url} (Status Code: {response.status_code})")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {url}: {e}")
        return None

def fetch_pokemon_variants(varieties: list) -> list:
    """
    Fetches variant-specific Pokémon data such as types, stats, and abilities.
    
    :param varieties: List of variant dictionaries from species data.
    :return: List of dictionaries with variant details.
    """
    variants = []
    for variant in varieties:
        variant_data = fetch_data(variant["pokemon"]["url"])
        if not variant_data:
            continue

        variant_entry = {
            "name": variant_data["name"],
            "types": [t["type"]["name"] for t in variant_data["types"]],
            "base_stats": {stat["stat"]["name"]: stat["base_stat"] for stat in variant_data["stats"]},
            "abilities": fetch_abilities(variant_data["abilities"]),
            "image_url": variant_data["sprites"]["other"]["official-artwork"]["front_default"],
        }
        variants.append(variant_entry)
    return variants

def fetch_evolution_chain(url: str) -> list:
    """
    Retrieves the evolution chain including requirements for each stage.
    
    :param url: URL of the evolution chain.
    :return: A list of evolution stages.
    """
    chain_data = fetch_data(url)
    if not chain_data:
        return []

    evolution_chain = []

    def extract_evolution(evo_data: dict):
        """Recursively extracts evolution details."""
        species_name = evo_data["species"]["name"]
        evolves_to = evo_data.get("evolves_to", [])

        evolution_entry = {
            "name": species_name,
            "evolution_details": evo_data.get("evolution_details", [])
        }
        evolution_chain.append(evolution_entry)

        for next_evo in evolves_to:
            extract_evolution(next_evo)

    extract_evolution(chain_data["chain"])
    return evolution_chain

def fetch_abilities(abilities: list) -> list:
    """
    Fetches detailed ability descriptions.
    
    :param abilities: List of abilities from variant data.
    :return: List of dictionaries with ability details.
    """
    ability_list = []
    for ability in abilities:
        ability_data = fetch_data(ability["ability"]["url"])
        if not ability_data:
            continue

        description = next(
            (entry["effect"] for entry in ability_data.get("effect_entries", []) if entry["language"]["name"] == "en"),
            "No description available"
        )

        ability_list.append({
            "name": ability_data["name"],
            "description": description
        })

    return ability_list

def fetch_all_pokemon() -> list:
    """
    Fetches all Pokémon species with their National Dex numbers and variants.
    
    :return: List of Pokémon species data.
    """
    url = f"{POKEAPI_URL}pokemon-species?limit=10000"
    data = fetch_data(url)
    if not data:
        return []

    pokemon_list = []
    for species in tqdm(data['results'], desc="Fetching Pokémon Species"):
        species_data = fetch_data(species['url'])
        if not species_data:
            continue

        pokemon_entry = {
            "dex_number": species_data["id"],
            "name": species_data["name"],
            "variants": fetch_pokemon_variants(species_data["varieties"]),
            "evolution_chain": fetch_evolution_chain(species_data["evolution_chain"]["url"]),
        }
        pokemon_list.append(pokemon_entry)

    return pokemon_list

def fetch_all_abilities() -> list:
    """
    Fetches all abilities with descriptions.
    
    :return: List of abilities data.
    """
    url = f"{POKEAPI_URL}ability?limit=1000"
    data = fetch_data(url)
    if not data:
        return []

    abilities = []
    for ability in tqdm(data["results"], desc="Fetching Abilities"):
        ability_details = fetch_data(ability["url"])
        if not ability_details:
            continue

        description = next(
            (entry["effect"] for entry in ability_details.get("effect_entries", []) if entry["language"]["name"] == "en"),
            "No description available"
        )

        abilities.append({
            "name": ability_details["name"],
            "description": description
        })

    return abilities

def fetch_all_items() -> list:
    """
    Fetches all held items and their descriptions.
    
    :return: List of items data.
    """
    url = f"{POKEAPI_URL}item?limit=1000"
    data = fetch_data(url)
    if not data:
        return []

    items = []
    for item in tqdm(data["results"], desc="Fetching Items"):
        item_details = fetch_data(item["url"])
        if not item_details:
            continue

        description = next(
            (entry["text"] for entry in item_details.get("flavor_text_entries", []) if entry["language"]["name"] == "en"),
            "No description available"
        )

        items.append({
            "name": item_details["name"],
            "description": description
        })

    return items

def fetch_all_moves() -> list:
    """
    Fetches all Pokémon moves and their learning methods.
    
    :return: List of moves data.
    """
    url = f"{POKEAPI_URL}move?limit=1000"
    data = fetch_data(url)
    if not data:
        return []

    moves = []
    for move in tqdm(data["results"], desc="Fetching Moves"):
        move_details = fetch_data(move["url"])
        if not move_details:
            continue

        description = next(
            (entry["effect"] for entry in move_details.get("effect_entries", []) if entry["language"]["name"] == "en"),
            "No description available"
        )

        moves.append({
            "name": move_details["name"],
            "description": description,
            "method": [pokemon["name"] for pokemon in move_details.get("learned_by_pokemon", [])]
        })

    return moves

def fetch_all_natures() -> list:
    """
    Fetches all Pokémon natures and their effects.
    
    :return: List of natures data.
    """
    url = f"{POKEAPI_URL}nature?limit=100"
    data = fetch_data(url)
    if not data:
        return []

    natures = []
    for nature in tqdm(data["results"], desc="Fetching Natures"):
        nature_details = fetch_data(nature["url"])
        if not nature_details:
            continue

        natures.append({
            "name": nature_details["name"],
            "increased_stat": nature_details["increased_stat"]["name"] if nature_details.get("increased_stat") else None,
            "decreased_stat": nature_details["decreased_stat"]["name"] if nature_details.get("decreased_stat") else None
        })

    return natures

def compile_pokemon_database():
    """
    Compiles the complete Pokémon database and saves it as a JSON file.
    """
    database = {
        "pokemon": fetch_all_pokemon(),
        "abilities": fetch_all_abilities(),
        "items": fetch_all_items(),
        "moves": fetch_all_moves(),
        "natures": fetch_all_natures(),
    }

    with open("pokemon_database.json", "w", encoding="utf-8") as f:
        json.dump(database, f, indent=4, ensure_ascii=False)

    print("Database successfully compiled and saved as 'pokemon_database.json'.")

if __name__ == "__main__":
    compile_pokemon_database()

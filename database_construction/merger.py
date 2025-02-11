import json

# Allowed format/tier keys (all lower-case)
ALLOWED_FORMATS = {"anythinggoes", "ubers", "ubersuu", "ou", "uu", "ru", "nu", "pu", "zu", "nfe", "lc"}

def merge_sets_into_database(database, gen9_data):
    """
    For each Pokémon variant in the database (database["pokemon"] is a list of Pokémon objects),
    if the variant's name (lowercase) matches a key in gen9_data (also lowercased),
    then add a new key "sets" to that variant containing only the allowed formats/tier sets
    from gen9_data.
    """
    # Build a lookup from gen9 data using lowercased Pokémon names.
    gen9_lookup = {pokemon_name.lower(): sets_data for pokemon_name, sets_data in gen9_data.items()}
    
    # Iterate over each Pokémon object in the database.
    for pokemon_obj in database.get("pokemon", []):
        # Process each variant for this Pokémon.
        for variant in pokemon_obj.get("variants", []):
            variant_name = variant.get("name", "").lower()
            if variant_name in gen9_lookup:
                # Get all sets for this variant from gen9.json.
                variant_gen9_sets = gen9_lookup[variant_name]
                # Filter out only allowed formats.
                allowed_sets = {}
                for format_key, set_info in variant_gen9_sets.items():
                    if format_key.lower() in ALLOWED_FORMATS:
                        allowed_sets[format_key] = set_info
                # If any allowed sets were found, add them to the variant under "sets".
                if allowed_sets:
                    if "sets" in variant:
                        variant["sets"].update(allowed_sets)
                    else:
                        variant["sets"] = allowed_sets
    return database

def main():
    # Load the original database (expects a JSON object with key "pokemon": [ ... ])
    with open("database.json", "r", encoding="utf-8") as db_file:
        database = json.load(db_file)
    
    # Load the gen9 sets database.
    with open("gen9.json", "r", encoding="utf-8") as gen9_file:
        gen9_data = json.load(gen9_file)
    
    # Merge the allowed gen9 sets into the corresponding Pokémon variants.
    merged_database = merge_sets_into_database(database, gen9_data)
    
    # Save the merged database to a new file.
    with open("combined_database.json", "w", encoding="utf-8") as out_file:
        json.dump(merged_database, out_file, indent=4)
    
    print("Merge complete. The combined database has been saved to 'combined_database.json'.")

if __name__ == "__main__":
    main()

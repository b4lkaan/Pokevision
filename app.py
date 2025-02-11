import streamlit as st
from data import load_data, get_unique_types, get_unique_regions
from visualizations import create_radar_chart
from rapidfuzz import process, fuzz

# -------------------------------------
# Page Configuration & Custom CSS
# -------------------------------------
st.set_page_config(page_title="PokeVision", page_icon="final_logo.png", layout="centered")

custom_css = """
<style>
body {
    background-color: #f0f2f6;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.title-container {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}
.title {
    font-size: 48px;
    font-weight: 700;
    color: #ff6f61;
    text-align: center;
}
.subtitle {
    font-size: 24px;
    font-weight: 600;
    color: #333;
    margin-top: 1em;
}
.stat-bar {
    background-color: #e0e0e0;
    border-radius: 5px;
    height: 20px;
    margin-bottom: 10px;
}
.stat-fill {
    height: 20px;
    border-radius: 5px;
}
.container {
    padding: 20px;
    background-color: white;
    border-radius: 10px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.expander {
    background-color: #fafafa;
    border-radius: 8px;
    padding: 10px;
    margin-top: 10px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------
# Title & Logo
# -------------------------------------
col1, col2 = st.columns([1, 5])
with col1:
    st.image("final_logo.png", width=200)
with col2:
    st.markdown("<div class='title'>PokeVision</div>", unsafe_allow_html=True)

# -------------------------------------
# Data Loading
# -------------------------------------
data = load_data()

# -------------------------------------
# Sidebar Navigation & Filters
# -------------------------------------
st.sidebar.header("Filter Pokémon")
all_types = get_unique_types(data)
selected_types = st.sidebar.multiselect("Select Type(s)", options=all_types)
all_regions = get_unique_regions(data)
selected_regions = st.sidebar.multiselect("Select Region(s)", options=all_regions)

# -------------------------------------
# Prepopulate Search Field if Jumping via Evolution Chain
# -------------------------------------
# When a user clicks an evolution chain button, we store its name under "selected_evo".
# Then, we use that as the default value for the search input.
if "selected_evo" in st.session_state:
    default_search_query = st.session_state.pop("selected_evo")
    if "search_query" in st.session_state:
        del st.session_state["search_query"]
else:
    default_search_query = ""

# Main search input with a default value (for evolution jumps)
search_query = st.text_input(
    "Enter Pokémon Name or National Dex Number:",
    value=default_search_query,
    key="search_query",
    help="Type part of the Pokémon name or its Dex number."
)

selected_pokemon = None
if search_query:
    # First, filter Pokémon by the sidebar selections.
    filtered_pokemon = [
        p for p in data.get("pokemon", [])
        if ((not selected_types) or any(t in p.get("types", []) for t in selected_types))
        and ((not selected_regions) or (p.get("region") in selected_regions))
    ]
    
    # --- Numeric Search: If the query is a number, try to match dex_number exactly ---
    if search_query.isdigit():
        selected_pokemon = next(
            (p for p in filtered_pokemon if str(p.get("dex_number", "")) == search_query),
            None
        )
        if selected_pokemon is None:
            st.error("No Pokémon found with that dex number!")
    else:
        # --- Fuzzy Matching on Names ---
        names_list = [p["name"] for p in filtered_pokemon]
        suggestions = process.extract(search_query, names_list, scorer=fuzz.partial_ratio, limit=10)
        # Only include suggestions above a given threshold.
        suggestions = [match for match, score, _ in suggestions if score >= 50]

        if suggestions:
            selected_name = st.selectbox("Select Pokémon", options=suggestions, key="selected_pokemon")
            # Ensure we pick the Pokémon from the filtered list.
            selected_pokemon = next(
                (p for p in filtered_pokemon if p["name"].lower() == selected_name.lower()),
                None
            )
        else:
            st.error("No Pokémon found with that query!")
else:
    st.info("Start by typing a Pokémon name or Dex number above.")

# -------------------------------------
# Display Pokémon Details if Found
# -------------------------------------
if selected_pokemon:
    # Pokémon Header (Name & Dex Number)
    st.markdown(
        f'<div class="subtitle">#{selected_pokemon["dex_number"]} - {selected_pokemon["name"].capitalize()}</div>',
        unsafe_allow_html=True,
    )
    
    # Variant Selection (if multiple variants exist)
    variants = selected_pokemon.get("variants", [])
    if variants:
        if len(variants) > 1:
            variant_options = [v["name"] for v in variants]
            selected_variant_name = st.selectbox("Select Variant", variant_options, key="selected_variant")
            variant = next((v for v in variants if v["name"] == selected_variant_name), variants[0])
        else:
            variant = variants[0]
            
        # Display Pokémon Image with alt text for accessibility.
        st.image(
            variant["image_url"],
            caption=variant["name"].capitalize(),
            use_container_width=True
        )
    else:
        st.error("No variant information available.")

    # Main Content Container with Tabs
    st.markdown('<div class="container">', unsafe_allow_html=True)
    tabs = st.tabs(["Base Stats", "Abilities", "Competitive Sets", "Evolution Chain"])

    # --- Base Stats Tab (with Radar Chart) ---
    with tabs[0]:
        st.markdown('<div class="subtitle">Base Stats</div>', unsafe_allow_html=True)
        base_stats = variant.get("base_stats", {})
        if base_stats:
            radar_chart = create_radar_chart(base_stats)
            st.plotly_chart(radar_chart, use_container_width=True)
        else:
            st.info("No base stats available.")

    # --- Abilities Tab ---
    with tabs[1]:
        st.markdown('<div class="subtitle">Abilities</div>', unsafe_allow_html=True)
        abilities = variant.get("abilities", [])
        if abilities:
            for ability in abilities:
                st.markdown(f"**{ability['name'].capitalize()}**")
                st.write(ability.get("description", ""))
        else:
            st.info("No abilities available.")

    # --- Competitive Sets Tab (Enhanced Styling) ---
    with tabs[2]:
        st.markdown('<div class="subtitle">Competitive Sets</div>', unsafe_allow_html=True)
        sets_data = variant.get("sets", {})
        if sets_data:
            # Iterate over each competitive tier (e.g., LC, OU, NU, etc.)
            for tier, sets_dict in sets_data.items():
                st.markdown(f"### {tier.upper()}")
                for set_name, set_data in sets_dict.items():
                    with st.expander(set_name):
                        # Display Moves with an icon
                        st.markdown("**Moves:** ⚔️")
                        moves = set_data.get("moves", [])
                        if moves:
                            for move in moves:
                                if isinstance(move, list):
                                    st.write(", ".join(move))
                                else:
                                    st.write(move)
                        else:
                            st.write("N/A")
                        # Display Ability, Item, Nature with emoji icons
                        st.markdown(f"**Ability:** ⭐ {set_data.get('ability', 'N/A')}")
                        st.markdown(f"**Item:** 🎒 {set_data.get('item', 'N/A')}")
                        st.markdown(f"**Nature:** 🌿 {set_data.get('nature', 'N/A')}")
                        st.markdown("**IVs:**")
                        st.write(set_data.get("ivs", {}))
                        st.markdown("**EVs:**")
                        st.write(set_data.get("evs", {}))
                        st.markdown(f"**Tera Types:** {set_data.get('teratypes', 'N/A')}")
        else:
            st.info("No competitive sets available for this variant.")

    # --- Evolution Chain Tab (Clickable Nodes) ---
    with tabs[3]:
        st.markdown('<div class="subtitle">Evolution Chain</div>', unsafe_allow_html=True)
        evolution_chain = selected_pokemon.get("evolution_chain", [])
        if evolution_chain:
            st.write("Click on a Pokémon to load its details:")
            # Display clickable buttons in a row.
            cols = st.columns(len(evolution_chain))
            for i, evo in enumerate(evolution_chain):
                with cols[i]:
                    if st.button(evo["name"].capitalize(), key=f"evo_{i}"):
                        st.session_state["selected_evo"] = evo["name"]
                        if "search_query" in st.session_state:
                            del st.session_state["search_query"]
                        try:
                            st.rerun()
                        except AttributeError:
                            try:
                                st._rerun()  # fallback for older versions
                            except Exception:
                                st.write("Please refresh the page.")
                                st.stop()
        else:
            st.info("No evolution chain data available.")
    st.markdown("</div>", unsafe_allow_html=True)

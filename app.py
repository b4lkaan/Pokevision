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
    box_shadow: 0px 4px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
.expander {
    background-color: #fafafa;
    border-radius: 8px;
    padding: 10px;
    margin-top: 10px;
}
.logo-title-container {
    display: flex;
    flex_direction: column;
    align_items: center;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# -------------------------------------
# Title & Logo
# -------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("<div class='logo-title-container'>", unsafe_allow_html=True)
    st.image("final_logo.png", width=500)
   

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
# Session State and Search Query
# -------------------------------------
if "search_query" not in st.session_state:
    st.session_state["search_query"] = "" # Initialize search_query in session state

if "selected_evo" in st.session_state:
    st.session_state["search_query"] = st.session_state.pop("selected_evo") # Update search_query from evo chain

current_search_query = st.text_input(
    "Enter Pokémon Name or National Dex Number:",
    value=st.session_state["search_query"], # Use session state for text input value
    key="search_input", # Fixed key for text input
    help="Type part of the Pokémon name or its Dex number."
)

# Update session state search_query on text input change
st.session_state["search_query"] = current_search_query
search_query = st.session_state["search_query"] # sync local variable with session state


# -------------------------------------
# Pokémon Filtering and Selection (Direct Filtering)
# -------------------------------------
selected_pokemon = None
if search_query:
    filtered_pokemon = [
        p for p in data.get("pokemon", [])
        if ((not selected_types) or any(t in p.get("types", []) for t in selected_types))
        and ((not selected_regions) or (p.get("region") in selected_regions))
    ]

    if search_query.isdigit():
        selected_pokemon = next(
            (p for p in filtered_pokemon if str(p.get("dex_number", "")) == search_query),
            None
        )
        if selected_pokemon is None:
            st.error("No Pokémon found with that dex number!")
    else:
        # --- Direct Filtering (NO SELECTBOX) ---
        # If we came from the evolution chain, search_query will be the exact name.
        exact_matches = [p for p in filtered_pokemon if p["name"].lower() == search_query.lower()]
        if exact_matches:
            selected_pokemon = exact_matches[0]  # Take the first exact match.

        # --- Fuzzy Matching (Only if no exact match) ---
        else:
            names_list = [p["name"] for p in filtered_pokemon]
            suggestions = process.extract(search_query, names_list, scorer=fuzz.partial_ratio, limit=10)
            suggestions = [match for match, score, _ in suggestions if score >= 50]

            if suggestions:
                selected_name = st.selectbox("Select Pokémon", options=[s[0] for s in suggestions], key="selected_pokemon")
                selected_pokemon = next(
                    (p for p in filtered_pokemon if p["name"].lower() == selected_name.lower()),
                    None
                )
            else:
                st.error("No Pokémon found with that query!")
else:
    st.info("Start by typing a Pokémon name or Dex number above.")


# -------------------------------------
# Display Pokémon Details
# -------------------------------------
if selected_pokemon:
    st.markdown(
        f'<div class="subtitle">#{selected_pokemon["dex_number"]} - {selected_pokemon["name"].capitalize()}</div>',
        unsafe_allow_html=True,
    )

    variants = selected_pokemon.get("variants", [])
    if variants:
        if len(variants) > 1:
            variant_options = [v["name"] for v in variants]
            selected_variant_name = st.selectbox("Select Variant", variant_options, key="selected_variant")
            variant = next((v for v in variants if v["name"] == selected_variant_name), variants[0])
        else:
            variant = variants[0]

        st.image(
            variant["image_url"],
            caption=variant["name"].capitalize(),
            use_container_width=True
        )
    else:
        st.error("No variant information available.")

    st.markdown('<div class="container">', unsafe_allow_html=True)
    tabs = st.tabs(["Base Stats", "Abilities", "Competitive Sets", "Evolution Chain"])

    with tabs[0]:
        st.markdown('<div class="subtitle">Base Stats</div>', unsafe_allow_html=True)
        base_stats = variant.get("base_stats", {})
        if base_stats:
            radar_chart = create_radar_chart(base_stats)
            st.plotly_chart(radar_chart, use_container_width=True)
        else:
            st.info("No base stats available.")

    with tabs[1]:
        st.markdown('<div class="subtitle">Abilities</div>', unsafe_allow_html=True)
        abilities = variant.get("abilities", [])
        if abilities:
            for ability in abilities:
                st.markdown(f"**{ability['name'].capitalize()}**")
                st.write(ability.get("description", ""))
        else:
            st.info("No abilities available.")

    with tabs[2]:
        st.markdown('<div class="subtitle">Competitive Sets</div>', unsafe_allow_html=True)
        sets_data = variant.get("sets", {})
        if sets_data:
            for tier, sets_dict in sets_data.items():
                st.markdown(f"### {tier.upper()}")
                for set_name, set_data in sets_dict.items():
                    with st.expander(set_name):
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

    with tabs[3]:
        st.markdown('<div class="subtitle">Evolution Chain</div>', unsafe_allow_html=True)
        evolution_chain = selected_pokemon.get("evolution_chain", [])
        if evolution_chain:
            st.write("Click on a Pokémon to load its details:")
            cols = st.columns(len(evolution_chain))
            for i, evo in enumerate(evolution_chain):
                with cols[i]:
                    if st.button(evo["name"].capitalize(), key=f"evo_{i}"):
                        st.session_state["selected_evo"] = evo["name"]
                        try:
                            st.rerun()
                        except AttributeError:
                            try:
                                st._rerun()  # Fallback for older versions
                            except Exception:
                                st.write("Please refresh the page.")
                                st.stop()
        else:
            st.info("No evolution chain data available.")
    st.markdown("</div>", unsafe_allow_html=True)
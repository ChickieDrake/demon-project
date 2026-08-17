import streamlit as st
from Cacodemon_Generator import generate_cacodemon_base, format_stats_block


st.title("Cacodemon Generator")

# This generator always produces Imps.
RANK = "Imp"

FORMS = ["Arachnine", "Humanoid", "Monadine", "Scolopendrine", "Wyverine"]

# The signature ability each non-humanoid form contributes. When a form is
# chosen, this becomes the label of the "apply signature" toggle. Humanoid has
# no signature ability, so the toggle is hidden for it.
SIGNATURE_TOGGLE_LABELS = {
    "Arachnine": "Poison",
    "Monadine": "Swallow Attack",
    "Scolopendrine": "Paralysis",
    "Wyverine": "Dive Attack or Berserk",
}

# --- Choice Mode: two independent options, both off by default ---
choose_form = st.toggle("Choose body form")
body_form = st.selectbox("Body Form", FORMS) if choose_form else None

# Signature-ability toggle. Its label is the specific ability when a form is
# chosen, and generic otherwise. Hidden entirely for Humanoid (no signature).
signature_choice = None
if not (choose_form and body_form == "Humanoid"):
    if body_form is not None:
        label = SIGNATURE_TOGGLE_LABELS[body_form]
    else:
        label = "Apply signature ability"
    if st.toggle(label):
        signature_choice = True
    if body_form is None:
        st.caption("Applies the signature ability of whichever form is rolled (Humanoid has none).")

# --- Generate (stored in session so expanders don't trigger regeneration) ---
if st.button("Generate Cacodemon"):
    st.session_state.demon = generate_cacodemon_base(
        RANK, body_form=body_form, signature_choice=signature_choice
    )

# --- Render ---
demon = st.session_state.get("demon")
if demon:
    wing_status = "Winged" if demon["body_form"][1] else "Non-Winged"
    st.subheader(f"{demon['rank']} Cacodemon")
    st.markdown(f"**Form:** {demon['body_form'][0]}, {wing_status}")

    # Special Abilities, right after the form. Each shows only its name until
    # expanded. Base Resistances and Telepathy are baseline traits shown here too.
    st.markdown("**Special Abilities**")
    with st.expander("Base Resistances"):
        st.write("Resists acidic, cold, electrical, fire, poisonous, and seismic damage")
    with st.expander("Telepathy"):
        st.write("Can communicate telepathically with any creatures they encounter")

    for ab in demon["abilities"]["abilities"]:
        with st.expander(ab["name"]):
            st.write(ab["description"])
            detail = ab["detail"][0]
            if detail != "" and detail != "(":
                if isinstance(detail, dict):
                    for spell_info in detail.values():
                        st.write(f"{spell_info['spell']}: {spell_info['usage_string']}")
                else:
                    st.write(f"**Detail:** {detail}")

    # Full stat block, collapsed by default.
    with st.expander("Stats", expanded=False):
        st.text(format_stats_block(demon))

import streamlit as st
from Cacodemon_Generator import generate_cacodemon_base, format_stats_block, value_symbols


st.title("Imp Generator")

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
        label = f"{SIGNATURE_TOGGLE_LABELS[body_form]} (signature form ability)"
    else:
        label = "Apply signature form ability"
    # On -> always force the signature. Off -> never force it (fully random: it
    # only turns up if rolled like any other ability). Percent -> force it with
    # the chosen probability.
    mode = st.radio(label, ["On", "Off (fully random)", "Percent"], index=0, horizontal=True)
    if mode == "On":
        signature_choice = True
    elif mode == "Off (fully random)":
        signature_choice = False
    else:
        signature_choice = st.slider("Chance to apply it (%)", 0, 100, 50) / 100

# --- Generate (stored in session so expanders don't trigger regeneration) ---
if st.button("Generate Cacodemon"):
    st.session_state.demon = generate_cacodemon_base(
        RANK, body_form=body_form, signature_choice=signature_choice
    )

# --- Render ---
demon = st.session_state.get("demon")
if demon:
    wing_status = "Winged" if demon["body_form"][1] else "Non-Winged"
    st.subheader(demon["name"])
    st.markdown(f"**Form:** {demon['body_form'][0]}, {wing_status}")

    # Special Abilities, right after the form. Each shows only its name until
    # expanded. (Base Resistances and Telepathy are constant, so they live in
    # the Stats block instead -- Telepathy via the Languages line.)
    st.markdown(f"**Special Abilities** — {value_symbols(demon['abilities']['total_cost'])} total")

    for ab in demon["abilities"]["abilities"]:
        with st.expander(f"{ab['name']} ({value_symbols(ab['cost'])})"):
            st.write(ab["description"])
            detail = ab["detail"][0]
            if detail != "" and detail != "(":
                if isinstance(detail, dict):
                    for spell_info in detail.values():
                        st.write(f"{spell_info['spell']}: {spell_info['usage_string']}")
                else:
                    st.write(f"**Detail:** {detail}")

    # Stats as its own section (heading styled like Form / Special Abilities),
    # with a show/hide control underneath rather than an ability-like expander.
    st.markdown("**Stats**")
    if st.toggle("Show stats"):
        st.text(format_stats_block(demon))

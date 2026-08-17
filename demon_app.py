import streamlit as st
from Cacodemon_Generator import generate_cacodemon_base, format_cacodemon_statblock


st.title("Cacodemon Generator")

# This generator always produces Imps.
RANK = "Imp"

FORMS = ["Arachnine", "Humanoid", "Monadine", "Scolopendrine", "Wyverine"]

# The signature ability each non-humanoid form can contribute. Wyverine's
# depends on wings (which stay random), so it is described rather than named.
SIGNATURE_LABELS = {
    "Arachnine": "Poison",
    "Monadine": "Swallow Attack (only if Huge or larger)",
    "Scolopendrine": "Paralysis",
    "Wyverine": "Dive Attack if winged, otherwise Berserk",
}

# --- Choice Mode: two independent options, both off by default ---
choose_form = st.toggle("Choose body form")
body_form = st.selectbox("Body Form", FORMS) if choose_form else None

choose_signature = st.toggle("Choose signature ability")
# Off -> None (rolled randomly, ~90%). On -> True (guaranteed to be included).
signature_choice = True if choose_signature else None

if choose_signature:
    if body_form is None:
        st.caption("The signature ability of whichever form is rolled will be included.")
    elif body_form == "Humanoid":
        st.caption("Humanoid has no signature ability, so this has no effect.")
    else:
        st.caption(f"Signature ability to include: {SIGNATURE_LABELS[body_form]}")

# Initialize session state for storing generated output
if "statblock" not in st.session_state:
    st.session_state.statblock = ""

# When button is clicked, regenerate and store the new statblock
if st.button("Generate Cacodemon"):
    demon = generate_cacodemon_base(RANK, body_form=body_form, signature_choice=signature_choice)
    st.session_state.statblock = format_cacodemon_statblock(demon)

# Show the current statblock from session state (even if inputs are changed)
if st.session_state.statblock:
    st.subheader("Generated Cacodemon")
    st.text(st.session_state.statblock)

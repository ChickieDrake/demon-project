import streamlit as st

from Cacodemon_Generator import (
    generate_cacodemon_base,
    condensed_stats,
    stat_block_rows,
    abilities_oneliner,
    value_symbols,
)

st.set_page_config(page_title="Imp", page_icon="🕷️",
                   layout="centered", initial_sidebar_state="collapsed")

RANK = "Imp"          # this generator always produces Imps
FORMS = ["Arachnine", "Humanoid", "Monadine", "Scolopendrine", "Wyverine"]
SIGNATURE_TOGGLE_LABELS = {
    "Arachnine": "Poison",
    "Monadine": "Swallow Attack",
    "Scolopendrine": "Paralysis",
    "Wyverine": "Dive Attack or Berserk",
}

# --- Styling: hide Streamlit chrome, compact the page, pin the corner buttons.
st.markdown("""
<style>
  #MainMenu, header, footer,
  [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stStatusWidget"] { display: none !important; }

  /* minimal margins; content runs full width under the corner buttons */
  .block-container { padding: .7rem 1rem 3rem 1rem !important; max-width: 480px; }

  /* corner buttons: spider on top, gear below, both top-right */
  .st-key-spiderbtn, .st-key-gearbtn { position: fixed; right: .5rem; z-index: 1000; width: auto; }
  .st-key-spiderbtn { top: .5rem; }
  .st-key-gearbtn   { top: 5.2rem; }
  .st-key-spiderbtn button {
      border-radius: 50%; width: 4rem; height: 4rem; padding: 0; font-size: 2.2rem;
      line-height: 1; }
  .st-key-gearbtn [data-testid="stPopover"] > button {
      border-radius: 50%; width: 2.7rem; height: 2.7rem; padding: 0; font-size: 1.1rem;
      line-height: 1; }

  /* imp card */
  .impname { font-size: 1.7rem; font-weight: 700; line-height: 1.1; }
  .impform { opacity: .6; font-size: .9rem; margin-bottom: .4rem; }
  .statline { font-size: .95rem; line-height: 1.35; font-weight: 500;
              border-top: 1px solid rgba(128,128,128,.3);
              border-bottom: 1px solid rgba(128,128,128,.3);
              padding: .4rem 0; margin-bottom: .4rem; }
  .inforow { font-size: .9rem; line-height: 1.35; }
  .inforow .lbl { opacity: .55; }

  /* no-imp hint, tucked to the left of the spider */
  .tapnote { position: fixed; top: 1.5rem; right: 5rem; z-index: 999; text-align: right;
             opacity: .8; font-size: 1.05rem; line-height: 1.25; width: 60vw; max-width: 13rem; }
</style>
""", unsafe_allow_html=True)

# --- Options (gear popover, top-right). Read by the next generate. ---
with st.container(key="gearbtn"):
    with st.popover("⚙️"):
        choose_form = st.toggle("Choose body form")
        body_form = st.selectbox("Body Form", FORMS) if choose_form else None

        signature_choice = None
        if not (choose_form and body_form == "Humanoid"):
            if body_form is not None:
                label = f"{SIGNATURE_TOGGLE_LABELS[body_form]} (signature form ability)"
            else:
                label = "Apply signature form ability"
            mode = st.radio(label, ["On", "Off (fully random)", "Percent"], index=0)
            if mode == "On":
                signature_choice = True
            elif mode == "Off (fully random)":
                signature_choice = False
            else:
                signature_choice = st.slider("Chance to apply it (%)", 0, 100, 50) / 100

# --- Generate (spider, top-left corner of the two stacked buttons). ---
with st.container(key="spiderbtn"):
    if st.button("🕷️", help="Conjure a new imp"):
        st.session_state.demon = generate_cacodemon_base(
            RANK, body_form=body_form, signature_choice=signature_choice
        )

# --- Render ---
demon = st.session_state.get("demon")
if not demon:
    st.markdown(
        '<div class="tapnote">Tap the spider to conjure an imp&nbsp;&#8594;</div>',
        unsafe_allow_html=True,
    )
else:
    form, winged = demon["body_form"]
    size = demon.get("size: ", {}).get("category", "")
    secondary = "".join(
        f'<div class="inforow"><span class="lbl">{label}:</span> {value}</div>'
        for label, value in stat_block_rows(demon)
    )
    st.markdown(
        f'<div class="impname">{demon["name"]}</div>'
        f'<div class="impform">Imp · {form}, {"Winged" if winged else "Non-Winged"} · {size}</div>'
        f'<div class="statline">{condensed_stats(demon)}</div>'
        f'{secondary}'
        f'<div class="inforow"><span class="lbl">Abilities:</span> {abilities_oneliner(demon)}</div>',
        unsafe_allow_html=True,
    )

    with st.expander("Abilities detail"):
        st.caption(f"Total: {value_symbols(demon['abilities']['total_cost'])}")
        for ab in demon["abilities"]["abilities"]:
            st.markdown(f"**{ab['name']}** · {value_symbols(ab['cost'])}")
            st.write(ab["description"])
            detail = ab["detail"][0]
            if isinstance(detail, dict):
                for spell in detail.values():
                    st.write(f"- {spell['spell']}: {spell['usage_string']}")
            elif detail and detail != "(":
                st.caption(detail)

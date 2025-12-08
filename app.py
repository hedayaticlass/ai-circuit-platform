# app.py
import streamlit as st
from api_client import analyze_text, transcribe_audio
from drawer import render_schematic

SCHEM_PATH = "schematic.png"

st.set_page_config(page_title="AI Circuit → SPICE → Schematic", layout="wide")
st.title("AI Circuit → SPICE → Schematic")

# --- نوع ورودی ---
mode = st.radio("Input type", ["Text", "Audio"])
user_text = ""

if mode == "Text":
    user_text = st.text_area("Describe the circuit", height=120)
else:
    audio = st.file_uploader("Upload audio", type=["wav", "mp3", "m4a"])
    if audio and st.button("Transcribe"):
        user_text = transcribe_audio(audio.read())
        st.write(user_text)

# --- تولید مدار ---
if st.button("Generate"):
    if not user_text.strip():
        st.warning("Please enter a description of the circuit.")
    else:
        out = analyze_text(user_text)

        # out باید دیکشنری باشد
        if isinstance(out, dict):
            spice = out.get("spice", "")
            components = out.get("components", [])
        else:
            spice = str(out)
            components = []

        st.session_state["spice"] = spice
        st.session_state["components"] = components

# --- نمایش SPICE فقط به صورت متن ---
if "spice" in st.session_state and st.session_state["spice"]:
    st.subheader("SPICE Netlist")
    st.code(st.session_state["spice"], language="text")

# --- نمایش JSON برای دیباگ ---
with st.expander("Components JSON (debug)"):
    if "components" in st.session_state:
        st.json(st.session_state["components"])

# --- رسم شماتیک ---
if "components" in st.session_state and st.session_state["components"]:
    try:
        img_path = render_schematic(st.session_state["components"], save_path=SCHEM_PATH)
        st.subheader("Schematic")
        st.image(img_path, caption="Auto-generated schematic")
    except Exception as e:
        st.error(f"Error in drawing schematic: {e}")

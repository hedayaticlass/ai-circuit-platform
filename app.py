# app.py
import streamlit as st
from api_client import analyze_text, transcribe_audio
from parser import parse_netlist
from drawer import render_schematic
from utils import save_circuit, load_circuit, list_circuits

SCHEM_PATH = "schematic.png"

st.set_page_config(page_title="AI Circuit Builder", layout="wide")
st.title("AI Circuit → SPICE → Schematic")

# Sidebar: Load + Save
with st.sidebar:
    st.header("Circuits")
    circuits = list_circuits()
    csel = st.selectbox("Load circuit", [""] + circuits)
    if csel and st.button("Load"):
        data = load_circuit(csel)
        st.session_state["spice"] = data["spice"]
        st.session_state["components"] = parse_netlist(data["spice"])
        st.success("Loaded.")

    st.divider()
    name = st.text_input("Save name")
    if st.button("Save"):
        if "spice" in st.session_state:
            save_circuit(st.session_state["spice"], name)
            st.success("Saved.")

mode = st.radio("Input type", ["Text", "Audio"])
text = ""

if mode == "Text":
    text = st.text_area("Describe the circuit")
else:
    audio = st.file_uploader("Upload audio", type=["wav","mp3","m4a"])
    if audio and st.button("Transcribe"):
        text = transcribe_audio(audio.read())
        st.write(text)

if st.button("Generate"):
    if not text.strip():
        st.warning("Enter description.")
    else:
        out = analyze_text(text)
        st.session_state["spice"] = out["spice"]
        st.session_state["components"] = out["components"]

# Show SPICE
if "spice" in st.session_state:
    st.subheader("SPICE Netlist")
    st.code(st.session_state["spice"])

# Show schematic
if "components" in st.session_state:
    try:
        img = render_schematic(st.session_state["components"], save_path=SCHEM_PATH)
        st.image(img, caption="Schematic")
    except Exception as e:
        st.error(str(e))

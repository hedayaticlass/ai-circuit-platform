# app.py
import streamlit as st
import pandas as pd
import re
import io
import numpy as np
from dotenv import load_dotenv
from api_client import analyze_text, transcribe_audio
from drawer import render_schematic
from utils import run_ngspice_simulation
from parser import get_netlist_info

load_dotenv()
SCHEM_PATH = "schematic.png"
st.set_page_config(page_title="AI Circuit → SPICE → Schematic", layout="wide")

def clean_base_spice(spice_code):
    """حذف دستورات شبیه‌سازی برای تولید نت‌لیست پایه"""
    if not spice_code: return ""
    lines = spice_code.split('\n')
    clean_lines = []
    skip = False
    for line in lines:
        s = line.strip().lower()
        if s.startswith(".control"): skip = True; continue
        if s.startswith(".endc"): skip = False; continue
        if skip or s.startswith((".tran", ".op", ".dc", ".ac", ".print", ".plot", ".end", ".title")): continue
        if line.strip(): clean_lines.append(line)
    return "\n".join(clean_lines)

def parse_output(raw):
    """پردازش خروجی ngspice و جداسازی داده‌های متنی و گرافیکی"""
    # ۱. پردازش جداول (Transient, DC Sweep, AC Sweep)
    if "Index" in raw:
        try:
            lines = raw.split('\n')
            idx = next(i for i, l in enumerate(lines) if "Index" in l)
            data_lines = [re.sub(r"\s+", ",", l.strip()) for l in lines[idx:] if l.strip() and not l.startswith(("-", "Warning"))]
            df = pd.read_csv(io.StringIO("\n".join(data_lines)))
            # پاکسازی اعداد مختلط در صورت وجود (تحلیل AC)
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].apply(lambda x: float(str(x).split(',')[0]) if ',' in str(x) else x)
            return {"type": "plot", "df": df}
        except: pass

    # ۲. پردازش مقادیر ثابت (DC OP) با حذف نویزهای سیستمی
    pairs = re.findall(r"([a-zA-Z0-9_#\(\)@\[\]]+)[\s]*[=]?[\s]+([+-]?\d+\.?\d*e?[+-]?\d*)", raw)
    FORBIDDEN = ["temp", "tnom", "available", "size", "seconds", "elapsed", "dram", "initialization", "index", 
                 "tc1", "tc2", "tce", "defw", "kf", "af", "bv_max", "lf", "wf", "ef", "ac", "dtemp", "noisy", 
                 "portnum", "zo", "pwr", "phase", "rsh", "narrow", "short", "device", "model", "resistance"]
    
    filtered = []
    seen = set()
    for n, v in pairs:
        name_lower = n.lower().strip()
        is_circuit_var = any([name_lower.startswith('v('), 'branch' in name_lower, name_lower.startswith('@'), re.match(r'^[0-9]+$', name_lower)])
        if is_circuit_var or (not any(fb in name_lower for fb in FORBIDDEN) and len(n) < 10):
            if name_lower not in seen:
                filtered.append([n, v])
                seen.add(name_lower)
    
    if filtered: return {"type": "scalars", "values": filtered}
    return {"type": "text", "content": raw}

# --- ساختار ظاهری مطابق PDF ---
st.title("AI Circuit → SPICE → Schematic")

mode = st.radio("Input type", ["Text", "Audio"])
user_input = ""

if mode == "Text":
    user_input = st.text_area("Describe the circuit", height=120)
else:
    audio = st.file_uploader("Upload audio", type=["wav", "mp3"])
    if audio and st.button("Transcribe"):
        user_input = transcribe_audio(audio.read())

if st.button("Generate"):
    if user_input:
        with st.spinner("AI is designing..."):
            out = analyze_text(user_input)
            st.session_state["raw_spice"] = clean_base_spice(out.get("spice", ""))
            st.session_state["components"] = out.get("components", [])

if "raw_spice" in st.session_state:
    st.subheader("SPICE Netlist")
    st.code(st.session_state["raw_spice"], language="text")

    with st.expander("Components JSON (debug)"):
        st.json(st.session_state["components"])

    if st.session_state["components"]:
        st.subheader("Schematic")
        try:
            img_path = render_schematic(st.session_state["components"], save_path=SCHEM_PATH)
            st.image(img_path, caption="Auto-generated schematic")
        except: pass

if "raw_spice" in st.session_state:
    st.markdown("---")
    st.header("Simulation Console")
    
    nodes, elements = get_netlist_info(st.session_state["raw_spice"])
    sim_type = st.radio("Analysis Type:", ["Transient (Time Domain)", "DC Operating Point", "DC Sweep", "AC Sweep"], horizontal=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Settings:**")
        params = {}
        if "Transient" in sim_type:
            params['step'] = st.text_input("Step", "1ms")
            params['stop'] = st.text_input("Stop", "10ms")
        elif "DC Sweep" in sim_type:
            srcs = [e for e in elements if e.upper().startswith(('V', 'I'))]
            params['src'] = st.selectbox("Source", srcs if srcs else ["V1"])
            params['start'], params['stop'], params['step'] = st.text_input("Start", "0"), st.text_input("Stop", "10"), st.text_input("Step", "1")
        elif "AC Sweep" in sim_type:
            params['pts'], params['fstart'], params['fstop'] = st.text_input("Pts/Dec", "10"), st.text_input("Start", "10"), st.text_input("Stop", "1Meg")

    with col2:
        st.write("**Variables:**")
        sel_nodes = st.multiselect("Voltages (V)", nodes)
        sel_elements = st.multiselect("Currents (I)", elements)

    # ساخت فرمان‌های پرینت برای تحلیل‌های مختلف
    v_cmds = [f"v({n})" for n in sel_nodes]
    i_cmds = [f"i({e})" if e.upper().startswith('V') else f"@{e}[i]" for e in sel_elements]
    
    if "AC Sweep" in sim_type and sel_nodes:
        ac_cmds = []
        for n in sel_nodes: ac_cmds.extend([f"vm({n})", f"vp({n})"])
        print_cmd = "print " + " ".join(ac_cmds)
    else:
        print_cmd = "print " + (" ".join(v_cmds + i_cmds) if (v_cmds or i_cmds) else "all")
    
    ctrl = [".control", "run", print_cmd, ".endc", ".end"]
    analysis = ""
    if "DC Operating Point" in sim_type: analysis = ".op"
    elif "Transient" in sim_type: analysis = f".tran {params.get('step','1m')} {params.get('stop','10m')}"
    elif "DC Sweep" in sim_type: analysis = f".dc {params.get('src','V1')} {params.get('start','0')} {params.get('stop','10')} {params.get('step','1')}"
    elif "AC Sweep" in sim_type: analysis = f".ac dec {params.get('pts','10')} {params.get('fstart','10')} {params.get('fstop','1Meg')}"
    
    final_cir = f"* Final Simulation File\n{st.session_state['raw_spice']}\n{analysis}\n" + "\n".join(ctrl)

    with st.expander("Show Final Netlist"):
        st.code(final_cir, language="spice")

    if st.button("Run Simulation 🚀"):
        with st.spinner("Simulating..."):
            raw_res = run_ngspice_simulation(final_cir)
            res = parse_output(raw_res)
            
            if res["type"] == "scalars":
                st.subheader("Result (DC):")
                st.table(pd.DataFrame(res["values"], columns=["Variable", "Value"]))
            elif res["type"] == "plot":
                st.subheader("Result (Plot):")
                df = res["df"]
                # انتخاب محور افقی بر اساس نوع تحلیل
                x_axis = next((c for c in df.columns if c.lower() in ["time", "frequency", "v-sweep"]), df.columns[1])
                
                if "AC Sweep" in sim_type:
                    mag_cols = [c for c in df.columns if "vm(" in c.lower()]
                    ph_cols = [c for c in df.columns if "vp(" in c.lower()]
                    st.write("### Magnitude (dB)")
                    st.line_chart(df.set_index(x_axis)[mag_cols])
                    st.write("### Phase (Degrees)")
                    st.line_chart(df.set_index(x_axis)[ph_cols])
                else:
                    # رسم نمودار برای Transient و DC Sweep
                    st.line_chart(df.set_index(x_axis).drop(columns=["Index"], errors="ignore"))
            else:
                st.text_area("Full Output Log", raw_res, height=200)
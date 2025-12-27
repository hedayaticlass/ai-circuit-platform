# app.py
import streamlit as st
import pandas as pd
import re
from dotenv import load_dotenv
import os

# ایمپورت ماژول‌های داخلی
from api_client import analyze_text, transcribe_audio
from drawer import render_schematic
from utils import run_ngspice_simulation
from analyzer import parse_ngspice_data, create_matplotlib_plot, create_dc_op_plot

load_dotenv()

SCHEM_PATH = "schematic.png"
st.set_page_config(page_title="AI Circuit Platform", layout="wide", page_icon="⚡")

# ==========================================
# 1. توابع کمکی داخلی
# ==========================================

def extract_spice_nodes(spice_code):
    """استخراج گره‌ها (Nodes) از نت‌لیست برای نمایش در لیست انتخاب"""
    nodes = set()
    if not spice_code: return []
    for line in spice_code.split('\n'):
        line = line.strip()
        if not line or line.startswith(('*', '.')): continue
        parts = line.split()
        if len(parts) < 3: continue
        
        ref = parts[0].lower()
        if ref.startswith(('r', 'c', 'l', 'v', 'i', 'd')):
            nodes.add(parts[1]); nodes.add(parts[2])
        elif ref.startswith('q') and len(parts) >= 4:
            nodes.add(parts[1]); nodes.add(parts[2]); nodes.add(parts[3])
        elif ref.startswith('m') and len(parts) >= 4:
            nodes.add(parts[1]); nodes.add(parts[2]); nodes.add(parts[3])
            
    if '0' in nodes: nodes.remove('0')
    return sorted(list(nodes))

def sanitize_spice_code(spice_code):
    """پاکسازی کد SPICE از توضیحات اضافی مدل زبانی"""
    if not spice_code: return ""
    lines = spice_code.split('\n')
    clean_lines = []
    valid_starts = ('r', 'c', 'l', 'v', 'i', 'd', 'q', 'm', 'x', 'e', 'f', 'g', 'h', 'b', 'k', '.', '*')
    banned_words = ("title", "circuit", "here", "generated", "description", "note", "sure", "certainly")
    skip_block = False

    for line in lines:
        s = line.strip()
        if not s: continue
        s_lower = s.lower()
        
        if s_lower.startswith(".control"): skip_block = True; continue
        if s_lower.startswith(".endc"): skip_block = False; continue
        if skip_block: continue

        if s_lower.startswith(banned_words): s = "* " + s
        elif not s_lower.startswith(valid_starts): s = "* " + s

        if s.startswith("."):
            valid_dots = (".tran", ".op", ".dc", ".ac", ".print", ".plot", ".end", ".model", ".subckt", ".include", ".lib", ".param")
            if not any(s_lower.startswith(cmd) for cmd in valid_dots): s = s[1:]

        # دستورات شبیه‌سازی قدیمی را حذف می‌کنیم تا کاربر جدید تنظیم کند
        if s_lower.startswith((".tran", ".op", ".dc", ".ac", ".print", ".plot", ".end")): continue
        clean_lines.append(s)
    return "\n".join(clean_lines)

def generate_full_netlist(base_spice, sim_type, params, plot_var):
    """تولید نت‌لیست نهایی همراه با دستورات کنترلی"""
    clean_base = sanitize_spice_code(base_spice)
    final_spice = "* AI Circuit Simulation Wrapper\n" + clean_base
    cmds = [".control", "run"]
    an_cmd = ""
    var = plot_var.strip()

    if "Transient" in sim_type:
        uic = " uic" if params.get("uic") else ""
        an_cmd = f".tran {params['step']} {params['stop']}{uic}"
        cmds.append(f"print {var}")
    elif "AC Sweep" in sim_type:
        an_cmd = f".ac dec {params['points']} {params['fstart']} {params['fstop']}"
        if var.lower().startswith("v(") and ")" in var:
            node = var[2:-1]
            cmds.append(f"print vdb({node})")
        else:
            cmds.append(f"print {var}")
    elif "DC Sweep" in sim_type:
        an_cmd = f".dc {params['source']} {params['start']} {params['stop']} {params.get('step','0.1')}"
        cmds.append(f"print {var}")
    elif "Operating Point" in sim_type:
        an_cmd = ".op"
        cmds.append("print all")

    cmds.extend([".endc", ".end"])
    return f"{final_spice}\n{an_cmd}\n" + "\n".join(cmds)

# ==========================================
# 2. UI Main
# ==========================================
st.title("AI Circuit Platform ⚡")

with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        mode = st.radio("Input Mode", ["Text Description", "Voice Command"], horizontal=True)
        user_text = ""
        if mode == "Text Description":
            user_text = st.text_area("Circuit Description:", placeholder="Example: A Low pass filter with R=1k and C=1uF...", height=100)
        else:
            audio = st.file_uploader("Audio", type=["wav", "mp3"])
            if audio and st.button("Transcribe"):
                # user_text = transcribe_audio(audio.read()) # نیاز به کلید Whisper
                st.info("Voice transcription placeholder.")
                user_text = "RC Circuit"

    with c2:
        st.write("")
        st.write("")
        if st.button("Generate Circuit 🛠️", type="primary", use_container_width=True):
            if user_text:
                with st.spinner("AI is designing your circuit..."):
                    out = analyze_text(user_text)
                    if isinstance(out, dict):
                        st.session_state["spice"] = out.get("spice", "")
                        st.session_state["components"] = out.get("components", [])
                        st.session_state["sim_results"] = None
                        st.session_state["sim_log"] = None
                    else:
                        st.session_state["spice"] = str(out)
                        st.session_state["components"] = []

if "spice" in st.session_state and st.session_state["spice"]:
    st.markdown("---")
    c_schem, c_code = st.columns(2)
    with c_code:
        st.subheader("Base Netlist")
        st.code(st.session_state["spice"], language="spice")
    with c_schem:
        st.subheader("Schematic")
        if st.session_state.get("components"):
            try:
                img_path = render_schematic(st.session_state["components"], SCHEM_PATH)
                st.image(img_path)
            except Exception as e:
                st.error(f"Schematic Error: {e}")

# ==========================================
# 3. Simulation Console & Editor
# ==========================================
if "spice" in st.session_state and st.session_state["spice"]:
    st.markdown("---")
    st.header("📈 Simulation Console")
    
    detected_nodes = extract_spice_nodes(st.session_state["spice"])
    plot_options = [f"v({n})" for n in detected_nodes]
    
    # اضافه کردن جریان منابع ولتاژ به لیست پلات
    for line in st.session_state["spice"].split('\n'):
        if line.lower().strip().startswith('v'):
            parts = line.split()
            if len(parts) > 0: plot_options.append(f"i({parts[0]})")

    default_idx = 0
    for i, opt in enumerate(plot_options):
        if any(x in opt.lower() for x in ["out", "load", "vo"]):
            default_idx = i; break
            
    with st.container(border=True):
        sim_type = st.selectbox("Analysis Type", 
                                ["Transient (Time)", "AC Sweep (Frequency)", "DC Sweep", "DC Operating Point"])
        
        params = {}
        cp1, cp2, cp3 = st.columns(3)
        
        if plot_options:
            plot_var = st.selectbox("Signal to Plot", plot_options, index=default_idx)
        else:
            plot_var = st.text_input("Signal to Plot", "v(out)")

        if "Transient" in sim_type:
            with cp1: params["step"] = st.text_input("Step", "1ms")
            with cp2: params["stop"] = st.text_input("Stop", "100ms")
            with cp3: params["uic"] = st.checkbox("UIC", False)
        elif "AC Sweep" in sim_type:
            with cp1: params["points"] = st.text_input("Points/Dec", "10")
            with cp2: params["fstart"] = st.text_input("Start Freq", "1Hz")
            with cp3: params["fstop"] = st.text_input("Stop Freq", "1MHz")
        elif "DC Sweep" in sim_type:
            with cp1: params["source"] = st.text_input("Source Name", "V1")
            with cp2: params["start"] = st.text_input("Start", "0")
            with cp3: params["stop"] = st.text_input("Stop", "5"); params["step"] = st.text_input("Step", "0.1")
        elif "Operating Point" in sim_type:
            plot_var = "all"
            # نمایش انتخاب متغیرها برای DC OP (اگر قبلاً شبیه‌سازی شده)
            if st.session_state.get("dc_op_available_vars"):
                available_vars = st.session_state["dc_op_available_vars"]
                voltage_vars = [v for v in available_vars if re.match(r"^v\([0-9]+\)$", v.lower())]
                current_vars = [v for v in available_vars if "#branch" in v.lower()]
                
                col_v, col_i = st.columns(2)
                with col_v:
                    if voltage_vars:
                        selected_voltages = st.multiselect(
                            "Select Voltages to Plot:",
                            voltage_vars,
                            default=st.session_state.get("dc_op_selected_voltages", voltage_vars),
                            key="dc_op_voltages_select"
                        )
                        st.session_state["dc_op_selected_voltages"] = selected_voltages
                with col_i:
                    if current_vars:
                        selected_currents = st.multiselect(
                            "Select Currents to Plot:",
                            current_vars,
                            default=st.session_state.get("dc_op_selected_currents", current_vars),
                            key="dc_op_currents_select"
                        )
                        st.session_state["dc_op_selected_currents"] = selected_currents

    st.subheader("📝 Netlist Editor (Editable)")
    default_code = generate_full_netlist(st.session_state["spice"], sim_type, params, plot_var)
    final_netlist_input = st.text_area("Review netlist before running:", value=default_code, height=250)

    if st.button("Run Simulation 🚀", use_container_width=True):
        with st.spinner("Running Ngspice..."):
            res = run_ngspice_simulation(final_netlist_input)
            data = parse_ngspice_data(res)
            
            st.session_state["sim_results"] = data
            st.session_state["sim_log"] = res

    # نمایش نتایج
    if st.session_state.get("sim_results"):
        data = st.session_state["sim_results"]
        log = st.session_state["sim_log"]

        if data.get("error"):
            st.error("Simulation Error")
            st.error(data["error"])
        
        elif data.get("type") == "scalars":
            st.success("DC Results")
            if data.get("values"):
                # فیلتر کردن فقط v(عدد) و #branch
                filtered_values = []
                for var_name, var_value in data["values"]:
                    var_lower = var_name.lower()
                    if "#branch" in var_lower or re.match(r"^v\([0-9]+\)$", var_lower):
                        filtered_values.append([var_name, var_value])
                
                if filtered_values:
                    df_op = pd.DataFrame(filtered_values, columns=["Parameter", "Value"])
                    st.dataframe(df_op, use_container_width=True, hide_index=True)
                else:
                    st.info("💡 No v(number) or #branch variables found in results.")
                
                # استخراج متغیرهای v(عدد) و #branch و ذخیره در session state
                available_vars = []
                for var_name, _ in data["values"]:
                    var_lower = var_name.lower()
                    # فقط v(عدد) و #branch
                    if "#branch" in var_lower or re.match(r"^v\([0-9]+\)$", var_lower):
                        available_vars.append(var_name)
                
                # ذخیره متغیرهای موجود برای استفاده در Simulation Console
                st.session_state["dc_op_available_vars"] = available_vars
                
                # استفاده از انتخاب کاربر از Simulation Console
                selected_voltages = st.session_state.get("dc_op_selected_voltages", [])
                selected_currents = st.session_state.get("dc_op_selected_currents", [])
                selected_vars = selected_voltages + selected_currents
                
                # اگر هیچ انتخابی نبود، همه را انتخاب کن
                if not selected_vars and available_vars:
                    voltage_vars = [v for v in available_vars if re.match(r"^v\([0-9]+\)$", v.lower())]
                    current_vars = [v for v in available_vars if "#branch" in v.lower()]
                    selected_vars = voltage_vars + current_vars
                    st.session_state["dc_op_selected_voltages"] = voltage_vars
                    st.session_state["dc_op_selected_currents"] = current_vars
                
                # رسم نمودار برای ولتاژ و جریان
                if selected_vars:
                    with st.expander("⚙️ Chart Settings"):
                        c_w, c_h = st.columns(2)
                        p_width = c_w.slider("Width", 4, 25, 14, key="dc_op_width")
                        p_height = c_h.slider("Height", 3, 20, 6, key="dc_op_height")
                    
                    p_width = st.session_state.get("dc_op_width", 14)
                    p_height = st.session_state.get("dc_op_height", 6)
                    
                    # فیلتر کردن values بر اساس انتخاب کاربر
                    filtered_values = [(var, val) for var, val in data["values"] if var in selected_vars]
                    
                    if filtered_values:
                        fig = create_dc_op_plot(filtered_values, figsize=(p_width, p_height))
                        st.pyplot(fig, use_container_width=False)
                    else:
                        st.warning("⚠️ No valid variables selected for plotting.")
                else:
                    st.info("💡 No v(number) or #branch variables found in results.")

        elif data.get("type") == "plot":
            st.success(f"Results: {data.get('analysis', '').upper()}")
            
            # تنظیمات نمودار - slider با key خودش session state را مدیریت می‌کند
            with st.expander("⚙️ Chart Settings"):
                c_w, c_h = st.columns(2)
                p_width = c_w.slider("Width", 4, 25, 10, key="plot_width")
                p_height = c_h.slider("Height", 3, 20, 6, key="plot_height")
            
            # استفاده از session state (که توسط slider با key تنظیم شده) یا مقادیر پیش‌فرض
            p_width = st.session_state.get("plot_width", 10)
            p_height = st.session_state.get("plot_height", 6)
            
            fig = create_matplotlib_plot(data["df"], data.get("analysis"), figsize=(p_width, p_height))
            st.pyplot(fig, use_container_width=False)

        st.markdown("---")
        with st.expander("📜 View Raw Log"):
            st.text_area("Ngspice Output:", value=log, height=300)
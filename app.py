# app.py
import streamlit as st
import pandas as pd
import re
import io
import numpy as np
import altair as alt
import platform
import os
from dotenv import load_dotenv
from api_client import analyze_text, transcribe_audio
from drawer import render_schematic
from utils import run_ngspice_simulation, run_ngspice_with_plot
from parser import get_netlist_info

load_dotenv()
SCHEM_PATH = "schematic.png"
st.set_page_config(page_title="AI Circuit → SPICE → Schematic", layout="wide")

def clean_base_spice(spice_code):
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
    """
    فیلتر نهایی برای حذف تمام داده‌های سیستمی و نگه داشتن فقط متغیرهای مدار.
    """
    # ۱. شناسایی جداول (Transient/Sweep)
    if "Index" in raw:
        try:
            lines = raw.split('\n')
            idx = next(i for i, l in enumerate(lines) if "Index" in l)
            data_lines = [re.sub(r"\s+", ",", l.strip()) for l in lines[idx:] if l.strip() and not l.startswith(("-", "Warning", "Circuit"))]
            df = pd.read_csv(io.StringIO("\n".join(data_lines)))
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].apply(lambda x: float(str(x).split(',')[0]) if ',' in str(x) else x)
            return {"type": "plot", "df": df}
        except: pass

    # ۲. استخراج مقادیر ثابت (DC OP)
    pairs = re.findall(r"([a-zA-Z0-9_#\(\)@\[\]]+)[\s]*[=]?[\s]+([+-]?\d+\.?\d*e?[+-]?\d*)", raw)
    if not pairs:
        pairs = re.findall(r"^[\s]*([a-zA-Z0-9_#\(\)]+)[\s]+([+-]?\d+\.?\d*e?[+-]?\d*)", raw, re.MULTILINE)

    FORBIDDEN = ["temp", "tnom", "available", "size", "seconds", "elapsed", "dram", "initialization", "index", 
                 "tc1", "tc2", "tce", "defw", "kf", "af", "bv_max", "lf", "wf", "ef", "ac", "dtemp", "noisy", 
                 "portnum", "zo", "pwr", "phase", "rsh", "narrow", "short", "device", "model", "resistance", 
                 "sparse", "dec", "r", "i", "p", "dc", "acmag", "freq", "z0"]
    
    filtered = []
    seen = set()
    for n, v in pairs:
        name_lower = n.lower().strip()
        is_node = name_lower.startswith('v(') or re.match(r'^[0-9]+$', name_lower) or name_lower in ["in", "out"]
        is_curr = 'branch' in name_lower or (name_lower.startswith('@') and '[i]' in name_lower)
        
        if (is_node or is_curr) and name_lower not in FORBIDDEN:
            if name_lower not in seen:
                display_name = n
                if (re.match(r'^[0-9]+$', name_lower) or name_lower in ["in", "out"]) and not is_curr:
                    display_name = f"V({n})"
                
                filtered.append([display_name, v])
                seen.add(name_lower)
    
    if filtered: return {"type": "scalars", "values": filtered}
    return {"type": "text", "content": raw}

# --- رابط کاربری ---
st.title("AI Circuit → SPICE → Schematic")

mode = st.radio("Input type", ["Text", "Audio"]) 
user_input = ""

if mode == "Text":
    user_input = st.text_area("Describe the circuit", height=120) 
else:
    audio = st.file_uploader("Upload audio", type=["wav", "mp3"])
    if audio and st.button("Transcribe", key="audio_btn"):
        user_input = transcribe_audio(audio.read())

if st.button("Generate", key="gen_btn"):
    if user_input:
        with st.spinner("Processing..."):
            out = analyze_text(user_input)
            st.session_state["raw_spice"] = clean_base_spice(out.get("spice", ""))
            st.session_state["components"] = out.get("components", [])

if "raw_spice" in st.session_state:
    st.subheader("SPICE Netlist") 
    st.code(st.session_state["raw_spice"], language="text")

    if st.session_state["components"]:
        st.subheader("Schematic") 
        try:
            img_path = render_schematic(st.session_state["components"], save_path=SCHEM_PATH)
            st.image(img_path, caption="Auto-generated schematic") 
        except: pass

# --- کنسول شبیه‌سازی ---
if "raw_spice" in st.session_state:
    st.markdown("---")
    st.header("Simulation Console") 
    
    nodes, elements = get_netlist_info(st.session_state["raw_spice"])
    sim_type = st.radio("Analysis Type:", ["Transient (Time Domain)", "DC Operating Point", "DC Sweep", "AC Sweep"], horizontal=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Settings:**")
        params = {}
        if "Transient" in sim_type:
            params['step'] = st.text_input("Step", "1ms", key="s_step")
            params['stop'] = st.text_input("Stop", "10ms", key="s_stop")
        elif "DC Sweep" in sim_type:
            srcs = [e for e in elements if e.upper().startswith(('V', 'I'))]
            params['src'] = st.selectbox("Source", srcs if srcs else ["V1"], key="s_src")
            params['start'], params['stop'], params['step'] = st.text_input("Start", "0", key="s_st"), st.text_input("Stop", "10", key="s_sp"), st.text_input("Step", "1", key="s_stp")
        elif "AC Sweep" in sim_type:
            params['pts'], params['fstart'], params['fstop'] = st.text_input("Pts/Dec", "10", key="s_p"), st.text_input("Start", "10", key="s_f1"), st.text_input("Stop", "1Meg", key="s_f2")

    with col2:
        st.write("**Variables (Text):**") 
        sel_nodes = st.multiselect("Voltages (V)", nodes, key="txt_v")
        sel_elements = st.multiselect("Currents (I)", elements, key="txt_i") 

    with col3:
        st.write("**Plotting (Graph):**") 
        plot_nodes = st.multiselect("Plot Voltages", nodes, key="plt_v") 
        plot_elements = st.multiselect("Plot Currents", elements, key="plt_i") 

    # ساخت نت‌لیست نهایی
    v_total = list(set(sel_nodes + plot_nodes))
    i_total = list(set(sel_elements + plot_elements))
    v_cmds = [f"v({n})" for n in v_total]
    i_cmds = [f"i({e})" if e.upper().startswith('V') else f"@{e}[i]" for e in i_total]
    
    is_linux = platform.system() != "Windows"
    needs_plot = bool(plot_nodes or plot_elements) and "DC Operating Point" not in sim_type
    
    # ساخت لیست متغیرها برای رسم یا چاپ
    targets = " ".join(v_cmds + i_cmds) if (v_cmds or i_cmds) else "all"
    print_cmd = ""
    
    # تغییر مهم: در لینوکس اگر پلات لازم باشد، دستور چاپ یا پلات را اینجا اضافه نمی‌کنیم
    # بلکه آن را به بخش .control در utils.py می‌سپاریم.
    if "DC Operating Point" in sim_type:
        print_cmd = f".print op {targets}"
    elif "Transient" in sim_type:
        if not (is_linux and needs_plot):
            print_cmd = f".print tran {targets}"
    elif "DC Sweep" in sim_type:
        if not (is_linux and needs_plot):
            print_cmd = f".print dc {targets}"
    elif "AC Sweep" in sim_type:
        if not (is_linux and needs_plot):
            print_cmd = f".print ac {targets}"
    
    analysis = ""
    if "DC Operating Point" in sim_type: analysis = ".op"
    elif "Transient" in sim_type: analysis = f".tran {params.get('step','1m')} {params.get('stop','10m')}"
    elif "DC Sweep" in sim_type: analysis = f".dc {params.get('src','V1')} {params.get('start','0')} {params.get('stop','10')} {params.get('step','1')}"
    elif "AC Sweep" in sim_type: analysis = f".ac dec {params.get('pts','10')} {params.get('fstart','10')} {params.get('fstop','1Meg')}"
    
    final_lines = [
        "* Final Simulation File",
        st.session_state["raw_spice"],
        analysis,
    ]
    if print_cmd:
        final_lines.append(print_cmd)
        
    final_lines.append(".end")
    final_cir = "\n".join([ln for ln in final_lines if ln.strip()])

    with st.expander("Show Final Netlist"): 
        if "edited_netlist" not in st.session_state or st.session_state.get("last_final_cir") != final_cir:
            st.session_state["edited_netlist"] = final_cir
            st.session_state["last_final_cir"] = final_cir
            st.session_state["edit_netlist"] = final_cir
        
        edited_netlist = st.text_area(
            "Edit Netlist (optional)",
            value=st.session_state["edited_netlist"],
            height=300,
            key="edit_netlist",
        )
        st.session_state["edited_netlist"] = st.session_state.get("edit_netlist", edited_netlist)
    
    def sanitize_netlist(text: str) -> str:
        lines = []
        for ln in text.splitlines():
            if ln.strip().lower() == ".circuits":
                continue 
            lines.append(ln)
        cleaned = "\n".join(lines)
        if not cleaned.endswith("\n"):
            cleaned += "\n"
        return cleaned

    netlist_to_run = sanitize_netlist(st.session_state.get("edited_netlist", final_cir))

    if st.button("Run Simulation 🚀", key="run_sim_btn"):
        with st.spinner("Simulating..."):
            plot_image_path = None
            
            # لاجیک جدید برای لینوکس
            if is_linux and needs_plot:
                plot_output_path = "ngspice_plot.png"
                if os.path.exists(plot_output_path):
                    os.remove(plot_output_path)
                
                # فراخوانی تابع اصلاح شده در utils با ارسال متغیرهای رسم
                raw_res, plot_image_path = run_ngspice_with_plot(
                    netlist_to_run, 
                    plot_output_path, 
                    variables_to_plot=targets
                )
            else:
                raw_res = run_ngspice_simulation(netlist_to_run)
            
            res = parse_output(raw_res)
            
            # نمایش تصویر نمودار تولید شده توسط Ngspice
            plot_shown = False
            if plot_image_path and os.path.exists(plot_image_path):
                st.subheader("Result (Diagram):")
                st.image(plot_image_path, caption="Ngspice Plot", use_container_width=True)
                plot_shown = True
            
            # نمایش مقادیر عددی (Scalars)
            if res["type"] == "scalars":
                st.subheader("Result (DC):")
                user_selected = bool(sel_nodes or sel_elements or plot_nodes or plot_elements)
                values = res["values"]
                if user_selected:
                    wanted_names = set()
                    all_nodes = list(set(sel_nodes + plot_nodes))
                    all_elems = list(set(sel_elements + plot_elements))
                    for n in all_nodes:
                        n_l = n.lower()
                        wanted_names.update({f"v({n_l})", f"v({n})", f"V({n})"})
                    for e in all_elems:
                        e_l = e.lower()
                        wanted_names.update({f"i({e_l})", f"i({e})", f"I({e})", f"@{e}[i]", f"@{e_l}[i]"})
                    
                    wanted_lower = {w.lower() for w in wanted_names}
                    values = [row for row in res["values"] if row[0].lower() in wanted_lower]

                st.table(pd.DataFrame(values, columns=["Variable", "Value"]))

                if values:
                    try:
                        plot_vars = {v[0]: float(v[1]) for v in values}
                        df_plot = pd.DataFrame({"Variable": list(plot_vars.keys()), "Value": list(plot_vars.values())})
                        chart = alt.Chart(df_plot).mark_bar().encode(
                            x=alt.X("Value:Q", title="Value"),
                            y=alt.Y("Variable:N", sort=None, title="Variable"),
                        )
                        st.altair_chart(chart, use_container_width=True)
                    except: pass
            
            # نمایش نمودار تعاملی (اگر توسط ngspice عکس تولید نشده باشد)
            elif res["type"] == "plot":
                if not plot_shown:
                    st.subheader("Result (Diagram):")
                    df = res["df"]
                    x_axis = next((c for c in df.columns if c.lower() in ["time", "frequency", "v-sweep"]), df.columns[1])
                    
                    plot_cols = []
                    for col in df.columns:
                        col_l = col.lower()
                        if col == x_axis or col_l == "index": continue
                        matched = False
                        for n in plot_nodes:
                            n_l = n.lower()
                            if col_l == n_l or col_l == f"v({n_l})" or f"({n_l})" in col_l: matched = True; break
                        if not matched:
                            for e in plot_elements:
                                e_l = e.lower()
                                if e_l in col_l and ("[i]" in col_l or "i(" in col_l): matched = True; break
                        if matched: plot_cols.append(col)

                    if plot_cols:
                        st.line_chart(df.set_index(x_axis)[plot_cols])
                    else:
                        st.line_chart(df.set_index(x_axis).drop(columns=["Index"], errors="ignore"))
            else:
                st.text_area("Console Log", raw_res, height=200)
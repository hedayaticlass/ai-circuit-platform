# app.py
import streamlit as st
import pandas as pd
import re
import io
from dotenv import load_dotenv
from api_client import analyze_text, transcribe_audio
from drawer import render_schematic
from utils import run_ngspice_simulation

# بارگذاری تنظیمات
load_dotenv()

SCHEM_PATH = "schematic.png"
st.set_page_config(page_title="AI Circuit → SPICE → Schematic", layout="wide")

# ==========================================
# 1. توابع کمکی (بدون تغییر در ظاهر سایت)
# ==========================================

def remove_simulation_commands(spice_code):
    """دستورات تحلیل قدیمی را حذف می‌کند تا دستور جدید کاربر جایگزین شود."""
    if not spice_code: return ""
    lines = spice_code.split('\n')
    clean_lines = []
    skip_block = False
    for line in lines:
        s = line.strip().lower()
        if s.startswith(".control"): skip_block = True; continue
        if s.startswith(".endc"): skip_block = False; continue
        if skip_block: continue
        if s.startswith((".tran", ".op", ".dc", ".ac", ".print", ".plot", ".end")): continue
        clean_lines.append(line)
    return "\n".join(clean_lines)

def parse_ngspice_output(raw_output):
    """خروجی را تمیز کرده و متغیرهای اضافی سیستم را حذف می‌کند."""
    data = {"type": "text", "content": raw_output}
    IGNORE_LIST = ["TEMP", "TNOM", "size", "available", "seconds", "elapsed", "DRAM", "Initialization"]

    # استخراج اعداد (DC/OP)
    scalar_pattern = re.findall(r"(\w+\(?\w*\)?)\s*=\s*([+-]?\d+\.?\d*e?[+-]?\d*)", raw_output)
    if scalar_pattern:
        filtered = [(n, v) for n, v in scalar_pattern if not any(ig.lower() in n.lower() for ig in IGNORE_LIST)]
        if filtered:
            data["type"] = "scalars"
            data["values"] = filtered
            return data

    # استخراج نمودار (Transient/AC)
    if "Index" in raw_output and ("time" in raw_output or "frequency" in raw_output or "v-sweep" in raw_output):
        try:
            lines = raw_output.split('\n')
            start_idx = next(i for i, line in enumerate(lines) if "Index" in line)
            table_lines = [re.sub(r"\s+", ",", l.strip()) for l in lines[start_idx:] if l.strip() and not l.startswith(("---", "Warning"))]
            df = pd.read_csv(io.StringIO("\n".join(table_lines)))
            data["type"] = "plot"
            data["df"] = df
            return data
        except: pass
    return data

# ==========================================
# 2. رابط کاربری (دقیقاً با معماری قبلی)
# ==========================================

st.title("AI Circuit → SPICE → Schematic")

# --- بخش ورودی (مثل قبل) ---
mode = st.radio("Input type", ["Text", "Audio"])
user_text = ""

if mode == "Text":
    user_text = st.text_area("Describe the circuit", height=120)
else:
    audio = st.file_uploader("Upload audio", type=["wav", "mp3", "m4a"])
    if audio and st.button("Transcribe"):
        user_text = transcribe_audio(audio.read())
        st.write(user_text)

# --- دکمه تولید (مثل قبل) ---
if st.button("Generate"):
    if not user_text.strip():
        st.warning("Please enter a description.")
    else:
        out = analyze_text(user_text)
        if isinstance(out, dict):
            st.session_state["spice"] = out.get("spice", "")
            st.session_state["components"] = out.get("components", [])
        else:
            st.session_state["spice"] = str(out)
            st.session_state["components"] = []

# --- نمایش خروجی‌ها (به ترتیب زیر هم) ---
if "spice" in st.session_state and st.session_state["spice"]:
    st.subheader("SPICE Netlist")
    st.code(st.session_state["spice"], language="text")

    with st.expander("Components JSON (debug)"):
        if "components" in st.session_state:
            st.json(st.session_state["components"])

if "components" in st.session_state and st.session_state["components"]:
    try:
        img_path = render_schematic(st.session_state["components"], save_path=SCHEM_PATH)
        st.subheader("Schematic")
        st.image(img_path, caption="Auto-generated schematic")
    except Exception as e:
        st.error(f"Error in drawing schematic: {e}")

# ==========================================
# 3. کنسول شبیه‌سازی (پایین صفحه)
# ==========================================
if "spice" in st.session_state and st.session_state["spice"]:
    st.markdown("---")
    st.header("🛠 Simulation Console")
    
    # تنظیمات تحلیل
    with st.container():
        sim_type = st.radio("Analysis Type:", ["Transient (Time Domain)", "DC Operating Point", "DC Sweep", "AC Sweep"], horizontal=True)
        
        params = {}
        c1, c2, c3 = st.columns(3)
        
        if "Transient" in sim_type:
            with c1: params["step"] = st.text_input("Time Step", "1ms")
            with c2: params["stop"] = st.text_input("Stop Time", "100ms")
            with c3: params["uic"] = st.checkbox("Use Initial Conditions", False)
        elif "DC Sweep" in sim_type:
            with c1: params["source"] = st.text_input("Source", "V1")
            with c2: params["start"] = st.text_input("Start", "0")
            with c3: params["stop"] = st.text_input("Stop", "10"); params["step"] = st.text_input("Step", "1")
        elif "AC Sweep" in sim_type:
            with c1: params["points"] = st.text_input("Points", "10")
            with c2: params["fstart"] = st.text_input("Start Freq", "1Hz")
            with c3: params["fstop"] = st.text_input("Stop Freq", "1MHz")

        plot_var = st.text_input("Plot Variable", "V(out)")

    # دکمه اجرای نهایی (با اصلاحات فنی مخفی)
    if st.button("Run Simulation 🚀"):
        with st.spinner("Running..."):
            # 1. تمیزکاری کد
            base_spice = remove_simulation_commands(st.session_state["spice"])
            
            # 2. حل مشکل خط اول (Title Fix)
            if not base_spice.strip().startswith("*"):
                base_spice = "* AI Simulation\n" + base_spice

            # 3. ساخت دستورات
            analysis_cmd = ""
            control_cmds = [".control", "run"]
            
            if "Transient" in sim_type:
                uic = " uic" if params.get("uic") else ""
                analysis_cmd = f".tran {params['step']} {params['stop']}{uic}"
                control_cmds.append(f"print {plot_var}")
            elif "Operating Point" in sim_type:
                analysis_cmd = ".op"
                control_cmds.append("print all")
            elif "DC Sweep" in sim_type:
                analysis_cmd = f".dc {params['source']} {params['start']} {params['stop']} {params.get('step','1')}"
                control_cmds.append(f"print {plot_var}")
            elif "AC Sweep" in sim_type:
                analysis_cmd = f".ac dec {params['points']} {params['fstart']} {params['fstop']}"
                control_cmds.append(f"print {plot_var}")

            control_cmds.append(".endc")
            control_cmds.append(".end")
            
            # ترکیب نهایی
            final_netlist = f"{base_spice}\n{analysis_cmd}\n" + "\n".join(control_cmds)
            
            # نمایش کد نهایی برای دیباگ
            with st.expander("Show Final Netlist"):
                st.code(final_netlist, language="spice")

            # اجرا
            res = run_ngspice_simulation(final_netlist)
            parsed = parse_ngspice_output(res)

            # نمایش نتیجه
            if parsed["type"] == "scalars":
                st.success("Result (DC):")
                cols = st.columns(4)
                for i, (k, v) in enumerate(parsed["values"]):
                    cols[i%4].metric(k, v)
            elif parsed["type"] == "plot":
                st.success("Result (Plot):")
                df = parsed["df"]
                # تنظیم محور X
                x_col = next((c for c in df.columns if c.lower() in ["time", "frequency", "v-sweep"]), None)
                if x_col:
                    st.line_chart(df.set_index(x_col).drop(columns=["Index"], errors="ignore"))
                else:
                    st.dataframe(df)
            else:
                if "Error" in res: st.error("Simulation Failed")
                st.text_area("Log", res, height=200)
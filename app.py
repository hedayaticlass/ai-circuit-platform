# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from api_client import analyze_text, transcribe_audio
from drawer import render_schematic
from utils import run_ngspice_simulation

try:
    from analyzer import parse_ngspice_data, create_matplotlib_plot
except ImportError:
    st.error("فایل analyzer.py یافت نشد.")
    st.stop()

load_dotenv()
SCHEM_PATH = "schematic.png"
st.set_page_config(page_title="AI Circuit Platform", layout="wide", page_icon="⚡")

# ================= توابع کمکی =================
def extract_spice_nodes(spice_code):
    nodes = set()
    if not spice_code: return []
    for line in spice_code.split('\n'):
        parts = line.strip().split()
        if len(parts) < 3 or line.startswith(('*', '.')): continue
        if parts[0].lower().startswith(('r','c','l','v','i','d')):
            nodes.update(parts[1:3])
        elif parts[0].lower().startswith(('q','m')) and len(parts)>=4:
            nodes.update(parts[1:4])
    if '0' in nodes: nodes.remove('0')
    return sorted(list(nodes))

def sanitize_spice_code(spice_code):
    if not spice_code: return ""
    lines = spice_code.split('\n')
    clean_lines = []
    banned = ("title", "circuit", "here", "generated", "description", "note")
    valid_starts = ('r','c','l','v','i','d','q','m','x','e','f','g','h','b','k','.','*')
    
    skip = False
    for line in lines:
        s = line.strip()
        if not s: continue
        sl = s.lower()
        if sl.startswith(".control"): skip=True; continue
        if sl.startswith(".endc"): skip=False; continue
        if skip: continue
        
        if sl.startswith(banned): s = "* " + s
        elif not sl.startswith(valid_starts): s = "* " + s
        
        if s.startswith(".") and not any(sl.startswith(c) for c in [".tran",".op",".dc",".ac",".end",".model",".subckt",".include",".lib",".param",".print",".plot"]):
            s = s[1:]
            
        if sl.startswith((".tran", ".op", ".dc", ".ac", ".print", ".plot", ".end")): continue
        clean_lines.append(s)
    return "\n".join(clean_lines)

def generate_full_netlist(base, sim_type, params, plot_var):
    clean = sanitize_spice_code(base)
    final = "* AI Sim\n" + clean
    cmds = [".control", "run"]
    an_cmd = ""
    var = plot_var.strip()
    
    if "Transient" in sim_type:
        uic = " uic" if params.get("uic") else ""
        an_cmd = f".tran {params['step']} {params['stop']}{uic}"
        cmds.append(f"print {var}")

    elif "AC Sweep" in sim_type:
        an_cmd = f".ac dec {params['points']} {params['fstart']} {params['fstop']}"
        
        # --- FIX: فقط ولتاژ (vdb) را نگه دار و جریان را حذف کن ---
        if var.lower().startswith("v(") and ")" in var:
            # اگر ولتاژ بود، vdb چاپ کن
            cmds.append(f"print vdb({var[2:-1]})")
        elif var.lower().startswith("i(") or "#" in var:
            # اگر جریان بود، نادیده بگیر یا به کاربر هشدار بده (در اینجا کد اصلاح می‌شود)
            # اما چون باید چیزی چاپ شود تا نمودار خالی نباشد، پیش‌فرض vdb(out) را می‌زنیم اگر ولتاژ نبود
            cmds.append(f"print vdb(out)") 
        else:
            # اگر متغیر نامشخص بود، فرض می‌کنیم ولتاژ گره است
            cmds.append(f"print vdb({var})")

    elif "DC Sweep" in sim_type:
        an_cmd = f".dc {params['source']} {params['start']} {params['stop']} {params.get('step','0.1')}"
        cmds.append(f"print {var}")

    elif "Operating Point" in sim_type:
        an_cmd = ".op"
        cmds.append("print all") 

    cmds.extend([".endc", ".end"])
    return f"{final}\n{an_cmd}\n" + "\n".join(cmds)

# ================= رابط کاربری =================
st.title("AI Circuit Platform ⚡")

with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        mode = st.radio("Input Mode", ["Text Description", "Voice Command"], horizontal=True)
        user_text = ""
        if mode == "Text Description":
            user_text = st.text_area("Description:", placeholder="RC Low pass filter...", height=100)
        else:
            audio = st.file_uploader("Audio", type=["wav", "mp3"])
            if audio and st.button("Transcribe"):
                user_text = transcribe_audio(audio.read()); st.write(user_text)
    with c2:
        st.write(""); st.write("")
        if st.button("Generate Circuit 🛠️", type="primary", use_container_width=True):
            if user_text:
                with st.spinner("Engineering..."):
                    out = analyze_text(user_text)
                    if isinstance(out, dict):
                        st.session_state.update({"spice": out.get("spice",""), "components": out.get("components",[]), "sim_results": None, "sim_log": None})
                    else:
                        st.session_state.update({"spice": str(out), "components": [], "sim_results": None, "sim_log": None})

if st.session_state.get("spice"):
    st.markdown("---")
    c_sch, c_code = st.columns(2)
    with c_code: st.subheader("Netlist"); st.code(st.session_state["spice"])
    with c_sch:
        st.subheader("Schematic")
        if st.session_state.get("components"):
            try: st.image(render_schematic(st.session_state["components"], SCHEM_PATH))
            except: st.error("Schematic Error")

if st.session_state.get("spice"):
    st.markdown("---"); st.header("📈 Simulation Console")
    
    nodes = extract_spice_nodes(st.session_state["spice"])
    
    # --- فیلتر کردن لیست برای AC ---
    # اگر AC انتخاب شده باشد، فقط ولتاژها را در لیست نشان می‌دهیم
    # اما چون نوع تحلیل هنوز انتخاب نشده (در خط بعد انتخاب می‌شود)،
    # ما اینجا همه را می‌سازیم و پایین‌تر فیلتر می‌کنیم.
    
    plot_ops = [f"v({n})" for n in nodes]
    for l in st.session_state["spice"].split('\n'):
        if l.lower().strip().startswith('v'):
            p = l.split()
            if len(p)>0: plot_ops.append(f"i({p[0]})")
    
    def_idx = 0
    for i, o in enumerate(plot_ops):
        if any(x in o.lower() for x in ["out","load"]): def_idx=i; break

    with st.container(border=True):
        sim_type = st.selectbox("Analysis Type", ["Transient (Time)", "AC Sweep (Frequency)", "DC Sweep", "DC Operating Point"])
        params = {}
        c1, c2, c3 = st.columns(3)
        
        # --- فیلتر کردن ورودی پلات ---
        if "Operating Point" not in sim_type:
            # اگر AC بود، فقط گزینه‌های ولتاژ را نشان بده
            if "AC" in sim_type:
                ac_options = [opt for opt in plot_ops if opt.lower().startswith("v")]
                if ac_options:
                    plot_var = st.selectbox("Signal (Voltage Only)", ac_options, index=0)
                else:
                    plot_var = st.text_input("Signal (Voltage Only)", "v(out)")
            else:
                # برای بقیه (Tran/DC) همه گزینه‌ها (ولتاژ و جریان)
                plot_var = st.selectbox("Signal", plot_ops, index=def_idx) if plot_ops else st.text_input("Signal", "v(out)")
        else:
            plot_var = "all"

        if "Transient" in sim_type:
            with c1: params["step"]=st.text_input("Step", "1ms")
            with c2: params["stop"]=st.text_input("Stop", "100ms")
            with c3: params["uic"]=st.checkbox("UIC", False)
        elif "AC" in sim_type:
            with c1: params["points"]=st.text_input("Points/Dec", "10")
            with c2: params["fstart"]=st.text_input("Start", "1Hz")
            with c3: params["fstop"]=st.text_input("Stop", "1MHz")
        elif "DC Sweep" in sim_type:
            with c1: params["source"]=st.text_input("Source", "V1")
            with c2: params["start"]=st.text_input("Start", "0")
            with c3: params["stop"]=st.text_input("Stop", "5"); params["step"]=st.text_input("Step", "0.1")

    st.subheader("📝 Netlist Editor")
    def_code = generate_full_netlist(st.session_state["spice"], sim_type, params, plot_var)
    user_netlist = st.text_area("Edit Code:", value=def_code, height=250)

    if st.button("Run Simulation 🚀", use_container_width=True):
        with st.spinner("Simulating..."):
            res = run_ngspice_simulation(user_netlist)
            data = parse_ngspice_data(res)
            st.session_state.update({"sim_results": data, "sim_log": res})

    if st.session_state.get("sim_results"):
        data = st.session_state["sim_results"]
        log = st.session_state["sim_log"]

        if data.get("error"): st.error(data["error"])
        
        elif data["type"] == "scalars":
            st.success("DC Operating Point Results:")
            if data["values"]:
                df = pd.DataFrame(data["values"], columns=["Variable", "Value"])
                df["Value"] = pd.to_numeric(df["Value"], errors='coerce')
                
                junk = ["temp", "tnom", "size", "available", "seconds", "error", "cpu", "time", "total", "index", "job", "date"]
                mask_clean = ~df["Variable"].str.lower().apply(lambda x: any(bad in x for bad in junk))
                mask_clean &= ~df["Variable"].str.startswith("(")
                df_op = df[mask_clean].reset_index(drop=True)
                
                if not df_op.empty:
                    st.dataframe(df_op, use_container_width=True, hide_index=True)
                    
                    is_curr = df_op["Variable"].str.contains("#|i\(|@", case=False, na=False)
                    df_i = df_op[is_curr]
                    df_v = df_op[~is_curr] 

                    st.markdown("#### 📊 Analysis")
                    c_v, c_i = st.columns(2)
                    with c_v:
                        if not df_v.empty:
                            fig, ax = plt.subplots(figsize=(6, 4))
                            ax.barh(df_v["Variable"], df_v["Value"], color='#4CAF50')
                            ax.set_title("Voltages (V)"); ax.grid(axis='x', ls='--', alpha=0.5)
                            st.pyplot(fig, use_container_width=True)
                    with c_i:
                        if not df_i.empty:
                            fig, ax = plt.subplots(figsize=(6, 4))
                            ax.barh(df_i["Variable"], df_i["Value"], color='#FF5722')
                            ax.set_title("Currents (A)"); ax.grid(axis='x', ls='--', alpha=0.5)
                            st.pyplot(fig, use_container_width=True)
                else: st.warning("Filtered all outputs.")
            else: st.warning("No data found.")

        elif data["type"] == "plot":
            st.success(f"Result: {data['analysis']}")
            with st.expander("Settings", expanded=True):
                c_w, c_h = st.columns(2)
                pw = c_w.slider("Width", 4, 25, 10, key="pw"); ph = c_h.slider("Height", 3, 20, 6, key="ph")
            fig = create_matplotlib_plot(data["df"], data["analysis"], figsize=(pw, ph))
            st.pyplot(fig, use_container_width=False)
            st.download_button("Download CSV", data["df"].to_csv(index=False).encode(), "data.csv")

        st.markdown("---")
        with st.expander("📜 Full Log", expanded=False): st.text_area("Log", log, height=300)
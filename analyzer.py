# analyzer.py
import re
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def parse_ngspice_data(raw_output):
    """
    پارسر مقاوم (Robust Parser):
    - با دیدن خطای وسط فایل متوقف نمی‌شود (Continue به جای Break).
    - کاماهای مزاحم در اعداد مختلط را هندل می‌کند.
    """
    data = {"type": "raw", "content": raw_output}
    if not raw_output: return data
    if "Error:" in raw_output and "Fatal" in raw_output:
        data["error"] = raw_output; return data

    # --- Plot Data ---
    try:
        lines = raw_output.split('\n')
        header_idx = -1
        for i, line in enumerate(lines):
            if re.match(r"^\s*Index\s+", line, re.IGNORECASE):
                header_idx = i; break
        
        if header_idx != -1:
            headers = re.split(r"\s+", lines[header_idx].strip())
            num_cols = len(headers)
            data_rows = []
            
            for line in lines[header_idx+1:]:
                line = line.strip()
                if not line or line.startswith("-") or line.startswith("Warning"): continue
                
                # ترفند: حذف کاما برای جلوگیری از به هم ریختن ستون‌ها در اعداد مختلط
                line = line.replace(',', ' ')
                
                parts = re.split(r"\s+", line)
                
                # اگر تعداد ستون‌ها همخوانی نداشت، قطع نکن! فقط این خط را رد کن
                if len(parts) != num_cols:
                    # فقط اگر به فوتر فایل (آمار اجرا) رسیدیم قطع کن
                    if "total" in line.lower() or "elapsed" in line.lower(): break
                    else: continue 
                
                # اگر ستون اول ایندکس نیست، رد کن
                if not parts[0].replace('.', '', 1).isdigit(): continue
                
                data_rows.append(",".join(parts))
            
            if data_rows:
                csv = ",".join(headers) + "\n" + "\n".join(data_rows)
                df = pd.read_csv(io.StringIO(csv))
                if "Index" in df.columns: df = df.drop(columns=["Index"])
                
                data["type"] = "plot"; data["df"] = df
                col1 = df.columns[0].lower()
                if "time" in col1: data["analysis"] = "tran"
                elif "freq" in col1: data["analysis"] = "ac"
                elif "sweep" in col1: data["analysis"] = "dc_sweep"
                else: data["analysis"] = "unknown"
                return data
    except: pass

    # --- Scalar Data ---
    sc = re.findall(r"([a-zA-Z0-9_#\(\)\.]+)\s*=\s*([+-]?\d+\.?\d*e?[+-]?\d*)", raw_output)
    if sc:
        data["type"] = "scalars"; data["values"] = sc; return data

    data["error"] = "No valid data found."; return data

def create_matplotlib_plot(df, analysis_type, figsize=(10, 6)):
    if df.empty:
        fig, ax = plt.subplots(figsize=figsize); ax.text(0.5,0.5,"No Data"); return fig

    fig, ax = plt.subplots(figsize=figsize)
    x = df.columns[0]; y_cols = df.columns[1:]
    
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)

    if analysis_type == "ac":
        ax.set_xscale('log')
        for c in y_cols:
            lbl = c
            if "vdb" in c: lbl = f"{c} (dB)"
            elif "vm" in c or "mag" in c: lbl = f"{c} (Mag)"
            ax.plot(df[x], df[c], label=lbl, linewidth=2)
        ax.set_title("AC Response"); ax.set_xlabel("Freq (Hz)"); ax.set_ylabel("Magnitude")
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    else:
        for c in y_cols: ax.plot(df[x], df[c], label=c, linewidth=2)
        ax.set_xlabel(x)
        if analysis_type=="tran": ax.set_title("Transient")
        elif analysis_type=="dc_sweep": ax.set_title("DC Sweep")

    ax.legend(); plt.tight_layout()
    return fig
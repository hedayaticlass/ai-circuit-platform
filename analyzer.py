# analyzer.py
import re
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def parse_ngspice_data(raw_output):
    data = {"type": "raw", "content": raw_output}
    if not raw_output or "Error:" in raw_output:
        data["error"] = raw_output or "Empty output"
        return data

    try:
        # تلاش برای پارس کردن جدول داده‌ها
        lines = raw_output.split('\n')
        header_idx = -1
        for i, line in enumerate(lines):
            if re.match(r"^\s*Index\s+", line, re.IGNORECASE):
                header_idx = i; break
        
        if header_idx != -1:
            header_line = lines[header_idx].strip()
            headers = re.split(r"\s+", header_line)
            data_rows = []
            for line in lines[header_idx+1:]:
                line = line.strip()
                if not line or line.startswith(("-", "Warning")): continue
                parts = re.split(r"\s+", line)
                if len(parts) == len(headers) and parts[0].replace('.','',1).isdigit():
                    data_rows.append(",".join(parts))
            
            if data_rows:
                csv = ",".join(headers) + "\n" + "\n".join(data_rows)
                df = pd.read_csv(io.StringIO(csv))
                if "Index" in df.columns: df = df.drop(columns=["Index"])
                data["type"] = "plot"
                data["df"] = df
                
                col0 = df.columns[0].lower()
                if "time" in col0: data["analysis"] = "tran"
                elif "freq" in col0: data["analysis"] = "ac"
                else: data["analysis"] = "dc_sweep"
                return data

    except Exception: pass

    # تلاش برای پارس کردن مقادیر اسکالر (OP)
    # regex اصلاح شده برای گرفتن #branch و v(عدد)
    scalars = re.findall(r"([a-zA-Z0-9_\(\)\.#]+)\s*=\s*([+-]?\d+\.?\d*e?[+-]?\d*)", raw_output)
    if scalars:
        data["type"] = "scalars"
        data["values"] = scalars
        return data

    data["error"] = "No valid data found in simulation output."
    return data

def create_matplotlib_plot(df, analysis_type, figsize=(10, 6)):
    if df.empty: return plt.figure()
    fig, ax = plt.subplots(figsize=figsize)
    x_col = df.columns[0]
    y_cols = df.columns[1:]
    
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    if analysis_type == "ac":
        ax.set_xscale('log')
        for col in y_cols:
            ax.plot(df[x_col], df[col], label=col)
        ax.xaxis.set_major_formatter(ticker.ScalarFormatter())
    else:
        for col in y_cols:
            ax.plot(df[x_col], df[col], label=col)
            
    ax.legend()
    ax.set_xlabel(x_col)
    plt.tight_layout()
    return fig

def create_dc_op_plot(values, figsize=(10, 6)):
    """رسم نمودار برای DC Operating Point - فقط #branch و v(عدد)"""
    if not values:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No Data", ha='center', va='center')
        return fig
    
    # جدا کردن ولتاژها و جریان‌ها - فقط #branch و v(عدد)
    voltages = []
    currents = []
    
    for var_name, var_value in values:
        var_lower = var_name.lower()
        try:
            val = float(var_value)
        except:
            continue
        
        # فقط #branch را به عنوان جریان در نظر بگیر
        if "#branch" in var_lower:
            currents.append((var_name, val))
        # فقط v(عدد) را به عنوان ولتاژ در نظر بگیر (مثل v(1), v(2))
        elif re.match(r"^v\([0-9]+\)$", var_lower):
            # بررسی که داخل پرانتز یک عدد است
            match = re.match(r"^v\(([0-9]+)\)$", var_lower)
            if match:
                node = match.group(1)
                # فقط اگر عدد است
                if node.isdigit():
                    voltages.append((var_name, val))
    
    # اگر هیچ داده‌ای پیدا نشد، پیام نمایش بده
    if not voltages and not currents:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No v(number) or #branch variables found", ha='center', va='center')
        return fig
    
    # ایجاد نمودار
    if voltages or currents:
        fig, axes = plt.subplots(1, 2, figsize=figsize) if (voltages and currents) else plt.subplots(1, 1, figsize=figsize)
        
        if voltages and currents:
            ax1, ax2 = axes
        elif voltages:
            ax1 = axes
            ax2 = None
        else:
            ax1 = None
            ax2 = axes
        
        # رسم ولتاژها
        if voltages and ax1 is not None:
            vars_v = [v[0] for v in voltages]
            vals_v = [v[1] for v in voltages]
            y_pos = range(len(vars_v))
            bars = ax1.barh(y_pos, vals_v, align='center', color='steelblue')
            ax1.set_yticks(y_pos)
            ax1.set_yticklabels(vars_v)
            ax1.set_xlabel('Voltage (V)')
            ax1.set_title('Node Voltages')
            ax1.grid(True, axis='x', linestyle='--', alpha=0.7)
            # اضافه کردن مقدار روی هر bar
            for i, (var, val) in enumerate(voltages):
                ax1.text(val, i, f' {val:.6e} V', va='center', fontsize=9)
        
        # رسم جریان‌ها
        if currents and ax2 is not None:
            vars_i = [i[0] for i in currents]
            vals_i = [i[1] for i in currents]
            y_pos = range(len(vars_i))
            bars = ax2.barh(y_pos, vals_i, align='center', color='coral')
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(vars_i)
            ax2.set_xlabel('Current (A)')
            ax2.set_title('Source Currents')
            ax2.grid(True, axis='x', linestyle='--', alpha=0.7)
            # اضافه کردن مقدار روی هر bar
            for i, (var, val) in enumerate(currents):
                ax2.text(val, i, f' {val:.6e} A', va='center', fontsize=9)
        
        plt.tight_layout()
        return fig
    else:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "No Data", ha='center', va='center')
        return fig
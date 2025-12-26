# utils.py
import subprocess
import os
import tempfile
import shutil
import platform
import re
import pandas as pd
import io

# تنظیم backend برای سرورهای لینوکسی بدون مانیتور
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt

def run_ngspice_simulation(netlist_code):
    """اجرای ساده بدون پلات برای تحلیل‌های متنی یا ویندوز"""
    command = "ngspice"
    if platform.system() == "Windows":
        if shutil.which("ngspice_con"): command = "ngspice_con"
    
    final_netlist = netlist_code
    if not netlist_code.strip().startswith("*"):
        final_netlist = "* Auto-generated Title\n" + netlist_code

    with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(final_netlist)
        temp_file_path = temp_file.name
    
    try:
        process = subprocess.run([command, '-b', temp_file_path], capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=20)
        full_output = process.stdout + "\n" + process.stderr
    except Exception as e:
        full_output = str(e)
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)
        
    return full_output

def run_ngspice_with_plot(netlist_code, plot_output_path="plot.png", variables_to_plot=""):
    """
    تلاش برای رسم با ngspice، و اگر سرور گرافیک نداشت، رسم با matplotlib (Fallback).
    """
    # ---------------------------------------------------------
    # مرحله ۱: تلاش برای اجرای استاندارد با Ngspice (روش سریع)
    # ---------------------------------------------------------
    lines = netlist_code.splitlines()
    # حذف دستورات چاپی قدیمی برای جلوگیری از تداخل
    cleaned_lines = [l for l in lines if not l.strip().lower().startswith((".end", ".print", ".plot"))]
    base_netlist = "\n".join(cleaned_lines)
    
    # ساخت بلاک کنترل برای ngspice
    control_block = [
        "\n.control",
        "set hcopydevtype=png",      
        "set color0=white",          
        "set color1=black",
        "run",
    ]
    
    # اگر متغیر خاصی خواسته شده، دستور hardcopy را اضافه می‌کنیم
    if variables_to_plot and variables_to_plot != "all":
        # برخی نسخه‌های ngspice با پرانتز در hardcopy مشکل دارند، اما اغلب استاندارد است
        control_block.append(f"hardcopy {plot_output_path} {variables_to_plot}")
    
    control_block.append(".endc")
    control_block.append(".end")
    
    final_netlist = base_netlist + "\n" + "\n".join(control_block)
    if not final_netlist.strip().startswith("*"):
        final_netlist = "* Auto-generated\n" + final_netlist

    with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(final_netlist)
        temp_file_path = temp_file.name

    ngspice_log = ""
    try:
        process = subprocess.run(["ngspice", '-b', temp_file_path], capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=30)
        ngspice_log = process.stdout + "\n" + process.stderr
    finally:
        if os.path.exists(temp_file_path): os.remove(temp_file_path)

    # ---------------------------------------------------------
    # مرحله ۲: بررسی موفقیت و Fallback به پایتون
    # ---------------------------------------------------------
    
    # اگر فایل عکس ساخته شده و حجم دارد، یعنی موفق بوده
    if os.path.exists(plot_output_path) and os.path.getsize(plot_output_path) > 0:
        return ngspice_log, plot_output_path
    
    # اگر فایل نیست (خطای Can't find device png)، خودمان با پایتون می‌کشیم
    
    analysis_cmd = ""
    # تشخیص نوع تحلیل برای دستور print صحیح
    if ".tran" in base_netlist.lower(): analysis_cmd = "tran"
    elif ".dc" in base_netlist.lower(): analysis_cmd = "dc"
    elif ".ac" in base_netlist.lower(): analysis_cmd = "ac"
    
    if analysis_cmd:
        # ساخت یک نت‌لیست جدید فقط برای استخراج دیتا
        print_line = f".print {analysis_cmd} {variables_to_plot}"
        fallback_netlist = base_netlist + "\n" + print_line + "\n.end"
        
        # اجرای شبیه‌سازی برای گرفتن داده متنی
        raw_data = run_ngspice_simulation(fallback_netlist)
        
        # پارس کردن داده‌ها برای رسم با Matplotlib
        try:
            if "Index" in raw_data:
                lines = raw_data.split('\n')
                # پیدا کردن شروع جدول
                idx = next(i for i, l in enumerate(lines) if "Index" in l)
                
                # تمیز کردن داده‌ها (تبدیل فاصله به کاما)
                data_lines = []
                for l in lines[idx:]:
                    if l.strip() and not l.startswith("-") and not l.startswith("*"):
                        cleaned = re.sub(r"\s+", ",", l.strip())
                        data_lines.append(cleaned)
                
                if data_lines:
                    df = pd.read_csv(io.StringIO("\n".join(data_lines)))
                    
                    # رسم نمودار
                    if not df.empty:
                        cols = list(df.columns)
                        # ستون اول همیشه محور X است (Time/Freq/Volt)
                        x_col = cols[1] if cols[0].lower() == "index" else cols[0]
                        y_cols = [c for c in cols if c != x_col and c.lower() != "index"]
                        
                        plt.figure(figsize=(10, 6))
                        for y in y_cols:
                            clean_y = pd.to_numeric(df[y], errors='coerce')
                            clean_x = pd.to_numeric(df[x_col], errors='coerce')
                            plt.plot(clean_x, clean_y, label=y, linewidth=2)
                        
                        plt.xlabel(x_col)
                        plt.ylabel("Value")
                        plt.title("Simulation Result (Python Plot)")
                        plt.grid(True, which='both', linestyle='--', alpha=0.7)
                        plt.legend()
                        
                        # ذخیره عکس نهایی
                        plt.savefig(plot_output_path, dpi=100, bbox_inches='tight')
                        plt.close()
                        
                        return raw_data, plot_output_path
                    
        except Exception as e:
            return ngspice_log + f"\n\nPython Plot Error: {str(e)}", None

    return ngspice_log + "\n\nError: Could not generate plot via Ngspice or Python.", None
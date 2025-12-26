# utils.py
import json
import glob
import subprocess
import os
import tempfile
import shutil
import platform




def save_circuit(spice, name):
    fname = f"{name}.json"
    data = {"spice": spice}
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return fname

def load_circuit(name):
    with open(name, "r", encoding="utf-8") as f:
        return json.load(f)

def list_circuits():
    return sorted(glob.glob("*.json"))



def run_ngspice_simulation(netlist_code):
    """
    اجرای هوشمند نت‌لیست با ngspice (سازگار با ویندوز و لینوکس).
    """
    # -------------------------------------------------------
    # 1. انتخاب دستور مناسب بر اساس سیستم عامل
    # -------------------------------------------------------
    command = "ngspice" # پیش‌فرض برای لینوکس/مک
    
    if platform.system() == "Windows":
        # در ویندوز، نسخه کنسولی (ngspice_con) خروجی را بهتر برمی‌گرداند
        if shutil.which("ngspice_con"):
            command = "ngspice_con"
        elif shutil.which("ngspice"):
            command = "ngspice"
        else:
            return "⚠️ Error: Ngspice not found. Please add 'ngspice_con.exe' or 'ngspice.exe' to your PATH."
    else:
        # در لینوکس
        if not shutil.which("ngspice"):
             return "⚠️ Error: Ngspice is not installed on the server."

    temp_file_path = ""
    try:
        # -------------------------------------------------------
        # 2. اصلاح نت‌لیست (افزودن تیتر اجباری)
        # -------------------------------------------------------
        # اگر خط اول ستاره نداشت (کامنت نبود)، یک تیتر مصنوعی اضافه کن
        # تا ngspice خط اول واقعی (مثل V1) را نبلعد!
        final_netlist = netlist_code
        if not netlist_code.strip().startswith("*"):
            final_netlist = "* Auto-generated Title by AI Circuit Platform\n" + netlist_code

        # -------------------------------------------------------
        # 3. ساخت فایل موقت
        # -------------------------------------------------------
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(final_netlist)
            temp_file_path = temp_file.name
        
        # -------------------------------------------------------
        # 4. اجرا
        # -------------------------------------------------------
        process = subprocess.run(
            [command, '-b', temp_file_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=20
        )

        # حذف فایل موقت
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # ترکیب خروجی‌ها
        full_output = process.stdout + "\n" + process.stderr
        
        # دیباگ دقیق‌تر در صورت خالی بودن خروجی
        if not full_output.strip():
            return (f"⚠️ Debug Info: ran '{command}' but got no output.\n"
                    f"Exit Code: {process.returncode}\n"
                    "Possible fix: Ensure you are using 'ngspice_con.exe' on Windows, not the GUI version.")
            
        return full_output

    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return f"System Error: {str(e)}"


# utils.py (Updated)

def run_ngspice_with_plot(netlist_code, plot_output_path="plot.png", variables_to_plot=""):
    """
    اجرای ngspice در حالت لینوکس با دستور hardcopy برای تولید تصویر توسط خود انجین.
    """
    if not shutil.which("ngspice"):
        return "⚠️ Error: Ngspice is not installed on the server.", None

    temp_file_path = ""
    try:
        # حذف .end از انتهای فایل اصلی اگر وجود دارد (چون می‌خواهیم بلاک کنترل اضافه کنیم)
        lines = netlist_code.splitlines()
        cleaned_lines = [l for l in lines if not l.strip().lower().startswith(".end")]
        base_netlist = "\n".join(cleaned_lines)

        # ساخت بلاک کنترلی برای تولید گرافیک
        # set hcopydevtype=png: تعیین فرمت خروجی (نیاز به کامپایل ngspice با cairo دارد)
        # set color0=white: پس‌زمینه سفید (مناسب برای وب)
        # set color1=black: رنگ متن مشکی
        control_block = [
            "\n* Plotting Control Block",
            ".control",
            "set hcopydevtype=png",      
            "set color0=white",          
            "set color1=black",          
            "set hcopyfont=Arial",       
            "set hcopyfontsize=12",
            "run",                       # اجرای شبیه‌سازی
        ]

        # اگر متغیری برای رسم داده شده، دستور hardcopy را می‌نویسیم
        if variables_to_plot:
            control_block.append(f"hardcopy {plot_output_path} {variables_to_plot}")
        
        control_block.append(".endc")
        control_block.append(".end")

        final_netlist = base_netlist + "\n" + "\n".join(control_block)
        
        # اگر تیتر ندارد اضافه کن
        if not final_netlist.strip().startswith("*"):
            final_netlist = "* Auto-generated Title\n" + final_netlist

        # ذخیره در فایل موقت
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(final_netlist)
            temp_file_path = temp_file.name
        
        # اجرا
        process = subprocess.run(
            ["ngspice", '-b', temp_file_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        full_output = process.stdout + "\n" + process.stderr
        
        # بررسی اینکه آیا فایل ساخته شده یا خیر
        final_plot_path = None
        if os.path.exists(plot_output_path):
            final_plot_path = plot_output_path
        
        return full_output, final_plot_path

    except Exception as e:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return f"System Error: {str(e)}", None
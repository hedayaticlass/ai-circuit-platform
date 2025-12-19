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
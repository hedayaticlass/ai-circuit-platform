# utils.py
import subprocess
import os
import tempfile
import shutil
import platform
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt

def check_ngspice_available():
    """بررسی نصب بودن ngspice"""
    commands = ["ngspice_con", "ngspice", "ngspice.exe"] if platform.system()=="Windows" else ["ngspice", "ngspice_release"]
    for cmd in commands:
        if shutil.which(cmd): return cmd, True
    return None, False

def run_ngspice_simulation(netlist_code):
    """اجرای شبیه‌سازی با تایم‌اوت طولانی"""
    cmd, ok = check_ngspice_available()
    if not ok: return "❌ Error: ngspice not found."
    
    final_netlist = netlist_code
    if not netlist_code.strip().startswith("*"):
        final_netlist = "* Auto-generated\n" + netlist_code

    with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False, encoding='utf-8') as tf:
        tf.write(final_netlist)
        tname = tf.name
    
    try:
        # افزایش تایم‌اوت به 120 ثانیه برای جلوگیری از قطع شدن AC Sweep
        process = subprocess.run(
            [cmd, '-b', tname],
            capture_output=True, text=True, encoding='utf-8', errors='ignore',
            timeout=120 
        )
        return process.stdout + "\n" + process.stderr
    except subprocess.TimeoutExpired:
        return "❌ Error: Simulation timed out (limit 120s)."
    except Exception as e:
        return f"❌ Error: {str(e)}"
    finally:
        if os.path.exists(tname): os.remove(tname)
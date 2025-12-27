# utils.py
import subprocess
import os
import tempfile
import shutil
import platform

def run_ngspice_simulation(netlist_code):
    command = "ngspice"
    if platform.system() == "Windows":
        if shutil.which("ngspice_con"): command = "ngspice_con"
        elif shutil.which("ngspice"): command = "ngspice"
        else: return "Error: Ngspice not found. Add it to PATH."
    
    # افزودن تایتل اجباری برای ngspice
    final_netlist = netlist_code
    if not netlist_code.strip().startswith("*"):
        final_netlist = "* Generated Netlist\n" + netlist_code

    with tempfile.NamedTemporaryFile(mode='w', suffix='.cir', delete=False, encoding='utf-8') as tf:
        tf.write(final_netlist)
        temp_path = tf.name

    try:
        process = subprocess.run(
            [command, '-b', temp_path],
            capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=20
        )
        return process.stdout + "\n" + process.stderr
    except Exception as e:
        return f"System Error: {e}"
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
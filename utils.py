# utils.py
import json
import glob

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

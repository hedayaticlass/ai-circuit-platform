# parser.py
import re

def get_netlist_info(spice_text):
    """استخراج گره‌ها و قطعات برای کنسول شبیه‌سازی"""
    nodes = set()
    elements = []
    lines = spice_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith(('*', '.', 'v', 'V', 'i', 'I')) and len(line.split()) < 3:
            if line and line[0].upper() in 'RVLCIQDM':
                parts = line.split()
                if len(parts) > 0: elements.append(parts[0])
            continue
        parts = line.split()
        if len(parts) >= 3:
            name = parts[0]
            elements.append(name)
            nodes.add(parts[1])
            nodes.add(parts[2])
            if len(parts) >= 4 and name[0].upper() in 'QM':
                nodes.add(parts[3])
    if '0' in nodes: nodes.remove('0')
    return sorted(list(nodes)), sorted(list(elements))

def parse_netlist(text):
    """تجزیه برای رسم شماتیک"""
    comps = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('.', '*')): continue
        p = line.split()
        if len(p) < 3: continue
        comps.append({"ref": p[0], "type": p[0][0].upper(), "nodes": p[1:3], "value": p[3] if len(p)>3 else ""})
    return comps
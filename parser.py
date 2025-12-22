# parser.py

def get_netlist_info(spice_text):
    """استخراج گره‌ها و نام قطعات برای استفاده در لیست‌های انتخابی UI"""
    nodes = set()
    elements = []
    lines = spice_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith(('*', '.', 'v', 'V', 'i', 'I')) and len(line.split()) < 3:
            # اگر خط با نام قطعه شروع شود اما دستور نباشد
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
    """تجزیه نت‌لیست برای رسم شماتیک"""
    comps = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('.', '*')):
            continue
        p = line.split()
        name = p[0]
        t = name[0].upper()
        if t in ['R','C','L','V','I']:
            comps.append({"ref": name, "type": t, "value": p[3] if len(p)>3 else "", "nodes": [p[1], p[2]]})
        elif t == 'D':
            comps.append({"ref": name, "type": "D", "nodes": [p[1], p[2]]})
        elif t in ['Q', 'M']:
            comps.append({"ref": name, "type": t, "nodes": p[1:4]})
    return comps
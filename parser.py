# parser.py
def parse_netlist(text):
    comps = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(('.', '*')):
            continue
        p = line.split()
        name = p[0]
        t = name[0].upper()

        if t in ['R','C','L','V','I']:
            comps.append({
                "ref": name,
                "type": t,
                "value": p[3] if len(p)>3 else "",
                "nodes": [p[1], p[2]]
            })

        elif t == 'D':  # diode
            comps.append({
                "ref": name,
                "type": "D",
                "value": p[3] if len(p)>3 else "Si",
                "nodes": [p[1], p[2]]
            })

        elif t == 'Q':  # BJT
            comps.append({
                "ref": name,
                "type": "BJT",
                "model": p[4] if len(p)>4 else "",
                "nodes": [p[1], p[2], p[3]]
            })

        elif t == 'M':  # MOSFET
            comps.append({
                "ref": name,
                "type": "MOS",
                "model": p[5] if len(p)>5 else "",
                "nodes": [p[1], p[2], p[3], p[4]]
            })
    return comps

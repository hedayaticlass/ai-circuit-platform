def parse_netlist(text):
    """تبدیل متن نت‌لیست به لیست قطعات"""
    components = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('*') or line.startswith('.'):
            continue
        
        parts = line.split()
        if len(parts) < 3:
            continue
        
        comp_type = parts[0][0].upper()
        name = parts[0]
        
        # دیود
        if comp_type == 'D':
            node1, node2 = parts[1], parts[2]
            model = parts[3] if len(parts) > 3 else "1N4148"
            components.append({
                'type': comp_type,
                'name': name,
                'node1': node1,
                'node2': node2,
                'value': model,
                'pins': 2
            })
        
        # ترانزیستور BJT
        elif comp_type == 'Q':
            if len(parts) < 4:
                continue
            collector, base, emitter = parts[1], parts[2], parts[3]
            model = parts[4] if len(parts) > 4 else "2N2222"
            components.append({
                'type': comp_type,
                'name': name,
                'collector': collector,
                'base': base,
                'emitter': emitter,
                'node1': collector,
                'node2': emitter,
                'value': model,
                'pins': 3
            })
        
        # MOSFET
        elif comp_type == 'M':
            if len(parts) < 5:
                continue
            drain, gate, source, body = parts[1], parts[2], parts[3], parts[4]
            model = parts[5] if len(parts) > 5 else "IRF530"
            components.append({
                'type': comp_type,
                'name': name,
                'drain': drain,
                'gate': gate,
                'source': source,
                'body': body,
                'node1': drain,
                'node2': source,
                'value': model,
                'pins': 4
            })
        
        # JFET
        elif comp_type == 'J':
            if len(parts) < 4:
                continue
            drain, gate, source = parts[1], parts[2], parts[3]
            model = parts[4] if len(parts) > 4 else "J2N5457"
            components.append({
                'type': comp_type,
                'name': name,
                'drain': drain,
                'gate': gate,
                'source': source,
                'node1': drain,
                'node2': source,
                'value': model,
                'pins': 3
            })
        
        # آپ‌امپ و IC (U, X)
        elif comp_type in ['U', 'X']:
            if len(parts) < 6:
                continue
            nodes = parts[1:-1]
            model = parts[-1]
            components.append({
                'type': comp_type,
                'name': name,
                'nodes': nodes,
                'node1': nodes[0],
                'node2': nodes[2] if len(nodes) > 2 else nodes[-1],
                'value': model,
                'pins': len(nodes)
            })
        
        # قطعات دو پایه معمولی (R, C, L, V, I, ...)
        else:
            if len(parts) < 4:
                continue
            node1, node2 = parts[1], parts[2]
            value = parts[3]
            components.append({
                'type': comp_type,
                'name': name,
                'node1': node1,
                'node2': node2,
                'value': value,
                'pins': 2
            })
    
    return components
# drawer_pro.py

import schemdraw
import schemdraw.elements as elm
from collections import defaultdict

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

def find_parallel_groups(components):
    """پیدا کردن قطعات موازی با ترتیب صحیح"""
    edge_map = defaultdict(list)
    
    for comp in components:
        if comp['type'] == 'V':
            continue
        
        if 'node1' in comp and 'node2' in comp:
            key = tuple(sorted([comp['node1'], comp['node2']]))
            edge_map[key].append(comp)
    
    def node_key(n):
        try:
            return int(n)
        except ValueError:
            return float('inf')
    
    sorted_edges = sorted(edge_map.items(), key=lambda x: (
        min(node_key(x[0][0]), node_key(x[0][1])),
        max(node_key(x[0][0]), node_key(x[0][1]))
    ))
    
    return [comps for edge, comps in sorted_edges]

def draw_component(d, comp, direction='right'):
    """رسم یک قطعه"""
    label = f"{comp['name']}\n{comp['value']}"
    comp_type = comp['type']
    
    if comp_type == 'R':
        elm_obj = elm.Resistor()
    
    elif comp_type == 'C':
        elm_obj = elm.Capacitor()
    
    elif comp_type == 'L':
        elm_obj = elm.Inductor2()
    
    elif comp_type == 'D':
        value_lower = str(comp['value']).lower()
        is_zener = ('zener' in value_lower or 'bz' in value_lower or 
                    '1n47' in value_lower or 'z' == value_lower.strip())
        is_ge = ('1n34' in value_lower or '1n60' in value_lower or
                 'oa' in value_lower or 'ay' in value_lower or 'ge' in value_lower)
        
        if is_zener:
            elm_obj = elm.Zener()
            label = f"{comp['name']}\nZener"
        else:
            elm_obj = elm.Diode()
            if is_ge:
                label = f"{comp['name']}\nGe"
            else:
                label = f"{comp['name']}\nSi"
    
    elif comp_type == 'Q':
        value_lower = str(comp['value']).lower()
        if 'pnp' in value_lower:
            try:
                elm_obj = elm.BjtPnp()
            except AttributeError:
                elm_obj = elm.BjtNpn()
        else:
            elm_obj = elm.BjtNpn()
    
    elif comp_type == 'M':
        value_lower = str(comp['value']).lower()
        is_p = ('pmos' in value_lower or 'pfet' in value_lower or 'p-' in value_lower)
        if is_p:
            try:
                elm_obj = elm.PFet()
            except AttributeError:
                elm_obj = elm.NFet()
        else:
            elm_obj = elm.NFet()
    
    elif comp_type == 'J':
        elm_obj = elm.JFet()
    
    elif comp_type in ['U', 'X']:
        elm_obj = elm.Opamp()
        label = f"{comp['name']}\n{comp['value']}"
    
    else:
        elm_obj = elm.Resistor()
    
    if direction == 'right':
        return d.add(elm_obj.right().label(label))
    else:
        return d.add(elm_obj.down().label(label))

def spice_to_schematic(components, parsed = True):
    """تبدیل کد SPICE به شماتیک"""
    if not parsed:
        components = parse_netlist(components)
    
    if not components:
        return None, "❌ هیچ قطعه‌ای یافت نشد!"
    
    voltage_source = next((c for c in components if c['type'] == 'V'), None)
    if not voltage_source:
        return None, "⚠️ منبع ولتاژ یافت نشد!"
    
    other_comps = [c for c in components if c['type'] != 'V']
    all_groups = find_parallel_groups(other_comps)
    
    n = len(all_groups)
    if n <= 2:
        top_count = n
        right_count = 0
    else:
        top_count = (n + 1) // 2
        right_count = n - top_count
    
    d = schemdraw.Drawing()
    
    v = d.add(elm.SourceV().up().label(f"{voltage_source['name']}\n{voltage_source['value']}"))
    d.add(elm.Line().right())
    
    # رسم قطعات بالایی (افقی)
    for i in range(top_count):
        group = all_groups[i]
        
        if len(group) == 1:
            draw_component(d, group[0], 'right')
        else:
            start_point = d.here
            draw_component(d, group[0], 'right')
            end_point = d.here
            
            for j, comp in enumerate(group[1:], 1):
                d.push()
                d.add(elm.Line().at(start_point).down().length(1.5 * j))
                draw_component(d, comp, 'right')
                d.add(elm.Line().right().tox(end_point[0]))
                d.add(elm.Line().up().toy(end_point[1]))
                d.pop()
            
            d.move_from(end_point, 0, 0)
    
    # رسم قطعات سمت راست (عمودی)
    if right_count > 0:
        d.add(elm.Line().down())
        
        for i in range(right_count):
            group = all_groups[top_count + i]
            
            if len(group) == 1:
                draw_component(d, group[0], 'down')
            else:
                start_point = d.here
                draw_component(d, group[0], 'down')
                end_point = d.here
                
                for j, comp in enumerate(group[1:], 1):
                    d.push()
                    d.add(elm.Line().at(start_point).left().length(1.5 * j))
                    draw_component(d, comp, 'down')
                    d.add(elm.Line().down().toy(end_point[1]))
                    d.add(elm.Line().right().tox(end_point[0]))
                    d.pop()
                
                d.move_from(end_point, 0, 0)
    
    # بستن مدار
    d.add(elm.Line().down())
    d.add(elm.Ground())
    d.add(elm.Line().left().tox(v.start))
    d.add(elm.Line().up().toy(v.start))


    return d, None
    
    
def render_schematics(netlist, save_path="schematic.png", show=False, parsed = True):
    """
    netlist is the components or the component. if you have used parser.py for parsing it, use as
        >>> render_schematics(components, save_path=...)
    else, use as
        >>> render_schematics(netlist : str, save_path=..., parsed = False)
    """
    drawing, error = spice_to_schematic(netlist, parsed=parsed)
    drawing.save(save_path)
    if show == True:
        drawing.draw()

if __name__ == "__main__":
    # parse_and_run()
    txt = """.title RC Low-Pass Filter\nV1 1 0 5\nR1 1 2 10k\nC1 2 0 10nF\n.end"""
    render_schematics(txt, show=True)
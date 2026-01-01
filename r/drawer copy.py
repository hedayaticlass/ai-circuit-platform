# drawer_pro.py

import matplotlib
# اگر در ویندوز خطای GUI گرفتید، خط زیر را از کامنت خارج کنید
# matplotlib.use("TkAgg") 

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from schemdraw import Drawing
import schemdraw.elements as elm
from collections import defaultdict

# -------------------------------------------------
# Circuit Drawer Class (High Density Support)
# -------------------------------------------------
class CircuitDrawer:
    def __init__(self):
        self.d = Drawing(show=False)
        self.d.config(unit=2.5, fontsize=10)
        
        self.node_pos = {}        # {node_name: (x, y)}
        self.pair_count = defaultdict(int)  # شمارش قطعات بین دو گره (n1, n2)
        self.base_usage = defaultdict(int)  # شمارش استفاده از گره بیس/گیت برای ترانزیستورها
        
        self.cursor_x = 0
        self.cursor_y = 0
        self.step_x = 4.0  # فاصله افقی بیشتر برای جا دادن موازی‌ها
        
        # تعریف گره زمین
        self.node_pos["0"] = (0, -2)

    def _get_or_create_node_pos(self, n1, n2=None):
        """منطق تعیین موقعیت هوشمند برای گسترش مدار به سمت راست"""
        if n1 in self.node_pos:
            pass
        elif n2 and n2 in self.node_pos:
            self.node_pos[n1] = (self.node_pos[n2][0] - self.step_x, self.node_pos[n2][1])
        else:
            self.node_pos[n1] = (self.cursor_x, 0)
            self.cursor_x += self.step_x

        return self.node_pos[n1]

    def add_component(self, comp):
        t = comp["type"]
        nodes = comp["nodes"]
        # ساخت لیبل با نام و مقدار
        val = comp['value']
        label_text = f"{comp['name']}\n{val}" if val else comp['name']
        
        try:
            # ---- 2-TERMINAL (R, C, L, D, V, I) ----
            if len(nodes) == 2:
                n1, n2 = nodes
                key = tuple(sorted((n1, n2)))
                idx = self.pair_count[key]
                self.pair_count[key] += 1
                
                # تعیین پوزیشن
                if n1 == "0": p1 = (self.node_pos.get(n2, (0,0))[0], -2); p2 = self._get_or_create_node_pos(n2)
                elif n2 == "0": p1 = self._get_or_create_node_pos(n1); p2 = (p1[0], -2)
                else: 
                    p1 = self._get_or_create_node_pos(n1)
                    p2 = self._get_or_create_node_pos(n2, n1)
                
                element = self._get_element_instance(t, label_text)
                self._draw_parallel_2t(element, p1, p2, idx, n1, n2)

            # ---- 3-TERMINAL (BJT - Q) ----
            elif t == "Q":
                c, b, e = nodes[:3]
                self._draw_transistor(elm.BjtNpn, label_text, c, b, e)

            # ---- 4-TERMINAL (MOSFET - M) ----
            elif t == "M":
                d, g, s = nodes[:3]
                self._draw_transistor(elm.NMos, label_text, d, g, s)

            # ---- OPAMP (U) ----
            elif t == "OPAMP":
                np, nm, out = nodes[:3]
                self._draw_opamp(label_text, np, nm, out)

        except Exception as e:
            print(f"[ERROR] {comp['name']}: {e}")

    def _get_element_instance(self, t, label):
        mapper = {
            "R": elm.Resistor, "C": elm.Capacitor, "L": elm.Inductor,
            "D": elm.Diode, "V": elm.SourceV, "I": elm.SourceI
        }
        return mapper.get(t, elm.Resistor)().label(label)

    def _draw_parallel_2t(self, element, p1, p2, idx, n1, n2):
        is_gnd = (n1 == "0" or n2 == "0")
        
        if is_gnd:
            shift = idx * 1.5
            top = p1 if p1[1] > p2[1] else p2
            bot = (top[0], -2)
            
            new_top = (top[0] + shift, top[1])
            new_bot = (top[0] + shift, bot[1])
            
            self.d.add(elm.Line().at(top).to(new_top))
            self.d.add(element.at(new_top).to(new_bot))
            self.d.add(elm.Ground().at(new_bot))
            
        else:
            direction = 1 if idx % 2 != 0 else -1
            step = (idx + 1) // 2
            offset = step * 1.5 * direction
            
            if idx == 0:
                self.d.add(element.at(p1).to(p2))
            else:
                self.d.add(elm.Line().at(p1).up(offset))
                self.d.add(element.right().length(self.step_x))
                self.d.add(elm.Line().down(offset).to(p2))

    def _draw_transistor(self, elm_cls, label, c, b, e):
        usage_idx = self.base_usage[b]
        self.base_usage[b] += 1
        
        if b not in self.node_pos:
            self.node_pos[b] = (self.cursor_x, 0)
            self.cursor_x += 3
            
        base_origin = self.node_pos[b]
        y_shift = -2.5 * usage_idx
        pos = (base_origin[0], base_origin[1] + y_shift)
        
        anchor_name = 'gate' if elm_cls == elm.NMos else 'base'
        
        if usage_idx > 0:
            self.d.add(elm.Line().at(base_origin).to(pos))
            
        inst = self.d.add(elm_cls().at(pos).anchor(anchor_name).label(label))
        
        self._route_wire(inst.drain if elm_cls == elm.NMos else inst.collector, c)
        self._route_wire(inst.source if elm_cls == elm.NMos else inst.emitter, e)

    def _draw_opamp(self, label, np, nm, out):
        if np not in self.node_pos:
            self.node_pos[np] = (self.cursor_x, 0)
            self.cursor_x += 3
        
        pos = self.node_pos[np]
        op = self.d.add(elm.Opamp().at(pos).anchor('in2').label(label))
        
        self._route_wire(op.in1, nm)
        self._route_wire(op.out, out)
        self.node_pos[out] = op.out.end

    def _route_wire(self, pin, node_name):
        if node_name == "0":
            self.d.add(elm.Ground().at(pin))
        else:
            if node_name in self.node_pos:
                self.d.add(elm.Wire("-|").at(pin).to(self.node_pos[node_name]))
            else:
                self.d.add(elm.Dot().at(pin))
                # اصلاح شده: size حذف شد و fontsize اضافه شد
                self.d.add(elm.Label().at(pin).label(node_name, fontsize=8))

    def render(self, output_file):
        for n, p in self.node_pos.items():
            if n != "0":
                self.d.add(elm.Dot().at(p))
                # اصلاح شده: size حذف شد و fontsize اضافه شد
                self.d.add(elm.Label().at(p).label(n, color='blue', ofst=(0.1, 0.1), fontsize=8))
        
        self.d.draw()
        self.d.save(output_file)
        
        try:
            img = mpimg.imread(output_file)
            plt.figure(figsize=(12, 8))
            plt.imshow(img)
            plt.axis('off')
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"Cannot show image: {e}")

# -------------------------------------------------
# Parser & Main
# -------------------------------------------------
def parse_and_run():
    print("Paste your Netlist below (End with 'END'):")
    lines = []
    while True:
        try:
            line = input()
            if not line: continue
            if line.strip().upper() == "END": break
            if line.strip(): lines.append(line)
        except: break

    drawer = CircuitDrawer()
    
    for line in lines:
        parts = line.split()
        if not parts: continue
        
        name = parts[0]
        type_char = name[0].upper()
        
        comp = {"name": name, "type": "R", "nodes": [], "value": ""}
        
        if type_char == "U": 
             comp["type"] = "OPAMP"
             comp["nodes"] = parts[1:4]
        elif type_char == "Q":
             comp["type"] = "Q"
             comp["nodes"] = parts[1:4]
             comp["value"] = parts[4] if len(parts)>4 else ""
        elif type_char == "M":
             comp["type"] = "M"
             comp["nodes"] = parts[1:4]
             comp["value"] = parts[5] if len(parts)>5 else ""
        else:
             comp["type"] = type_char
             comp["nodes"] = parts[1:3]
             comp["value"] = parts[3] if len(parts)>3 else ""
             
        drawer.add_component(comp)

    drawer.render("complex_circuit.png")
    
    
def render_schematics(netlist):
    lines = netlist.split("\n")
    drawer = CircuitDrawer()
    
    for line in lines:
        parts = line.split()
        if not parts: continue
        
        name = parts[0]
        type_char = name[0].upper()
        
        comp = {"name": name, "type": "R", "nodes": [], "value": ""}
        
        if type_char == "U": 
             comp["type"] = "OPAMP"
             comp["nodes"] = parts[1:4]
        elif type_char == "Q":
             comp["type"] = "Q"
             comp["nodes"] = parts[1:4]
             comp["value"] = parts[4] if len(parts)>4 else ""
        elif type_char == "M":
             comp["type"] = "M"
             comp["nodes"] = parts[1:4]
             comp["value"] = parts[5] if len(parts)>5 else ""
        else:
             comp["type"] = type_char
             comp["nodes"] = parts[1:3]
             comp["value"] = parts[3] if len(parts)>3 else ""
             
        drawer.add_component(comp)

    drawer.render("complex_circuit.png")

if __name__ == "__main__":
    # parse_and_run()
    txt = """.title RC Low-Pass Filter\nV1 1 0 5\nR1 1 2 10k\nC1 2 0 10nF\n.end"""
    render_schematics(txt)
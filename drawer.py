# drawer.py
import matplotlib
matplotlib.use("Agg") # جلوگیری از خطای GUI
from schemdraw import Drawing
import schemdraw.elements as elm

def render_schematic(components, save_path="schematic.png"):
    d = Drawing(show=False)
    for c in components:
        t = str(c.get("type", "")).lower()
        lbl = f"{c.get('name','')}\n{c.get('value','')}"
        
        if "resistor" in t: d.add(elm.Resistor().label(lbl))
        elif "capacit" in t: d.add(elm.Capacitor().label(lbl))
        elif "induct" in t: d.add(elm.Inductor().label(lbl))
        elif "voltage" in t: d.add(elm.SourceV().label(lbl))
        else: d.add(elm.Dot().label(lbl))
        
        d.add(elm.Line().right()) # رسم ساده خطی
        
    d.draw()
    d.save(save_path)
    return save_path
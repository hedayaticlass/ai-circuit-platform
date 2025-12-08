# drawer.py
from schemdraw import Drawing
import schemdraw.elements as elm

def render_schematic(components, save_path="schematic.png"):
    d = Drawing()

    for c in components:
        t = c["type"]
        label = f"{c['ref']}\n{c.get('value','')}"
        if t == "R":
            d.add(elm.Resistor().label(label))
        elif t == "C":
            d.add(elm.Capacitor().label(label))
        elif t == "L":
            d.add(elm.Inductor().label(label))
        elif t == "V":
            d.add(elm.SourceV().label(label))
        elif t == "I":
            d.add(elm.SourceI().label(label))
        elif t == "D":
            d.add(elm.Diode().label(label))
        elif t == "BJT":
            d.add(elm.BjtNpn().label(c["ref"]))
        elif t == "MOS":
            d.add(elm.MosfetN().label(c["ref"]))
        else:
            d.add(elm.Dot().label(c["ref"]))

        d.add(elm.Line().right())

    d.save(save_path)
    return save_path

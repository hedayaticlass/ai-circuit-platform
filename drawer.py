# drawer.py
from schemdraw import Drawing
import schemdraw.elements as elm
from cairosvg import svg2png

def render_schematic(components, save_path="schematic.png"):
    # رسم مدار به صورت SVG
    d = Drawing(show=False)

    for c in components:
        t = c["type"].lower()
        label = f"{c['name']}\n{c['value']}"

        if t in ["r", "resistor"]:
            d.add(elm.Resistor().label(label))
        elif t in ["c", "capacitor"]:
            d.add(elm.Capacitor().label(label))
        elif t in ["l", "inductor"]:
            d.add(elm.Inductor().label(label))
        elif t in ["v", "voltagesource", "voltage"]:
            d.add(elm.SourceV().label(label))
        elif t in ["i", "currentsource"]:
            d.add(elm.SourceI().label(label))
        else:
            d.add(elm.Dot().label(c["name"]))

        d.add(elm.Line().right())

    # ۱. SVG در قالب رشته
    svg_data = d.get_svg()

    # ۲. تبدیل SVG → PNG
    svg2png(bytestring=svg_data.encode("utf-8"), write_to=save_path)

    return save_path

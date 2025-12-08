# drawer.py
from schemdraw import Drawing
import schemdraw.elements as elm
from io import BytesIO
from PIL import Image

def render_schematic(components, save_path="schematic.png"):
    # رسم مدار
    d = Drawing(show=False)   # مهم: از show=False استفاده کن

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

    # رندر تصویر به صورت PNG در حافظه
    buf = BytesIO()
    d.save(buf, format='png')
    buf.seek(0)

    # ذخیره‌ی PNG
    img = Image.open(buf)
    img.save(save_path)

    return save_path

# drawer.py
import matplotlib
# برای اینکه خطای SVG backend نده و بتونیم PNG ذخیره کنیم
matplotlib.use("Agg")

from schemdraw import Drawing
import schemdraw.elements as elm


def render_schematic(components, save_path="schematic.png"):
    # show=False یعنی پنجره‌ی گرافیکی باز نکنه (برای سرور مناسبه)
    d = Drawing(show=False)

    for c in components:
        # انتظار داریم از مدل JSON به این شکل بیاد:
        # { "type": "Resistor", "name": "R1", "nodes": ["in","out"], "value": "1k" }
        t = str(c.get("type", "")).lower()
        name = str(c.get("name", ""))
        value = str(c.get("value", ""))
        label = f"{name}\n{value}" if value else name

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
            # اگر نوعش رو نشناختیم، حداقل یه نقطه با لیبل بذاریم
            d.add(elm.Dot().label(name))

        # هر المان رو با یه خط به بعدی وصل می‌کنیم (فعلاً سری ساده)
        d.add(elm.Line().right())

    # رندر شکل روی backend رستری (Agg)
    d.draw()
    # ذخیره‌ی شکل به صورت PNG (پسوند از save_path فهمیده می‌شه)
    d.save(save_path)

    return save_path

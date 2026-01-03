SYSTEM_PROMPT = """شما یک تولیدکننده کد برای مدارهای الکتریکی هستید.
کاربر توضیح یک مدار الکتریکی را به شما می‌دهد و شما باید سه خروجی تولید کنید:

1. کد پایتون کامل برای رسم نمودار مدار با matplotlib
2. کد SPICE netlist ساده و استاندارد برای شبیه‌سازی
3. لیست JSON المان‌های مدار

کد پایتون شما باید:
- از matplotlib و matplotlib.patches استفاده کند
- یک تابع اصلی به نام `draw_circuit(ax)` داشته باشد که یک matplotlib axes را به عنوان ورودی می‌گیرد
- المان‌های مدار را به درستی رسم کند (مقاومت، خازن، سلف، منبع ولتاژ، منبع جریان، دیود، ترانزیستور، op-amp و غیره)
- سیم‌ها و اتصالات را رسم کند
- برچسب‌ها و مقادیر المان‌ها را نمایش دهد

**کدهای دقیق برای رسم المان‌ها (باید از این کدها استفاده کنید):**

**1. مقاومت (Resistor):**
```python
def draw_resistor(ax, x, y, width=0.6, height=0.2, label='R', value=''):
    # رسم خط زیگزاگ مقاومت
    zigzag_x = [x, x+width*0.2, x+width*0.2, x+width*0.4, x+width*0.4, x+width*0.6, x+width*0.6, x+width*0.8, x+width*0.8, x+width]   
    zigzag_y = [y+height/2, y+height/2, y+height, y+height, y, y, y+height, y+height, y+height/2, y+height/2]
    ax.plot(zigzag_x, zigzag_y, 'k-', linewidth=2)
    # خطوط اتصال
    ax.plot([x-0.2, x], [y+height/2, y+height/2], 'k-', linewidth=2)
    ax.plot([x+width, x+width+0.2], [y+height/2, y+height/2], 'k-', linewidth=2)
    # برچسب
    if value:
        ax.text(x+width/2, y+height+0.15, f'{label}\n{value}', fontsize=9, ha='center', va='bottom')
    else:
        ax.text(x+width/2, y+height+0.15, label, fontsize=9, ha='center', va='bottom')
```

**2. دیود (Diode):**
```python
def draw_diode(ax, x, y, width=0.4, height=0.3, label='D', value='', reverse=False):
    # مثلث دیود
    if reverse:
        triangle = patches.Polygon([(x, y), (x, y+height), (x+width*0.6, y+height/2)],
                                   closed=True, edgecolor='black', facecolor='white', linewidth=2)
        bar_x = x - width*0.2
    else:
        triangle = patches.Polygon([(x, y+height/2), (x+width*0.6, y), (x+width*0.6, y+height)],
                                   closed=True, edgecolor='black', facecolor='white', linewidth=2)
        bar_x = x + width*0.6
    ax.add_patch(triangle)
    # خط عمودی (کاتد)
    ax.plot([bar_x, bar_x], [y, y+height], 'k-', linewidth=2)
    # خطوط اتصال
    if reverse:
        ax.plot([x-0.2, x], [y+height/2, y+height/2], 'k-', linewidth=2)
        ax.plot([bar_x, bar_x-0.2], [y+height/2, y+height/2], 'k-', linewidth=2)
    else:
        ax.plot([x-0.2, x], [y+height/2, y+height/2], 'k-', linewidth=2)
        ax.plot([bar_x, bar_x+0.2], [y+height/2, y+height/2], 'k-', linewidth=2)
    # برچسب
    if value:
        ax.text(x+width/2, y+height+0.15, f'{label}\n{value}', fontsize=9, ha='center', va='bottom')
    else:
        ax.text(x+width/2, y+height+0.15, label, fontsize=9, ha='center', va='bottom')
```

**3. ترانزیستور NPN (BJT NPN):**
```python
def draw_transistor_npn(ax, x, y, size=0.4, label='Q', value=''):
    # دایره ترانزیستور
    circle = patches.Circle((x, y), size, fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(circle)
    # خط عمودی مرکزی
    ax.plot([x, x], [y-size, y+size], 'k-', linewidth=2)
    # پایه Base (چپ)
    ax.plot([x-size, x], [y, y], 'k-', linewidth=2)
    ax.text(x-size-0.15, y, 'B', fontsize=8, ha='right', va='center')
    # پایه Collector (بالا راست)
    collector_x = x + size * 0.707
    collector_y = y - size * 0.707
    ax.plot([x, collector_x], [y-size, collector_y], 'k-', linewidth=2)
    ax.plot([collector_x, collector_x+0.2], [collector_y, collector_y], 'k-', linewidth=2)
    ax.text(collector_x+0.25, collector_y, 'C', fontsize=8, ha='left', va='center')
    # پایه Emitter (پایین راست) با فلش
    emitter_x = x + size * 0.707
    emitter_y = y + size * 0.707
    ax.plot([x, emitter_x], [y+size, emitter_y], 'k-', linewidth=2)
    ax.plot([emitter_x, emitter_x+0.2], [emitter_y, emitter_y], 'k-', linewidth=2)
    # فلش روی Emitter
    arrow = patches.FancyArrowPatch((emitter_x+0.1, emitter_y), (emitter_x+0.2, emitter_y),
                                   arrowstyle='->', mutation_scale=15, linewidth=2, color='black')
    ax.add_patch(arrow)
    ax.text(emitter_x+0.25, emitter_y, 'E', fontsize=8, ha='left', va='center')
    # برچسب
    if value:
        ax.text(x, y-size-0.2, f'{label}\n{value}', fontsize=9, ha='center', va='top')
    else:
        ax.text(x, y-size-0.2, label, fontsize=9, ha='center', va='top')
```

**4. مولد ولتاژ DC (Voltage Source):**
```python
def draw_voltage_source(ax, x, y, width=0.3, height=0.4, label='V', value='', reverse=False):
    # خط بلند (مثبت)
    long_line_y = y + height*0.3 if reverse else y
    ax.plot([x, x], [long_line_y, long_line_y+height*0.4], 'k-', linewidth=3)
    # خط کوتاه (منفی)
    short_line_y = y if reverse else y + height*0.3
    ax.plot([x, x], [short_line_y, short_line_y+height*0.2], 'k-', linewidth=3)
    # خطوط اتصال
    ax.plot([x-0.2, x], [y+height/2, y+height/2], 'k-', linewidth=2)
    ax.plot([x, x+0.2], [y+height/2, y+height/2], 'k-', linewidth=2)
    # علامت + و -
    if not reverse:
        ax.text(x-0.1, long_line_y+height*0.2, '+', fontsize=12, ha='center', va='center', weight='bold')
        ax.text(x-0.1, short_line_y+height*0.1, '-', fontsize=12, ha='center', va='center', weight='bold')
    else:
        ax.text(x-0.1, long_line_y+height*0.2, '-', fontsize=12, ha='center', va='center', weight='bold')
        ax.text(x-0.1, short_line_y+height*0.1, '+', fontsize=12, ha='center', va='center', weight='bold')
    # برچسب
    if value:
        ax.text(x+0.25, y+height/2, f'{label}\n{value}', fontsize=9, ha='left', va='center')
    else:
        ax.text(x+0.25, y+height/2, label, fontsize=9, ha='left', va='center')
```

**5. خازن (Capacitor):**
```python
def draw_capacitor(ax, x, y, width=0.2, height=0.4, label='C', value=''):
    # دو خط عمودی موازی
    gap = width * 0.3
    ax.plot([x-gap/2, x-gap/2], [y, y+height], 'k-', linewidth=3)
    ax.plot([x+gap/2, x+gap/2], [y, y+height], 'k-', linewidth=3)
    # خطوط اتصال
    ax.plot([x-0.2, x-gap/2], [y+height/2, y+height/2], 'k-', linewidth=2)
    ax.plot([x+gap/2, x+0.2], [y+height/2, y+height/2], 'k-', linewidth=2)
    # برچسب
    if value:
        ax.text(x, y+height+0.15, f'{label}\n{value}', fontsize=9, ha='center', va='bottom')
    else:
        ax.text(x, y+height+0.15, label, fontsize=9, ha='center', va='bottom')
```

**مهم: هنگام رسم مدار، حتماً از توابع بالا استفاده کنید. فاصله بین المان‌ها را زیاد کنید (حداقل 1.5 واحد بین مراکز المان‌ها).**       

فرمت پاسخ:
شما باید پاسخ خود را به صورت یک JSON object برگردانید با فیلدهای زیر:
{
  "pythonCode": "کد پایتون در بلوک ```python",
  "spice": "کد SPICE ساده و استاندارد با .title و .end",
  "components": [{"ref": "R1", "type": "R", "value": "1k", "nodes": ["n1", "n2"]}, ...]
}

مثال کد پایتون کامل:
```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# تعریف توابع رسم المان‌ها (از کدهای بالا استفاده کنید)

def draw_circuit(ax):
    # رسم المان‌ها با استفاده از توابع تعریف شده
    # مثال: draw_resistor(ax, x=1, y=1, label='R1', value='1k')
    # مثال: draw_diode(ax, x=2.5, y=1, label='D1')
    # مثال: draw_transistor_npn(ax, x=4, y=1, label='Q1')
    # مثال: draw_voltage_source(ax, x=0, y=1, label='V1', value='5V')
    # مثال: draw_capacitor(ax, x=5.5, y=1, label='C1', value='10uF')

    # اتصال المان‌ها با خطوط
    # ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_xlim(-1, 10)
    ax.set_ylim(-1, 3)
```

کد SPICE باید ساده و استاندارد باشد. از فرمت زیر استفاده کنید:
.title Circuit Description
V1 n1 0 5
R1 n1 n2 1k
R2 n1 n3 1k
.end

مهم: اگر نمی‌توانید JSON تولید کنید، حداقل کد پایتون را در بلوک ```python برگردانید.
کد پایتون باید کامل و قابل اجرا باشد و یک تابع `draw_circuit(ax)` داشته باشد.
حتماً از توابع رسم المان‌های بالا استفاده کنید و فاصله بین المان‌ها را زیاد کنید.

"""

# print(SYSTEM_PROMPT)


import requests

API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# SYSTEM_PROMPT = """You are an electrical engineer specialized in circuit simulation.
# Your only task is to convert the user's description into a valid NgSpice netlist.
# Do not include any explanation, comment, or text other than the NgSpice code.

# Rules:
# - Always output pure NgSpice syntax, compatible with ngspice.
# - Use standard component naming conventions: V for voltage sources, I for current sources, R for resistors, C for capacitors, L for inductors, Q for BJTs, D for diodes, M for MOSFETs, J for JFETs, U or X for op-amps, etc.
# - Assume node 0 is ground.
# - Units must follow ngspice syntax (e.g., 5k, 10uF, 1mH, 180V).
# - If unclear, make reasonable engineering assumptions to produce a valid and runnable netlist.
# - Do not output markdown formatting, code blocks, or extra explanations.
# - Node names should be numbered: 0 for ground, then 1, 2, 3, etc.

# Example:
# User: "یک منبع 180 ولتی با دو مقاومت 30 و 5 اهم سری"
# Output:
# V1 1 0 180V
# R1 1 2 30
# R2 2 0 5
# """

# ═══════════════════════════════════════════════════════════════
# توابع تولید کد Spice
# ═══════════════════════════════════════════════════════════════
def generate_spice_code(prompt: str, model: str = "mistralai/mistral-7b-instruct:free") -> str:
    """تولید کد SPICE از توضیحات"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
    }

    resp = requests.post(API_URL, json=data, headers=headers)
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"].replace("<s>", "")

# res = generate_spice_code("یک فیلتر RC پایین‌گذر با مقاومت 10k و خازن 10nF بساز")
# print(res)
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
from allauth.account.signals import user_signed_up
from django.db import models
import os
import json
import time
import requests
import re
import io
import sys
import base64
import matplotlib
matplotlib.use('Agg')  # استفاده از backend بدون GUI
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from .models import ChatSession, ChatMessage, UserProfile, Review
from django.contrib.auth.models import User

# Chat history is now stored in database using Django models
# No need for file-based session storage

# اطمینان از اینکه stdout به UTF-8 تنظیم شده
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except AttributeError:
    # اگر stdout قبلاً wrapper شده باشد
    pass

def render_python_code_to_image(python_code):
    """رندر کردن کد پایتون matplotlib به تصویر base64"""
    try:
        import numpy as np
        import matplotlib.patches as patches
        import re

        # پاک کردن plt.show() و سایر دستورات نمایش از کد
        python_code = re.sub(r'plt\.show\(\)', '', python_code)
        python_code = re.sub(r'plt\.show\(\s*\)', '', python_code)

        # پاک کردن markdown code blocks اگر وجود داشته باشد
        python_code = re.sub(r'```\w*\n?', '', python_code)
        python_code = re.sub(r'```', '', python_code)

        # پاک کردن کاراکترهای غیر ASCII از کد
        python_code = ''.join(c for c in python_code if ord(c) < 128)

        # اصلاح مشکلات syntax رایج در کد matplotlib
        # جایگزینی patterns مشکل‌ساز
        python_code = python_code.replace('\\k-', "'k-'")
        python_code = python_code.replace('k-\\\\', "'k-'")
        python_code = python_code.replace('k-\\\\\\\\', "'k-'")  # برای موارد با 4 backslash
        # پاک کردن backslashهای اضافه در انتهای خط
        lines = python_code.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.rstrip()
            if line.endswith('\\\\'):
                line = line[:-2]  # حذف 2 backslash از انتها
            cleaned_lines.append(line)
        python_code = '\n'.join(cleaned_lines)
        # پاک کردن backslashهای اضافه
        python_code = python_code.replace('\\\\', '\\')
        # پاک کردن trailing backslashes
        lines = python_code.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.rstrip()
            if line.endswith('\\\\'):
                line = line[:-1]
            cleaned_lines.append(line)
        python_code = '\n'.join(cleaned_lines)

        # ایجاد یک namespace جداگانه برای اجرای کد
        namespace = {
            'plt': plt,
            'matplotlib': matplotlib,
            'np': np,
            'patches': patches,
            '__builtins__': __builtins__,
        }

        # بستن تمام figureهای قبلی
        plt.close('all')

        # اجرای کد پایتون
        try:
            # چک کردن syntax قبل از اجرا
            compile(python_code, '<string>', 'exec')
        except SyntaxError as syntax_error:
            print("Syntax error in code:", str(syntax_error))
            # اگر syntax error دارد، تصویر تولید نکن
            return None

        try:
            exec(python_code, namespace)
        except Exception as exec_error:
            print("Error executing Python code:", str(exec_error))
            raise exec_error

        # گرفتن figure فعلی
        fig = plt.gcf()

        if fig is None or len(fig.axes) == 0:
            plt.close('all')
            return None

        # تبدیل به تصویر
        canvas = FigureCanvasAgg(fig)
        buf = io.BytesIO()
        canvas.print_png(buf)
        buf.seek(0)

        # تبدیل به base64
        image_data = buf.read()
        image_base64 = base64.b64encode(image_data).decode('ascii')

        # بستن figure برای آزاد کردن حافظه
        plt.close(fig)
        plt.close('all')

        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        print("Error rendering Python code:", str(e))
        import traceback
        traceback.print_exc()
        plt.close('all')
        return None

SYSTEM_PROMPT = (
    "شما یک تولیدکننده کد برای مدارهای الکتریکی هستید.\n"
    "کاربر توضیح یک مدار الکتریکی را به شما می‌دهد و شما باید سه خروجی تولید کنید:\n\n"
    "1. کد پایتون کامل برای رسم نمودار مدار با matplotlib\n"
    "2. کد SPICE netlist برای شبیه‌سازی\n"
    "3. لیست JSON المان‌های مدار\n\n"
    "کد پایتون شما باید:\n"
    "- از matplotlib و matplotlib.patches استفاده کند\n"
    "- یک تابع اصلی به نام `draw_circuit(ax)` داشته باشد که یک matplotlib axes را به عنوان ورودی می‌گیرد\n"
    "- المان‌های مدار را به درستی رسم کند (مقاومت، خازن، سلف، منبع ولتاژ، منبع جریان، دیود، ترانزیستور، op-amp و غیره)\n"
    "- سیم‌ها و اتصالات را رسم کند\n"
    "- برچسب‌ها و مقادیر المان‌ها را نمایش دهد\n\n"
    "**کدهای دقیق برای رسم المان‌ها (باید از این کدها استفاده کنید):**\n\n"
    "**1. مقاومت (Resistor):**\n"
    "```python\n"
    "def draw_resistor(ax, x, y, width=0.6, height=0.2, label='R', value=''):\n"
    "    # رسم خط زیگزاگ مقاومت\n"
    "    zigzag_x = [x, x+width*0.2, x+width*0.2, x+width*0.4, x+width*0.4, x+width*0.6, x+width*0.6, x+width*0.8, x+width*0.8, x+width]\n"
    "    zigzag_y = [y+height/2, y+height/2, y+height, y+height, y, y, y+height, y+height, y+height/2, y+height/2]\n"
    "    ax.plot(zigzag_x, zigzag_y, 'k-', linewidth=2)\n"
    "    # خطوط اتصال\n"
    "    ax.plot([x-0.2, x], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "    ax.plot([x+width, x+width+0.2], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "    # برچسب\n"
    "    if value:\n"
    "        ax.text(x+width/2, y+height+0.15, f'{label}\\n{value}', fontsize=9, ha='center', va='bottom')\n"
    "    else:\n"
    "        ax.text(x+width/2, y+height+0.15, label, fontsize=9, ha='center', va='bottom')\n"
    "```\n\n"
    "**2. دیود (Diode):**\n"
    "```python\n"
    "def draw_diode(ax, x, y, width=0.4, height=0.3, label='D', value='', reverse=False):\n"
    "    # مثلث دیود\n"
    "    if reverse:\n"
    "        triangle = patches.Polygon([(x, y), (x, y+height), (x+width*0.6, y+height/2)], \n"
    "                                   closed=True, edgecolor='black', facecolor='white', linewidth=2)\n"
    "        bar_x = x - width*0.2\n"
    "    else:\n"
    "        triangle = patches.Polygon([(x, y+height/2), (x+width*0.6, y), (x+width*0.6, y+height)], \n"
    "                                   closed=True, edgecolor='black', facecolor='white', linewidth=2)\n"
    "        bar_x = x + width*0.6\n"
    "    ax.add_patch(triangle)\n"
    "    # خط عمودی (کاتد)\n"
    "    ax.plot([bar_x, bar_x], [y, y+height], 'k-', linewidth=2)\n"
    "    # خطوط اتصال\n"
    "    if reverse:\n"
    "        ax.plot([x-0.2, x], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "        ax.plot([bar_x, bar_x-0.2], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "    else:\n"
    "        ax.plot([x-0.2, x], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "        ax.plot([bar_x, bar_x+0.2], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "    # برچسب\n"
    "    if value:\n"
    "        ax.text(x+width/2, y+height+0.15, f'{label}\\n{value}', fontsize=9, ha='center', va='bottom')\n"
    "    else:\n"
    "        ax.text(x+width/2, y+height+0.15, label, fontsize=9, ha='center', va='bottom')\n"
    "```\n\n"
    "**3. ترانزیستور NPN (BJT NPN):**\n"
    "```python\n"
    "def draw_transistor_npn(ax, x, y, size=0.4, label='Q', value=''):\n"
    "    # دایره ترانزیستور\n"
    "    circle = patches.Circle((x, y), size, fill=False, edgecolor='black', linewidth=2)\n"
    "    ax.add_patch(circle)\n"
    "    # خط عمودی مرکزی\n"
    "    ax.plot([x, x], [y-size, y+size], 'k-', linewidth=2)\n"
    "    # پایه Base (چپ)\n"
    "    ax.plot([x-size, x], [y, y], 'k-', linewidth=2)\n"
    "    ax.text(x-size-0.15, y, 'B', fontsize=8, ha='right', va='center')\n"
    "    # پایه Collector (بالا راست)\n"
    "    collector_x = x + size * 0.707\n"
    "    collector_y = y - size * 0.707\n"
    "    ax.plot([x, collector_x], [y-size, collector_y], 'k-', linewidth=2)\n"
    "    ax.plot([collector_x, collector_x+0.2], [collector_y, collector_y], 'k-', linewidth=2)\n"
    "    ax.text(collector_x+0.25, collector_y, 'C', fontsize=8, ha='left', va='center')\n"
    "    # پایه Emitter (پایین راست) با فلش\n"
    "    emitter_x = x + size * 0.707\n"
    "    emitter_y = y + size * 0.707\n"
    "    ax.plot([x, emitter_x], [y+size, emitter_y], 'k-', linewidth=2)\n"
    "    ax.plot([emitter_x, emitter_x+0.2], [emitter_y, emitter_y], 'k-', linewidth=2)\n"
    "    # فلش روی Emitter\n"
    "    arrow = patches.FancyArrowPatch((emitter_x+0.1, emitter_y), (emitter_x+0.2, emitter_y),\n"
    "                                   arrowstyle='->', mutation_scale=15, linewidth=2, color='black')\n"
    "    ax.add_patch(arrow)\n"
    "    ax.text(emitter_x+0.25, emitter_y, 'E', fontsize=8, ha='left', va='center')\n"
    "    # برچسب\n"
    "    if value:\n"
    "        ax.text(x, y-size-0.2, f'{label}\\n{value}', fontsize=9, ha='center', va='top')\n"
    "    else:\n"
    "        ax.text(x, y-size-0.2, label, fontsize=9, ha='center', va='top')\n"
    "```\n\n"
    "**4. مولد ولتاژ DC (Voltage Source):**\n"
    "```python\n"
    "def draw_voltage_source(ax, x, y, width=0.3, height=0.4, label='V', value='', reverse=False):\n"
    "    # خط بلند (مثبت)\n"
    "    long_line_y = y + height*0.3 if reverse else y\n"
    "    ax.plot([x, x], [long_line_y, long_line_y+height*0.4], 'k-', linewidth=3)\n"
    "    # خط کوتاه (منفی)\n"
    "    short_line_y = y if reverse else y + height*0.3\n"
    "    ax.plot([x, x], [short_line_y, short_line_y+height*0.2], 'k-', linewidth=3)\n"
    "    # خطوط اتصال\n"
    "    ax.plot([x-0.2, x], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "    ax.plot([x, x+0.2], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "    # علامت + و -\n"
    "    if not reverse:\n"
    "        ax.text(x-0.1, long_line_y+height*0.2, '+', fontsize=12, ha='center', va='center', weight='bold')\n"
    "        ax.text(x-0.1, short_line_y+height*0.1, '-', fontsize=12, ha='center', va='center', weight='bold')\n"
    "    else:\n"
    "        ax.text(x-0.1, long_line_y+height*0.2, '-', fontsize=12, ha='center', va='center', weight='bold')\n"
    "        ax.text(x-0.1, short_line_y+height*0.1, '+', fontsize=12, ha='center', va='center', weight='bold')\n"
    "    # برچسب\n"
    "    if value:\n"
    "        ax.text(x+0.25, y+height/2, f'{label}\\n{value}', fontsize=9, ha='left', va='center')\n"
    "    else:\n"
    "        ax.text(x+0.25, y+height/2, label, fontsize=9, ha='left', va='center')\n"
    "```\n\n"
    "**5. خازن (Capacitor):**\n"
    "```python\n"
    "def draw_capacitor(ax, x, y, width=0.2, height=0.4, label='C', value=''):\n"
    "    # دو خط عمودی موازی\n"
    "    gap = width * 0.3\n"
    "    ax.plot([x-gap/2, x-gap/2], [y, y+height], 'k-', linewidth=3)\n"
    "    ax.plot([x+gap/2, x+gap/2], [y, y+height], 'k-', linewidth=3)\n"
    "    # خطوط اتصال\n"
    "    ax.plot([x-0.2, x-gap/2], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "    ax.plot([x+gap/2, x+0.2], [y+height/2, y+height/2], 'k-', linewidth=2)\n"
    "    # برچسب\n"
    "    if value:\n"
    "        ax.text(x, y+height+0.15, f'{label}\\n{value}', fontsize=9, ha='center', va='bottom')\n"
    "    else:\n"
    "        ax.text(x, y+height+0.15, label, fontsize=9, ha='center', va='bottom')\n"
    "```\n\n"
    "**مهم: هنگام رسم مدار، حتماً از توابع بالا استفاده کنید. فاصله بین المان‌ها را زیاد کنید (حداقل 1.5 واحد بین مراکز المان‌ها).**\n\n"
    "فرمت پاسخ:\n"
    "شما باید پاسخ خود را به صورت یک JSON object برگردانید با فیلدهای زیر:\n"
    "{\n"
    '  "pythonCode": "کد پایتون در بلوک ```python",\n'
    '  "spice": "کد SPICE netlist کامل",\n'
    '  "components": [{"ref": "R1", "type": "R", "value": "1k", "nodes": ["n1", "n2"]}, ...]\n'
    "}\n\n"
    "مثال کد پایتون کامل:\n"
    "```python\n"
    "import matplotlib.pyplot as plt\n"
    "import matplotlib.patches as patches\n"
    "import numpy as np\n\n"
    "# تعریف توابع رسم المان‌ها (از کدهای بالا استفاده کنید)\n\n"
    "def draw_circuit(ax):\n"
    "    # رسم المان‌ها با استفاده از توابع تعریف شده\n"
    "    # مثال: draw_resistor(ax, x=1, y=1, label='R1', value='1k')\n"
    "    # مثال: draw_diode(ax, x=2.5, y=1, label='D1')\n"
    "    # مثال: draw_transistor_npn(ax, x=4, y=1, label='Q1')\n"
    "    # مثال: draw_voltage_source(ax, x=0, y=1, label='V1', value='5V')\n"
    "    # مثال: draw_capacitor(ax, x=5.5, y=1, label='C1', value='10uF')\n"
    "    \n"
    "    # اتصال المان‌ها با خطوط\n"
    "    # ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2)\n"
    "    \n"
    "    ax.set_aspect('equal')\n"
    "    ax.axis('off')\n"
    "    ax.set_xlim(-1, 10)\n"
    "    ax.set_ylim(-1, 3)\n"
    "```\n\n"
    "مثال SPICE:\n"
    ".title Circuit Description\n"
    "V1 n1 0 5\n"
    "R1 n1 n2 1k\n"
    ".end\n\n"
    "مهم: اگر نمی‌توانید JSON تولید کنید، حداقل کد پایتون را در بلوک ```python برگردانید.\n"
    "کد پایتون باید کامل و قابل اجرا باشد و یک تابع `draw_circuit(ax)` داشته باشد.\n"
    "حتماً از توابع رسم المان‌های بالا استفاده کنید و فاصله بین المان‌ها را زیاد کنید.\n"
)

EDIT_PROMPT = (
    "شما یک ویرایشگر کد برای اصلاح مدار الکتریکی هستید.\n"
    "کاربر یک کد پایتون قبلی و یک درخواست اصلاح به شما می‌دهد.\n"
    "شما باید کد قبلی را بر اساس درخواست کاربر اصلاح کنید و همچنین SPICE و components را به‌روزرسانی کنید.\n\n"
    "قوانین مهم:\n"
    "1. کد اصلاح شده باید همچنان یک تابع `draw_circuit(ax)` داشته باشد\n"
    "2. فقط قسمت‌های مورد نیاز را تغییر دهید، بقیه کد را حفظ کنید\n"
    "3. از matplotlib و matplotlib.patches استفاده کنید\n"
    "4. کد باید کامل و قابل اجرا باشد\n"
    "5. تغییرات را به صورت واضح و منطقی اعمال کنید\n"
    "6. SPICE netlist و components list را نیز به‌روزرسانی کنید\n"
    "7. از توابع رسم المان‌های استاندارد استفاده کنید (draw_resistor, draw_diode, draw_transistor_npn, draw_voltage_source, draw_capacitor)\n"
    "8. فاصله بین المان‌ها را زیاد کنید (حداقل 1.5 واحد)\n\n"
    "فرمت پاسخ:\n"
    "اگر ممکن است، پاسخ را به صورت JSON با فیلدهای pythonCode، spice و components برگردانید.\n"
    "در غیر این صورت، حداقل کد پایتون اصلاح شده را در بلوک ```python برگردانید.\n"
    "حتماً از توابع رسم المان‌های استاندارد استفاده کنید.\n"
)

def clean_code_block(code: str) -> str:
    """حذف markdown code block markers از کد"""
    if not code:
        return ""

    code = code.strip()

    # حذف ```python از ابتدا
    if code.startswith("```python"):
        code = code[9:].strip()
    elif code.startswith("```"):
        code = code[3:].strip()

    # حذف ``` از انتها
    if code.endswith("```"):
        code = code[:-3].strip()

    # حذف "python" از ابتدا اگر هنوز وجود دارد
    if code.startswith("python"):
        code = code[6:].strip()

    return code

def remove_json_from_code(code: str) -> str:
    """حذف JSON از کد Python - فقط JSON object های کامل را حذف می‌کند"""
    if not code:
        return ""

    # اگر کد شامل def draw_circuit نیست، احتمالاً کد معتبر نیست
    if "def draw_circuit" not in code:
        return code

    # حذف JSON object های کامل از کل کد
    lines = code.split('\n')
    cleaned_lines = []
    in_json = False
    brace_count = 0
    json_start_line = -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        # اگر خط با { شروع می‌شود و شامل "components" یا "spice" است
        if stripped.startswith('{') and ('"components"' in stripped or '"spice"' in stripped):
            # بررسی اینکه آیا این بخشی از کد Python است (مثلاً در یک string یا comment)
            # اگر قبل از این خط def یا import وجود دارد، احتمالاً بخشی از کد Python است
            prev_text = '\n'.join(lines[:i])
            if 'def ' in prev_text or 'import ' in prev_text:
                # این بخشی از کد Python است، نگه دار
                cleaned_lines.append(line)
                continue

            # این یک JSON object است
            in_json = True
            json_start_line = i
            brace_count = stripped.count('{') - stripped.count('}')
            continue

        # اگر در حال رد کردن JSON هستیم
        if in_json:
            brace_count += stripped.count('{') - stripped.count('}')
            if brace_count <= 0:
                in_json = False
                json_start_line = -1
            continue

        # خط را نگه دار
        cleaned_lines.append(line)

    result = '\n'.join(cleaned_lines)

    # حذف خطوط خالی اضافی
    result = re.sub(r'\n\s*\n\s*\n+', '\n\n', result)

    return result.strip()

def is_valid_python_code(code: str) -> bool:
    """بررسی اینکه آیا رشته داده شده کد Python معتبر است"""
    if not code or not code.strip():
        return False

    code = code.strip()

    # اگر با { شروع شود، احتمالاً JSON است نه کد Python
    if code.startswith("{"):
        return False

    # اگر شامل def draw_circuit باشد، احتمالاً کد Python است
    if "def draw_circuit" in code:
        return True

    # اگر شامل import matplotlib یا import numpy باشد، احتمالاً کد Python است
    if "import matplotlib" in code or "import numpy" in code or "import numpy as np" in code:
        return True

    # اگر شامل plt. یا ax. باشد، احتمالاً کد Python است
    if "plt." in code or "ax." in code:
        return True

    return False

def extract_python_code(text: str) -> str:
    """استخراج کد پایتون از متن"""
    if not text:
        return ""

    # ابتدا تلاش برای استخراج از JSON
    try:
        # جستجوی JSON object که ممکن است pythonCode داشته باشد
        json_match = re.search(r"\{[\s\S]*\"pythonCode\"[\s\S]*\}", text)
        if json_match:
            data = json.loads(json_match.group(0))
            python_code = data.get("pythonCode", "")
            if python_code:
                # پاک‌سازی کد از markdown markers
                cleaned_code = clean_code_block(python_code)
                # حذف JSON از کد
                cleaned_code = remove_json_from_code(cleaned_code)
                # بررسی اینکه آیا کد معتبر است
                if is_valid_python_code(cleaned_code):
                    return cleaned_code
    except (json.JSONDecodeError, AttributeError, KeyError):
        pass

    # اگر JSON پیدا نشد، جستجوی بلوک کد با ```python
    code_match = re.search(r"```python\s*([\s\S]*?)```", text, re.IGNORECASE)
    if code_match:
        cleaned_code = clean_code_block(code_match.group(1))
        cleaned_code = remove_json_from_code(cleaned_code)
        if is_valid_python_code(cleaned_code):
            return cleaned_code

    # جستجوی بلوک کد با ```
    code_match = re.search(r"```\s*([\s\S]*?)```", text)
    if code_match:
        code = code_match.group(1).strip()
        cleaned_code = clean_code_block(code)
        cleaned_code = remove_json_from_code(cleaned_code)
        if is_valid_python_code(cleaned_code):
            return cleaned_code

    # اگر بلوک کد پیدا نشد، بررسی اینکه آیا کل متن کد Python است
    cleaned_text = clean_code_block(text)
    cleaned_text = remove_json_from_code(cleaned_text)
    if is_valid_python_code(cleaned_text):
        return cleaned_text

    return ""

def extract_spice_and_components(text: str) -> tuple:
    """استخراج SPICE code و components از پاسخ LLM"""
    spice_code = ""
    components = []

    if not text:
        return spice_code, components

    # ابتدا تلاش برای استخراج از JSON کامل
    try:
        # جستجوی JSON object که ممکن است spice و components داشته باشد
        json_match = re.search(r"\{[\s\S]*\"spice\"[\s\S]*\}", text)
        if json_match:
            data = json.loads(json_match.group(0))
            spice_code = data.get("spice", "")
            components = data.get("components", [])
            if spice_code or components:
                return spice_code, components
    except (json.JSONDecodeError, AttributeError, KeyError):
        pass

    # اگر JSON کامل پیدا نشد، تلاش برای استخراج SPICE از بلوک کد
    try:
        # جستجوی بلوک SPICE
        spice_match = re.search(r"```(?:spice|text)?\s*(\.title[\s\S]*?\.end)", text, re.IGNORECASE)
        if spice_match:
            spice_code = spice_match.group(1).strip()
        else:
            # جستجوی ساده‌تر برای SPICE
            spice_match = re.search(r"(\.title[\s\S]*?\.end)", text, re.IGNORECASE)
            if spice_match:
                spice_code = spice_match.group(1).strip()
    except Exception:
        pass

    # تلاش برای استخراج components از JSON جداگانه
    try:
        components_match = re.search(r"\"components\"\s*:\s*\[([\s\S]*?)\]", text)
        if components_match:
            components_str = "[" + components_match.group(1) + "]"
            components = json.loads(components_str)
    except (json.JSONDecodeError, AttributeError):
        pass

    return spice_code, components

def call_llm(prompt: str, llm_api_key: str, previous_code: str = None) -> dict:
    """فراخوانی OpenAI chat/completions با کلید مستقیم"""

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {llm_api_key}",
        "Content-Type": "application/json"
    }

    # اگر کد قبلی وجود دارد، از prompt ویرایش استفاده کن
    if previous_code and previous_code.strip():
        system_prompt = EDIT_PROMPT
        user_prompt = f"کد قبلی:\n```python\n{previous_code}\n```\n\nدرخواست کاربر برای اصلاح: {prompt}"
    else:
        system_prompt = SYSTEM_PROMPT
        user_prompt = prompt

    payload = {
        "model": "gpt-4o-mini",  # مدل پیش‌فرض
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    resp.raise_for_status()
    data = resp.json()

    llm_text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

    # ابتدا تلاش برای استخراج از JSON کامل
    python_code = ""
    spice_code = ""
    components = []

    try:
        # تلاش برای پارس کل پاسخ به عنوان JSON
        parsed_json = json.loads(llm_text)
        if isinstance(parsed_json, dict):
            python_code = parsed_json.get("pythonCode", "")
            spice_code = parsed_json.get("spice", "")
            components = parsed_json.get("components", [])
            # پاک‌سازی کد Python از markdown markers
            if python_code:
                python_code = clean_code_block(python_code)
                # حذف JSON از کد
                python_code = remove_json_from_code(python_code)
                # بررسی اینکه آیا کد معتبر است (نه JSON)
                if not is_valid_python_code(python_code):
                    python_code = ""  # اگر معتبر نبود، خالی کن
    except (json.JSONDecodeError, ValueError):
        # اگر JSON نبود، از توابع استخراج استفاده کن
        pass

    # اگر از JSON استخراج نشد، از توابع استخراج استفاده کن
    if not python_code:
        python_code = extract_python_code(llm_text)
    if not spice_code and not components:
        extracted_spice, extracted_components = extract_spice_and_components(llm_text)
        if extracted_spice:
            spice_code = extracted_spice
        if extracted_components:
            components = extracted_components

    return {
        "modelOutput": llm_text,
        "pythonCode": python_code,
        "spiceCode": spice_code,
        "components": components
    }

def call_llm_local(prompt: str, llm_base_url: str, llm_model: str, llm_api_key: str = "", previous_code: str = None) -> dict:
    """فراخوانی LLM محلی"""
    url = f"{llm_base_url.rstrip('/')}/v1/chat/completions"

    headers = {
        "Content-Type": "application/json"
    }
    if llm_api_key:
        headers["Authorization"] = f"Bearer {llm_api_key}"

    # اگر کد قبلی وجود دارد، از prompt ویرایش استفاده کن
    if previous_code and previous_code.strip():
        system_prompt = EDIT_PROMPT
        user_prompt = f"کد قبلی:\n```python\n{previous_code}\n```\n\nدرخواست کاربر برای اصلاح: {prompt}"
    else:
        system_prompt = SYSTEM_PROMPT
        user_prompt = prompt

    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=90)
    resp.raise_for_status()
    data = resp.json()

    llm_text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

    # ابتدا تلاش برای استخراج از JSON کامل
    python_code = ""
    spice_code = ""
    components = []

    try:
        # تلاش برای پارس کل پاسخ به عنوان JSON
        parsed_json = json.loads(llm_text)
        if isinstance(parsed_json, dict):
            python_code = parsed_json.get("pythonCode", "")
            spice_code = parsed_json.get("spice", "")
            components = parsed_json.get("components", [])
            # پاک‌سازی کد Python از markdown markers
            if python_code:
                python_code = clean_code_block(python_code)
                # حذف JSON از کد
                python_code = remove_json_from_code(python_code)
                # بررسی اینکه آیا کد معتبر است (نه JSON)
                if not is_valid_python_code(python_code):
                    python_code = ""  # اگر معتبر نبود، خالی کن
    except (json.JSONDecodeError, ValueError):
        # اگر JSON نبود، از توابع استخراج استفاده کن
        pass

    # اگر از JSON استخراج نشد، از توابع استخراج استفاده کن
    if not python_code:
        python_code = extract_python_code(llm_text)
    if not spice_code and not components:
        extracted_spice, extracted_components = extract_spice_and_components(llm_text)
        if extracted_spice:
            spice_code = extracted_spice
        if extracted_components:
            components = extracted_components

    return {
        "modelOutput": llm_text,
        "pythonCode": python_code,
        "spiceCode": spice_code,
        "components": components
    }


def landing(request):
    """نمایش صفحه لندینگ"""
    return render(request, 'landing.html')

def index(request):
    """نمایش UI صفحه اصلی چت"""
    # فرم‌های ورود و ثبت‌نام را به قالب بفرستید
    return render(request, 'index.html', {
        'login_form': AuthenticationForm(),
        'signup_form': UserCreationForm()
    })

@csrf_exempt
@login_required # فقط کاربران لاگین شده می‌توانند پیام ارسال کنند
def api_chat_message(request):
    if request.method != "POST":
        return JsonResponse({"error": "فقط POST مجاز است."}, status=405)
    try:
        data = json.loads(request.body.decode())
        user_message_text = data.get('message')
        session_id = data.get('sessionId', 'default') # در فرانت‌اند باید session_id واقعی ارسال شود

        # پیدا کردن یا ایجاد ChatSession
        if session_id == 'default':
            chat_session, created = ChatSession.objects.get_or_create(
                user=request.user,
                session_id=session_id,
                defaults={'display_name': 'چت جدید'}
            )
        else:
            chat_session, created = ChatSession.objects.get_or_create(
                user=request.user,
                session_id=session_id
            )
            # اگر سشن جدید ساخته شد، نام آن را تنظیم کنید
            if created:
                chat_session.display_name = user_message_text[:30] + '...' if len(user_message_text) > 30 else user_message_text
                chat_session.save()


        # ذخیره پیام کاربر
        ChatMessage.objects.create(
            session=chat_session,
            role='user',
            content_text=user_message_text
        )

        # به‌روزرسانی زمان آخرین پیام
        chat_session.last_message_time = time.time()
        chat_session.save()

        # اتصال به LLM و دریافت پاسخ واقعی
        llm_base_url = data.get('llmBaseUrl')
        llm_model = data.get('llmModel')
        llm_api_key = data.get('llmApiKey')

        # بررسی اینکه آیا API key از OpenAI است
        is_openai = llm_api_key.strip().startswith("sk-")

        try:
            if is_openai:
                # استفاده از تابع call_llm با کد قبلی (اگر وجود دارد)
                assistant_response_content = call_llm(user_message_text, llm_api_key)
            else:
                # استفاده از LLM محلی
                assistant_response_content = call_llm_local(user_message_text, llm_base_url, llm_model, llm_api_key)

            # اگر پاسخ خالی است یا ساختار صحیح ندارد، از پاسخ پیش‌فرض استفاده کن
            if not assistant_response_content or not isinstance(assistant_response_content, dict):
                assistant_response_content = {
                    "modelOutput": f"خطا در پردازش پاسخ LLM",
                    "pythonCode": "",
                    "spiceCode": "",
                    "components": [],
                    "imageBase64": None
                }

            # اگر کد پایتون وجود دارد، تصویر را تولید کن
            if assistant_response_content.get("pythonCode"):
                image_base64 = render_python_code_to_image(assistant_response_content["pythonCode"])
                assistant_response_content["imageBase64"] = image_base64

        except Exception as llm_error:
            # اگر اتصال به LLM شکست خورد، از پاسخ پیش‌فرض استفاده کن
            assistant_response_content = {
                "modelOutput": f"خطا در اتصال به LLM: {str(llm_error)}",
                "pythonCode": "",
                "spiceCode": "",
                "components": [],
                "imageBase64": None
            }

        # ذخیره پیام دستیار
        ChatMessage.objects.create(
            session=chat_session,
            role='assistant',
            content_json=assistant_response_content
        )

        # دوباره زمان آخرین پیام را به‌روزرسانی کنید
        chat_session.last_message_time = time.time()
        chat_session.save()

        return JsonResponse({"message": assistant_response_content})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@login_required # فقط کاربران لاگین شده می‌توانند تاریخچه چت خود را ببینند/حذف کنند
def api_chat_history(request, session_id):
    try:
        chat_session = ChatSession.objects.get(user=request.user, session_id=session_id)
    except ChatSession.DoesNotExist:
        return JsonResponse({"messages": [], "displayName": "چت جدید", "lastMessage": time.time()}, status=200)

    if request.method == 'GET':
        messages = chat_session.messages.order_by('id')
        formatted_messages = []
        for msg in messages:
            if msg.role == 'user':
                formatted_messages.append({"role": "user", "content": msg.content_text})
            else:
                formatted_messages.append({"role": "assistant", "content": msg.content_json})

        return JsonResponse({
            "messages": formatted_messages,
            "displayName": chat_session.display_name,
            "lastMessage": chat_session.last_message_time
        })
    elif request.method == 'DELETE':
        if session_id == 'default':
            # برای سشن دیفالت، پیام‌ها را پاک می‌کنیم نه خود سشن را
            chat_session.messages.all().delete()
            chat_session.display_name = 'چت جدید'
            chat_session.last_message_time = time.time()
            chat_session.save()
            return JsonResponse({"success": True, "message": "Default chat history cleared."})
        else:
            chat_session.delete()
            return JsonResponse({"success": True, "message": "Session deleted."})
    return JsonResponse({"error": "متد نامعتبر."}, status=405)

@csrf_exempt
@login_required # فقط کاربران لاگین شده می‌توانند نام چت خود را تغییر دهند
def api_chat_rename(request, session_id):
    if request.method != "PUT":
        return JsonResponse({"success": False, "error": "فقط PUT مجاز است."}, status=405)
    
    try:
        chat_session = ChatSession.objects.get(user=request.user, session_id=session_id)
    except ChatSession.DoesNotExist:
        return JsonResponse({"success": False, "message": "Session not found."}, status=404)

    data = json.loads(request.body.decode())
    new_name = data.get('name')
    if not new_name:
        return JsonResponse({"success": False, "error": "نام جدید لازم است."}, status=400)
    
    chat_session.display_name = new_name
    chat_session.save()
    return JsonResponse({"success": True, "displayName": new_name})

@csrf_exempt
@login_required # فقط کاربران لاگین شده می‌توانند لیست جلسات چت خود را ببینند
def api_chat_sessions(request):
    if request.method != "GET":
        return JsonResponse({"error": "فقط GET مجاز است."}, status=405)
    
    sessions_db = ChatSession.objects.filter(user=request.user).order_by('-last_message_time')
    
    sessions_data = []
    for session in sessions_db:
        last_message_type = None
        if session.messages.exists():
            last_message_type = session.messages.last().role
        
        sessions_data.append({
            "sessionId": session.session_id,
            "displayName": session.display_name,
            "lastMessage": session.last_message_time,
            "lastMessageType": last_message_type
        })
    return JsonResponse({"sessions": sessions_data})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('index') # به صفحه اصلی چت هدایت شود
        else:
            # اگر فرم نامعتبر بود، ارورها را به قالب بفرستید
            return render(request, 'index.html', {'signup_form': form})
    else:
        form = UserCreationForm()
    return render(request, 'index.html', {'signup_form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index') # به صفحه اصلی چت هدایت شود
            else:
                # پیام خطا برای نام کاربری/رمز عبور اشتباه
                return render(request, 'index.html', {'login_form': form, 'show_login': True, 'error_message': 'نام کاربری یا رمز عبور اشتباه است.'})
        else:
            # اگر فرم نامعتبر بود، ارورها را به قالب بفرستید
            return render(request, 'index.html', {'login_form': form, 'show_login': True})
    else:
        form = AuthenticationForm()
    return render(request, 'index.html', {'login_form': form, 'show_login': True})
@login_required
def logout_view(request):
    logout(request)
    return redirect('landing')

# API Endpoints برای Google Sign-In
from django.views.decorators.http import require_POST
import google.auth.transport.requests
import google.oauth2.id_token

@require_POST
def google_client_id_api(request):
    """API برای دریافت Google Client ID"""
    client_id = os.getenv('GOOGLE_CLIENT_ID', '')
    return JsonResponse({'client_id': client_id})

@require_POST
def google_signin_api(request):
    """API برای پردازش Google Sign-In"""
    try:
        data = json.loads(request.body)
        credential = data.get('credential')
        action = data.get('action', 'login')

        if not credential:
            return JsonResponse({'error': 'Credential is required'}, status=400)

        # Verify the token
        try:
            id_info = google.oauth2.id_token.verify_oauth2_token(
                credential,
                google.auth.transport.requests.Request(),
                os.getenv('GOOGLE_CLIENT_ID')
            )
        except ValueError as e:
            return JsonResponse({'error': 'Invalid token'}, status=400)

        # Extract user information
        google_user_id = id_info['sub']
        email = id_info['email']
        name = id_info.get('name', '')
        given_name = id_info.get('given_name', '')
        family_name = id_info.get('family_name', '')
        picture = id_info.get('picture', '')

        # Check if user already exists with this email
        user = None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass

        # Check if there's a social account for this Google user
        social_account = None
        try:
            social_account = SocialAccount.objects.get(
                provider='google',
                uid=google_user_id
            )
            user = social_account.user
        except SocialAccount.DoesNotExist:
            pass

        if user:
            # User exists, log them in
            login(request, user)
            return JsonResponse({
                'success': True,
                'redirect_url': '/',
                'message': f'خوش آمدید {given_name}'
            })
        else:
            # User doesn't exist, create new user if action is signup
            if action == 'signup':
                # Create new user
                username = email.split('@')[0]
                # Make sure username is unique
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1

                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=given_name,
                    last_name=family_name,
                    is_active=True
                )

                # Create UserProfile
                UserProfile.objects.get_or_create(user=user)

                # Create SocialAccount
                social_account = SocialAccount.objects.create(
                    user=user,
                    provider='google',
                    uid=google_user_id,
                    extra_data={
                        'email': email,
                        'name': name,
                        'given_name': given_name,
                        'family_name': family_name,
                        'picture': picture
                    }
                )

                # Log the user in
                login(request, user)

                return JsonResponse({
                    'success': True,
                    'redirect_url': '/',
                    'message': f'حساب شما با موفقیت ایجاد شد. خوش آمدید {given_name}'
                })
            else:
                # User doesn't exist and action is login
                return JsonResponse({
                    'error': 'حساب کاربری یافت نشد. لطفاً ابتدا ثبت نام کنید.'
                }, status=404)

    except Exception as e:
        print(f"Google signin error: {e}")
        return JsonResponse({'error': 'خطا در پردازش ورود'}, status=500)

# Signal handler برای ایجاد UserProfile وقتی کاربر با social account ثبت نام می‌کند
from django.dispatch import receiver

@receiver(user_signed_up)
def create_user_profile_on_social_signup(request, user, **kwargs):
    """ایجاد UserProfile برای کاربرانی که با social account ثبت نام می‌کنند"""
    UserProfile.objects.get_or_create(user=user)

# ویوهای مرتبط با نظرات و امتیازدهی
def reviews_page(request):
    """صفحه اصلی نظرات و امتیازدهی - قابل دسترسی برای همه"""
    return render(request, 'reviews.html')

def reviews_list(request):
    """صفحه نمایش لیست نظرات کاربران"""
    reviews = Review.objects.filter(is_approved=True).order_by('-created_at')
    context = {
        'reviews': reviews,
    }
    return render(request, 'reviews_list.html', context)

def submit_review(request):
    """ثبت نظر و امتیاز جدید - برای کاربران لاگین کرده و مهمانان"""
    print(f"submit_review called: method={request.method}, user={request.user}")  # Debug log
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):
            return JsonResponse({'error': 'امتیاز باید بین 1 تا 5 باشد'}, status=400)

        # اگر کاربر لاگین کرده باشد
        if request.user.is_authenticated:
            guest_name = None
            guest_email = None
            selected_message_id = request.POST.get('chat_history_message')

            # بررسی اینکه آیا کاربر قبلاً نظر داده یا نه
            existing_review = Review.objects.filter(user=request.user).first()
            if existing_review:
                existing_review.rating = int(rating)
                existing_review.comment = comment
                if selected_message_id:
                    # ذخیره فقط message_id
                    try:
                        from .models import ChatMessage
                        message = ChatMessage.objects.get(
                            id=int(selected_message_id),
                            role='assistant',
                            session__user=request.user
                        )
                        existing_review.chat_history_message_id = message.id
                    except:
                        pass
                existing_review.is_approved = False  # نیاز به تأیید مجدد دارد
                existing_review.save()
                message = 'نظر شما بروزرسانی شد و منتظر تأیید مدیر است.'
            else:
                chat_history_message_id = None

                if selected_message_id:
                    # ذخیره فقط message_id
                    try:
                        from .models import ChatMessage
                        message = ChatMessage.objects.get(
                            id=int(selected_message_id),
                            role='assistant',
                            session__user=request.user
                        )
                        chat_history_message_id = message.id
                    except:
                        pass

                Review.objects.create(
                    user=request.user,
                    rating=int(rating),
                    comment=comment,
                    chat_history_message_id=chat_history_message_id,
                    is_approved=False
                )
                message = 'نظر شما ثبت شد و منتظر تأیید مدیر است.'
        else:
            # کاربر مهمان است
            guest_name = request.POST.get('guest_name', '').strip()
            guest_email = request.POST.get('guest_email', '').strip()

            if not guest_name:
                return JsonResponse({'error': 'لطفاً نام خود را وارد کنید'}, status=400)

            # بررسی اعتبار ایمیل اگر وارد شده
            if guest_email and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', guest_email):
                return JsonResponse({'error': 'ایمیل وارد شده معتبر نیست'}, status=400)

            Review.objects.create(
                rating=int(rating),
                comment=comment,
                guest_name=guest_name,
                guest_email=guest_email,
                is_approved=False
            )
            message = 'نظر شما ثبت شد و منتظر تأیید مدیر است.'

        return JsonResponse({'success': True, 'message': message})

    return JsonResponse({'error': 'متد درخواست نامعتبر است'}, status=405)

def reviews_stats(request):
    """آمار نظرات برای نمایش در لندینگ پیج"""
    total_reviews = Review.objects.filter(is_approved=True).count()
    avg_rating = Review.objects.filter(is_approved=True).aggregate(
        avg=models.Avg('rating')
    )['avg'] or 0

    rating_counts = {}
    rating_percentages = {}
    for i in range(1, 6):
        count = Review.objects.filter(is_approved=True, rating=i).count()
        rating_counts[i] = count
        rating_percentages[i] = round((count / total_reviews * 100), 1) if total_reviews > 0 else 0

    return JsonResponse({
        'total_reviews': total_reviews,
        'average_rating': round(avg_rating, 1),
        'rating_counts': rating_counts,
        'rating_percentages': rating_percentages
    })

def get_featured_reviews(request):
    """دریافت نظرات برجسته برای نمایش در لندینگ پیج"""
    # گرفتن 2 نظر تأیید شده اخیر
    reviews = Review.objects.filter(is_approved=True).order_by('-created_at')[:2]

    reviews_data = []
    for review in reviews:
        has_image = False
        if review.chat_history_message_id:
            try:
                # چک کردن اینکه پیام وجود دارد، قابل دسترسی است و کد پایتون دارد
                message = ChatMessage.objects.get(
                    id=review.chat_history_message_id,
                    role='assistant'
                )

                # چک کردن کد پایتون
                python_code = None
                if message.content_json and isinstance(message.content_json, dict):
                    python_code = message.content_json.get('pythonCode') or message.content_json.get('python_code')
                if not python_code and message.content_text:
                    if 'import matplotlib' in message.content_text or 'def draw_circuit' in message.content_text:
                        python_code = message.content_text

                has_image = bool(python_code)
            except ChatMessage.DoesNotExist:
                has_image = False

        reviews_data.append({
            'id': review.id,
            'author_name': review.author_name,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%Y-%m-%d'),
            'stars_display': review.stars_display,
            'user_type': 'کاربر ثبت‌شده' if review.user else 'مهمان',
            'has_image': has_image,
            'chat_history_message_id': review.chat_history_message_id
        })

    return JsonResponse({'reviews': reviews_data})

@login_required
def get_user_chat_history(request):
    """دریافت چت هیستوری کاربر برای انتخاب در نظرات - همه تصاویر رندر شده"""
    chat_sessions = ChatSession.objects.filter(user=request.user).order_by('-last_message_time')

    sessions_data = []
    for session in chat_sessions:
        # گرفتن همه پیام‌های assistant که تصویر دارند (یا می‌توانند رندر شوند)
        assistant_messages = ChatMessage.objects.filter(
            session=session,
            role='assistant'
        ).exclude(
            # پیام‌هایی که نه کد پایتون دارند نه تصویر رندر شده
            models.Q(content_json__isnull=True) &
            models.Q(content_text__isnull=True)
        )

        messages_with_images = []
        for message in assistant_messages:
            # چک کردن کد پایتون و تصویر
            python_code = None
            image_base64 = None

            if message.content_json and isinstance(message.content_json, dict):
                python_code = message.content_json.get('pythonCode') or message.content_json.get('python_code')
                image_base64 = message.content_json.get('imageBase64') or message.content_json.get('image_base64')

            if not python_code and message.content_text:
                # چک کردن آیا content_text کد پایتون است
                if 'import matplotlib' in message.content_text or 'def draw_circuit' in message.content_text:
                    python_code = message.content_text

            # اگر کد پایتون دارد یا تصویر رندر شده دارد
            if python_code or image_base64:
                # اگر تصویر وجود ندارد، سعی کن رندر کن
                if not image_base64 and python_code:
                    try:
                        image_base64 = render_python_code_to_image(python_code)
                        # ذخیره تصویر رندر شده برای استفاده‌های بعدی
                        if image_base64 and message.content_json:
                            message.content_json['imageBase64'] = image_base64
                            message.save(update_fields=['content_json'])
                    except Exception as e:
                        print(f"Error rendering image for message {message.id}: {e}")
                        continue

                if image_base64:  # فقط پیام‌هایی که تصویر دارند
                    messages_with_images.append({
                    'message_id': message.id,
                        'image_base64': image_base64,
                        'session_name': session.display_name,
                        'session_time': session.last_message_time,
                        'created_at': message.id  # برای ترتیب زمانی
                })

        if messages_with_images:
            # مرتب کردن بر اساس زمان ایجاد (جدیدترین اول)
            messages_with_images.sort(key=lambda x: x['created_at'], reverse=True)

            sessions_data.append({
                'session_id': session.session_id,
                'display_name': session.display_name,
                'last_message_time': session.last_message_time,
                'messages': messages_with_images
            })

    # مرتب کردن سشن‌ها بر اساس آخرین پیام
    sessions_data.sort(key=lambda x: x['last_message_time'], reverse=True)

    return JsonResponse({'chat_sessions': sessions_data})

@csrf_exempt
def render_python_code_api(request):
    """API برای رندر کردن کد پایتون به تصویر"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            python_code = data.get('python_code')
            
            if not python_code:
                return JsonResponse({'error': 'کد پایتون ارسال نشد'}, status=400)
            
            image_base64 = render_python_code_to_image(python_code)

            if image_base64:
                return JsonResponse({'image_base64': image_base64})
            else:
                return JsonResponse({'error': 'کد پایتون قابل رندر نیست - ممکن است نادرست باشد'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'متد درخواست نامعتبر است'}, status=405)

def get_chat_message_content(request, message_id):
    """دریافت محتوای یک پیام خاص از چت و رندر کردن کد پایتون به تصویر
    این API برای نمایش عمومی در نظرات استفاده می‌شود، پس نیاز به authentication ندارد
    اما فقط برای پیام‌های assistant که در نظرات استفاده شده‌اند"""
    try:
        # پیام باید حتماً از نوع assistant باشد
        message = ChatMessage.objects.get(
            id=int(message_id),
            role='assistant'
        )

        # بررسی اینکه آیا این پیام در یک نظر تأیید شده استفاده شده است
        from .models import Review
        review_exists = Review.objects.filter(
            chat_history_message_id=message_id,
            is_approved=True
        ).exists()
        if not review_exists:
            return JsonResponse({'error': 'دسترسی مجاز نیست'}, status=403)
        
        # گرفتن کد پایتون و تصویر از content_json
        python_code = None
        image_base64 = None

        if message.content_json and isinstance(message.content_json, dict):
            python_code = message.content_json.get('pythonCode') or message.content_json.get('python_code')
            image_base64 = message.content_json.get('imageBase64') or message.content_json.get('image_base64')

        if not python_code and message.content_text:
            # چک کردن آیا content_text کد پایتون است
            if 'import matplotlib' in message.content_text or 'def draw_circuit' in message.content_text:
                python_code = message.content_text

        # اگر کد پایتون داریم، سعی کنیم آن را رندر کنیم
        image_base64 = None
        if python_code:
            try:
                image_base64 = render_python_code_to_image(python_code)
            except Exception as e:
                print(f"Error rendering image for message {message_id}: {e}")
                image_base64 = None

        return JsonResponse({
            'python_code': python_code,
            'image_base64': image_base64,
            'session_name': message.session.display_name if message.session else None
        })
    except ChatMessage.DoesNotExist:
        return JsonResponse({'error': 'پیام یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

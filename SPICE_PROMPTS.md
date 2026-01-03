# پرامپت‌های مربوط به تولید و اصلاح کد SPICE

این فایل شامل تمام پرامپت‌هایی است که در پروژه برای تولید و اصلاح کد SPICE استفاده می‌شوند.

---

## 1. SPICE_PROMPT (از `as1/home/views.py`)

این پرامپت برای تولید کد SPICE به صورت مستقیم استفاده می‌شود:

```python
SPICE_PROMPT = """
You are an expert circuit designer.
Convert the user's description into a standard SPICE netlist.

Rules:
1. Return ONLY a JSON object. No markdown, no conversational text.
2. Structure:
{
  "spice": "Netlist lines separated by \\n (do not include .control blocks)",
  "components": [
     {"type": "Resistor", "name": "R1", "value": "1k", "nodes": ["1", "2"]},
     {"type": "Voltage Source", "name": "V1", "value": "DC 5", "nodes": ["1", "0"]}
  ]
}
3. Use '0' for ground.
""".strip()
```

**استفاده:** در تابع `call_openrouter_for_spice()` برای تولید مستقیم کد SPICE

---

## 2. SYSTEM_PROMPT (از `as1/home/views.py`)

این پرامپت سیستم اصلی برای تولید کد پایتون، SPICE و کامپوننت‌ها است. بخش‌های مربوط به SPICE:

```
شما یک تولیدکننده کد برای مدارهای الکتریکی هستید.
کاربر توضیح یک مدار الکتریکی را به شما می‌دهد و شما باید سه خروجی تولید کنید:

1. کد پایتون کامل برای رسم نمودار مدار با matplotlib
2. کد SPICE netlist ساده و استاندارد برای شبیه‌سازی
3. لیست JSON المان‌های مدار
```

**بخش مربوط به فرمت پاسخ:**

```
فرمت پاسخ:
شما باید پاسخ خود را به صورت یک JSON object برگردانید با فیلدهای زیر:
{
  "pythonCode": "کد پایتون در بلوک ```python",
  "spice": "کد SPICE ساده و استاندارد با .title و .end",
  "components": [{"ref": "R1", "type": "R", "value": "1k", "nodes": ["n1", "n2"]}, ...]
}
```

**بخش مربوط به فرمت SPICE:**

```
کد SPICE باید ساده و استاندارد باشد. از فرمت زیر استفاده کنید:
.title Circuit Description
V1 n1 0 5
R1 n1 n2 1k
R2 n1 n3 1k
.end
```

**استفاده:** در توابع `call_llm()` و `call_llm_local()` برای تولید کدهای مدار

---

## 3. EDIT_PROMPT (از `as1/home/views.py`)

این پرامپت برای ویرایش و اصلاح کدهای موجود استفاده می‌شود. بخش‌های مربوط به SPICE:

```
شما یک ویرایشگر کد برای اصلاح مدار الکتریکی هستید.
کاربر یک کد پایتون قبلی و یک درخواست اصلاح به شما می‌دهد.
شما باید کد قبلی را بر اساس درخواست کاربر اصلاح کنید و همچنین SPICE و components را به‌روزرسانی کنید.

قوانین مهم:
...
6. SPICE netlist و components list را نیز به‌روزرسانی کنید
...
```

**بخش مربوط به فرمت پاسخ:**

```
فرمت پاسخ:
اگر ممکن است، پاسخ را به صورت JSON با فیلدهای pythonCode، spice و components برگردانید.
```

**استفاده:** در توابع `call_llm()` و `call_llm_local()` زمانی که `previous_code` وجود دارد

---

## 4. PROMPT (از `r/api_client.py`)

این پرامپت ساده برای تولید کد SPICE:

```python
PROMPT = """
You are an expert analog/digital circuit designer.
User will describe a circuit in natural language.
Respond ONLY with a JSON object:
{
  "spice": "...",
  "components": [...]
}
""".strip()
```

**استفاده:** در ماژول `r/api_client.py` (احتمالاً استفاده نشده یا برای نسخه قدیمی)

---

## 5. SYSTEM_PROMPT (از `r/api_client.py`)

این پرامپت سیستم مشابه SYSTEM_PROMPT در views.py است اما در فرمت رشته با escape characters. بخش‌های مربوط به SPICE:

```
شما یک تولیدکننده کد برای مدارهای الکتریکی هستید.
کاربر توضیح یک مدار الکتریکی را به شما می‌دهد و شما باید سه خروجی تولید کنید:

1. کد پایتون کامل برای رسم نمودار مدار با matplotlib
2. کد SPICE netlist برای شبیه‌سازی
3. لیست JSON المان‌های مدار
```

**بخش مربوط به فرمت پاسخ:**

```
فرمت پاسخ:
شما باید پاسخ خود را به صورت یک JSON object برگردانید با فیلدهای زیر:
{
  "pythonCode": "کد پایتون در بلوک ```python",
  "spice": "کد SPICE netlist کامل",
  "components": [{"ref": "R1", "type": "R", "value": "1k", "nodes": ["n1", "n2"]}, ...]
}
```

**مثال SPICE:**

```
مثال SPICE:
.title Circuit Description
V1 n1 0 5
R1 n1 n2 1k
.end
```

**استفاده:** در ماژول `r/api_client.py` (احتمالاً برای نسخه قدیمی یا API جداگانه)

---

## خلاصه قوانین مهم برای کد SPICE

از تمام پرامپت‌ها، قوانین زیر استخراج می‌شوند:

1. **فرمت استاندارد:**
   - باید با `.title` شروع شود
   - باید با `.end` تمام شود
   - نباید بلوک `.control` داشته باشد (در SPICE_PROMPT)

2. **ساختار JSON:**
   - فیلد `spice`: رشته کد SPICE
   - فیلد `components`: لیست کامپوننت‌ها با ساختار `{"ref": "...", "type": "...", "value": "...", "nodes": [...]}`

3. **استفاده از گره 0 برای زمین:**
   - همیشه از `0` برای ground استفاده شود

4. **سادگی:**
   - کد باید ساده و استاندارد باشد
   - بدون دستورات شبیه‌سازی اضافی (`.tran`, `.op`, `.ac`, `.dc`)

5. **بروزرسانی در ویرایش:**
   - هنگام ویرایش کد، SPICE netlist و components list نیز باید به‌روزرسانی شوند

---

## توابع مرتبط

1. `call_openrouter_for_spice()` - استفاده از SPICE_PROMPT
2. `call_llm()` - استفاده از SYSTEM_PROMPT یا EDIT_PROMPT
3. `call_llm_local()` - استفاده از SYSTEM_PROMPT یا EDIT_PROMPT
4. `extract_spice_and_components()` - استخراج SPICE و components از پاسخ LLM
5. `generate_spice_api()` - API endpoint برای تولید کد SPICE


# AI Circuit Platform

پلتفرم متن‌باز طراحی، تحلیل و آموزش مدارهای الکتریکی/الکترونیکی با کمک هوش
مصنوعی. این نسخه بدون Django است و بر اساس یک **Circuit Intermediate
Representation (CIR)** مشترک ساخته شده که Backend و Frontend از طریق آن با
هم صحبت می‌کنند.

## ساختار پروژه

```
ai-circuit-platform/
├── core/                   # کتابخانه مشترک — قلب پروژه
│   ├── cir/                 # تعریف CIR (Circuit, Component, ComponentType)
│   ├── interfaces/          # کلاس‌های Abstract برای هر نوع ماژول
│   └── llm/                  # کلاینت LLM + پرامپت‌ها (فایل‌های جدا از کد)
├── services/                # پیاده‌سازی‌های concrete
│   ├── text_to_cir/          # متن -> CIR (با AI)
│   ├── cir_to_spice/          # CIR <-> SPICE (دترمینیستیک)
│   └── schematic/             # CIR -> تصویر شماتیک
├── api/
│   └── main.py                # FastAPI app
├── frontend/                # ویرایشگر شماتیک + چت هوشمند (React + Vite)
│   └── src/
│       ├── CircuitBuilder.jsx  # رابط کاربری اصلی
│       └── lib/
│           ├── cir.js            # adapter: مدل UI <-> CIR
│           └── api.js            # کلاینت backend
└── tests/                   # تست‌های pytest (بخش‌های دترمینیستیک)
```

## پیش‌نیازها

- Python 3.11+
- Node.js 20+
- یک API key سازگار با OpenAI (مثلاً از [OpenRouter](https://openrouter.ai))

---

## روش ۱: اجرا با Docker (پیشنهادی)

```bash
cp .env.example .env
# مقدار LLM_API_KEY را در .env تنظیم کنید

docker compose up --build
```

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173

---

## روش ۲: اجرای محلی (بدون Docker)

### ۱. Backend

```bash
python -m venv .venv
source .venv/bin/activate        # ویندوز: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# LLM_API_KEY, LLM_BASE_URL, LLM_MODEL را در .env تنظیم کنید

uvicorn api.main:app --reload
```

تست بخش‌های دترمینیستیک (بدون نیاز به API key):
```bash
pytest
```

### ۲. Frontend

در یک ترمینال جدید:

```bash
cd frontend
npm install

cp .env.example .env
# در صورت نیاز VITE_API_BASE_URL را تغییر دهید (پیش‌فرض: http://localhost:8000)

npm run dev
```

سپس مرورگر را باز کنید: **http://localhost:5173**

---

## نحوه کار

۱. در پنل «دستیار هوشمند» (سمت راست)، مدار خود را به فارسی توضیح دهید — مثلاً:
> یک فیلتر پایین‌گذر RLC با منبع ولتاژ ۵ ولت

۲. درخواست به `/api/text-to-cir` ارسال می‌شود؛ مدل AI یک CIR معتبر برمی‌گرداند.

۳. Frontend با استفاده از `cirToUiModel` (در `frontend/src/lib/cir.js`) این CIR
را به مدل داخلی ویرایشگر تبدیل و روی کانواس رسم می‌کند.

۴. هر بار که مدار را (به‌صورت دستی یا با AI) تغییر دهید، Frontend با
`uiModelToCIR` آن را به CIR تبدیل کرده و برای تولید نت‌لیست به
`/api/cir-to-spice` می‌فرستد — نتلیست در پنل پایین (Netlist) نمایش داده می‌شود.

## محدودیت‌های فعلی (نسخه اول adapter)

- ویرایشگر فعلی فقط از المان‌های دوپایه پشتیبانی می‌کند: مقاومت، خازن، سلف،
  دیود، منبع ولتاژ. اگر AI مداری با ترانزیستور/opamp/IC تولید کند، آن المان
  نادیده گرفته می‌شود و هشدار در چت نمایش داده می‌شود.
- هر پیام جدید در چت، **کل مدار را از نو می‌سازد** (جایگزین می‌کند)، نه اضافه
  می‌کند. ویژگی «این مدار را بهبود بده» (با حفظ مدار فعلی) در فاز بعدی
  (Circuit Improver agent) اضافه می‌شود.
- چیدمان (layout) مدارهای تولیدشده توسط AI ساده و خطی است؛ برای مدارهای
  پیچیده ممکن است سیم‌ها روی هم بیفتند — قطعات قابل drag-and-drop هستند.

## تحلیل مدار با PySpice/ngspice

دکمه «تحلیل مدار» در بالای صفحه، آنالیز DC operating point (ولتاژ هر گره و
جریان شاخه‌ها) را از طریق `/api/analyze` اجرا می‌کند.

⚠️ **نکته مهم:** PySpice برای اجرای واقعی شبیه‌سازی به باینری **ngspice**
نیاز دارد (نه فقط پکیج pip).

- **با Docker:** از قبل در `Dockerfile` نصب شده؛ کاری لازم نیست.
- **اجرای محلی (بدون Docker) روی ویندوز:** باید ngspice را جداگانه نصب کنید:
  از https://ngspice.sourceforge.io دانلود کنید، یا با conda:
  ```cmd
  conda install -c conda-forge ngspice
  ```
  اگر ngspice نصب نباشد، دکمه «تحلیل مدار» خطای واضحی نمایش می‌دهد (نه crash).

## نقشه راه

- ~~`services/spice_analyzer/` — تحلیل‌گر PySpice~~ ✅ انجام شد (DC operating point)
- `core/interfaces/circuit_improver.py` (interface تعریف شده، پیاده‌سازی باقی‌مانده) —
  عامل AI برای بهبود مدار بر اساس هدف کاربر (مثلاً کاهش نویز)
- پشتیبانی از ترانزیستور/opamp در adapter و سمبل‌های UI
- آنالیزهای AC/Transient (علاوه بر DC operating point فعلی)
- ماژول‌های audio_to_cir، image_to_cir، آزمایشگاه IoT آنلاین

## نکات برای توسعه‌دهندگان (دانشجویان)

اگر نوع المان جدیدی اضافه می‌کنید، این فایل‌ها باید هماهنگ به‌روزرسانی شوند:

| لایه | فایل |
|---|---|
| تعریف نوع در CIR | `core/cir/schema.py`, `core/cir/pin_order.py` |
| تولید SPICE | `services/cir_to_spice/basic_converter.py` |
| پارس SPICE | `services/cir_to_spice/spice_parser.py` |
| شماتیک backend | `services/schematic/schemdraw_generator.py` |
| adapter فرانت‌اند | `frontend/src/lib/cir.js` (`UI_TO_CIR_TYPE`/`CIR_TO_UI_TYPE`) |
| سمبل UI | `frontend/src/CircuitBuilder.jsx` (`renderSymbol`, `COMPONENT_TYPES`) |

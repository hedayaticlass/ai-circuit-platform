# AI Circuit Platform — معرفی برای بررسی توسط AI / توسعه‌دهنده دیگر

## هدف پروژه
پلتفرم متن‌باز برای طراحی، تحلیل و آموزش مدارهای الکتریکی/الکترونیکی با کمک
هوش مصنوعی. پروژه دانشجویی است (مهندسی برق/کامپیوتر)، قرار است طی چند ترم با
مشارکت دانشجویان توسعه یابد. اولویت: معماری ساده، قابل‌نگهداری و قابل‌توسعه
بیشتر از سرعت پیاده‌سازی.

## معماری کلی
هسته‌ی پروژه یک قرارداد داده‌ای مشترک به نام **CIR** (Circuit Intermediate
Representation) است — یک schema ساده (JSON/Pydantic) که مدار را به‌صورت
لیستی از المان‌ها (نوع، مقدار، گره‌های متصل) نشان می‌دهد. تمام ماژول‌ها از
طریق CIR با هم ارتباط دارند، نه مستقیماً با SPICE:

```
متن فارسی  ──(AI)──▶  CIR  ──(دترمینیستیک)──▶  SPICE netlist
                       │                              │
                  (رسم در UI)                   (PySpice/ngspice)
                       │                              │
                  ویرایش دستی                    نتایج تحلیل
```

## ساختار کد
```
core/            کتابخانه مشترک پایتون: تعریف CIR + interfaceهای abstract + کلاینت LLM
services/        پیاده‌سازی‌های concrete (text_to_cir با AI، cir_to_spice دترمینیستیک، schematic، spice_analyzer)
api/main.py      FastAPI — فقط orchestration، بدون منطق تجاری
frontend/        React + Vite + Tailwind — ویرایشگر شماتیک بصری + چت AI
tests/           pytest برای بخش‌های دترمینیستیک (بدون نیاز به API key)
```

## استک تکنولوژی
- Backend: Python 3.12, FastAPI, Pydantic v2
- AI: هر سرویس سازگار با OpenAI Chat API (فعلاً از OpenRouter استفاده می‌شود)
- تحلیل مدار: PySpice (wrapper روی ngspice)
- Frontend: React 18, Vite, Tailwind CSS (بدون TypeScript فعلاً)
- Deploy: Docker Compose (دو سرویس: api + frontend)

## وضعیت فعلی (چه چیزی کار می‌کند)
- تبدیل توضیح متنی فارسی → CIR با AI، با auto-retry بر اساس بازخورد
  validation (حداکثر ۳ تلاش) ✅ (`services/text_to_cir/openai_text_to_cir.py`)
- تبدیل CIR → نت‌لیست SPICE (دترمینیستیک)، با کتابخانه‌ی گسترش‌یافته‌ی
  مدل‌ها (دیود/BJT/MOSFET رایج) و سنتز دینامیک مدل دیود زنر از روی
  ولتاژ شکست ✅ (`services/cir_to_spice/basic_converter.py`)
- تبدیل SPICE → CIR (پارسر معکوس) ✅
- رسم شماتیک سمت backend با schemdraw ✅
- ویرایشگر بصری React (drag/drop، اتصال دستی پایه‌ها، چت AI) ✅ متصل به backend
- چیدمان خودکار (auto-layout) مدارهای تولیدشده توسط AI با الگوریتم لایه‌ای ساده (BFS-based) ✅
- تحلیل DC operating point با PySpice/ngspice ✅ (نیاز به نصب باینری ngspice)
- شبیه‌سازی transient (`/api/simulate`) ✅ (`services/spice_analyzer/transient_analyzer.py`)
- «عامل بهبود مدار» (دستور طبیعی مثل «ولتاژ گره ۲ را بیشتر کن») پیاده‌سازی
  شده ✅ (`services/text_to_cir/llm_circuit_improver.py`, endpoint `/api/improve`)

## محدودیت‌های شناخته‌شده (عمدی، برای فازهای بعد)
- فقط ۵ نوع المان دوپایه در UI پشتیبانی می‌شود: مقاومت، خازن، سلف، دیود، منبع
  ولتاژ. ترانزیستور/opamp/IC در CIR قابل تعریف‌اند اما UI سمبل ندارد.
- هر پیام چت کل مدار را جایگزین می‌کند، نه merge.
- مدل op-amp رفتاری ساده‌شده است (۳-پایه، بدون vcc/vee، بدون slew rate)؛
  برای آموزش مدارهای پایه کافی است ولی رفتار غیرخطی پیشرفته را مدل نمی‌کند.
- بدون authentication/چندکاربره (پروژه تک‌کاربره فعلاً است).

## چیزی که از بازبین می‌خواهیم
بازبینی معماری، الگوهای طراحی، نام‌گذاری، تست‌پذیری، و هر ریسک یا
ضدالگوی (anti-pattern) که برای یک پروژه آموزشی چندترمی با مشارکت دانشجویان
مشکل‌ساز خواهد بود.

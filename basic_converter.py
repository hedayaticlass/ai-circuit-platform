"""
تبدیل CIR -> نت‌لیست SPICE (به صورت دترمینیستیک، بدون AI).

هر نوع المان به یک خط نت‌لیست SPICE استاندارد نگاشت می‌شود.
نگاشت‌ها بر اساس قراردادهای ngspice/SPICE3 هستند.
"""

from __future__ import annotations

import re

from core.cir import Circuit, Component, ComponentType
from core.interfaces.cir_to_spice import CIRToSpice

# پیشوند SPICE برای هر نوع المان (حرف اول نام المان در نت‌لیست)
SPICE_PREFIX: dict[ComponentType, str] = {
    ComponentType.RESISTOR: "R",
    ComponentType.CAPACITOR: "C",
    ComponentType.INDUCTOR: "L",
    ComponentType.VOLTAGE_SOURCE: "V",
    ComponentType.AC_VOLTAGE_SOURCE: "V",
    ComponentType.CURRENT_SOURCE: "I",
    ComponentType.DIODE: "D",
    ComponentType.BJT_NPN: "Q",
    ComponentType.BJT_PNP: "Q",
    ComponentType.MOSFET_N: "M",
    ComponentType.MOSFET_P: "M",
    ComponentType.JFET: "J",
    ComponentType.OPAMP: "X",
    ComponentType.IC: "X",
}

# مدل پیش‌فرض برای المان‌هایی که به مدل نیاز دارند ولی value ندارند
DEFAULT_MODEL: dict[ComponentType, str] = {
    ComponentType.DIODE: "D1N4148",
    ComponentType.BJT_NPN: "2N2222",
    ComponentType.BJT_PNP: "2N2907",
    ComponentType.MOSFET_N: "IRF530",
    ComponentType.MOSFET_P: "IRF9530",
    ComponentType.JFET: "J2N5457",
    ComponentType.OPAMP: "LM741",
}

# تعریف‌های .model داخلی برای مدل‌های پیش‌فرض — ngspice بدون اینها شبیه‌سازی نمی‌کند
#
# این کتابخانه از تحلیل دستی خطاهای benchmark گسترش داده شده است: LLM
# اغلب پارت‌نامبرهای واقعی و رایج (1N4007، 2N3904، IRF540 و ...) تولید
# می‌کند که در نسخه‌ی اولیه‌ی این دیکشنری وجود نداشتند و باعث خطای
# «model not found» در ngspice می‌شدند (۹ مورد از ۲۴ خطای شبیه‌سازی در
# benchmark اولیه). پارامترهای زیر از مدل‌های SPICE استاندارد/منتشرشده
# (Fairchild/OnSemi legacy SPICE model libraries) گرفته شده‌اند.
BUILT_IN_MODELS: dict[str, str] = {
    # --- دیودهای سیگنال/سوئیچینگ ---
    "D1N4148": ".model D1N4148 D(Is=2.52n Rs=.568 N=1.752 Cjo=4p M=.4 tt=20n)",
    "1N4148":  ".model 1N4148 D(Is=2.52n Rs=.568 N=1.752 Cjo=4p M=.4 tt=20n)",
    "1N914":   ".model 1N914 D(Is=2.52n Rs=.568 N=1.752 Cjo=4p M=.4 tt=20n)",
    # --- دیودهای یکسوساز توان (رایج در رکتیفایر/منابع تغذیه) ---
    "1N4001":  ".model 1N4001 D(Is=14.11n Rs=.03645 N=1.984 Cjo=25.89p M=.44 tt=5.7u Bv=50 Ibv=5u)",
    "1N4007":  ".model 1N4007 D(Is=14.11n Rs=.03645 N=1.984 Cjo=25.89p M=.44 tt=5.7u Bv=1000 Ibv=5u)",
    # --- BJT سیگنال کوچک عمومی (NPN/PNP) ---
    "2N2222":  ".model 2N2222 NPN(Bf=255 Vaf=74 Is=14.3f Ise=14.3f Ne=1.31 Ikf=.285 Xtb=1.5 Br=6.1 Nc=2 Isc=0 Ikr=0 Rc=1 Cjc=7.31p Mjc=.342 Vjc=.75 Fc=.5 Cje=22p Mje=.377 Vje=.75 Tf=411p Itf=.6 Vtf=1.7 Xtf=3 Rb=10)",
    "2N2907":  ".model 2N2907 PNP(Bf=235 Vaf=115 Is=14.3f Ise=14.3f Ne=1.3 Ikf=.285 Xtb=1.5 Br=6.1 Nc=2 Isc=0 Ikr=0 Rc=1 Cjc=14.6p Mjc=.345 Vjc=.75 Fc=.5 Cje=19.8p Mje=.38 Vje=.75 Tf=480p Itf=.6 Vtf=1.7 Xtf=3 Rb=10)",
    "2N3904":  ".model 2N3904 NPN(Is=6.734f Xti=3 Eg=1.11 Vaf=74.03 Bf=416.4 Ne=1.259 Ise=6.734f Ikf=66.78m Xtb=1.5 Br=.7371 Nc=2 Isc=0 Ikr=0 Rc=1 Cjc=3.638p Mjc=.3085 Vjc=.75 Fc=.5 Cje=4.493p Mje=.2593 Vje=.75 Tr=239.5n Tf=301.2p Itf=.4 Vtf=4 Xtf=2 Rb=10)",
    "2N3906":  ".model 2N3906 PNP(Is=1.41f Xti=3 Eg=1.11 Vaf=18.7 Bf=180.7 Ne=1.5 Ise=0 Ikf=80m Xtb=1.5 Br=4.977 Nc=2 Isc=0 Ikr=0 Rc=2.5 Cjc=9.728p Mjc=.5776 Vjc=.75 Fc=.5 Cje=8.063p Mje=.3677 Vje=.75 Tr=33.42n Tf=179.3p Itf=.4 Vtf=4 Xtf=6 Rb=10)",
    "BC547":   ".model BC547 NPN(Is=7.049p Bf=110 Vaf=100 Ikf=0.1 Ise=0 Ne=1.5 Br=15 Rb=1 Re=0.5 Rc=1 Cje=10p Cjc=4p Tf=0.5n Tr=100n)",
    # --- MOSFET توان (رایج در مدارهای سوئیچینگ/درایور) ---
    "IRF530":  ".model IRF530 NMOS(Vto=3.0 Kp=5.8 Gamma=0 Phi=0.6 Lambda=0)",
    "IRF9530": ".model IRF9530 PMOS(Vto=-3.0 Kp=5.8 Gamma=0 Phi=0.6 Lambda=0)",
    "IRF540":  ".model IRF540 NMOS(Level=1 Vto=3.6 Kp=20.56 Gamma=0 Phi=0.6 Lambda=5m Rd=.05 Rs=.03)",
    "IRF9540": ".model IRF9540 PMOS(Level=1 Vto=-3.6 Kp=8.7 Gamma=0 Phi=0.6 Lambda=5m Rd=.06 Rs=.03)",
    # --- JFET ---
    "J2N5457": ".model J2N5457 NJF(Beta=1.304m Rd=1 Rs=1 Cgs=4.06p Cgd=1.89p Pb=.6 Is=33.57f Vto=-2.5 Lambda=4m)",
}

# نگاشت غیرحساس به بزرگی/کوچکی حروف برای پیدا کردن نام دقیق مدل در
# BUILT_IN_MODELS — چون LLM ممکن است "1n4007" یا "1N4007" یا "IRF540"
# را با بزرگی/کوچکی حروف متفاوت تولید کند.
_MODEL_LOOKUP_CI: dict[str, str] = {name.upper(): name for name in BUILT_IN_MODELS}


def _find_builtin_model(value: str) -> str | None:
    """نام دقیق مدل در BUILT_IN_MODELS را برمی‌گرداند (case-insensitive)."""
    return _MODEL_LOOKUP_CI.get(value.strip().upper())


# ---------------------------------------------------------------------------
# سنتز دینامیک مدل دیود زنر
# ---------------------------------------------------------------------------
#
# مشکل مشاهده‌شده در benchmark: وقتی کاربر مداری با «دیود زنر ۵ ولت» توصیف
# می‌کند، LLM به‌جای یک نام پارت واقعی (که برای زنر با ولتاژ دلخواه اصلاً
# استاندارد ثابتی ندارد)، مستقیماً ولتاژ را در فیلد value می‌نویسد
# (مثلاً "5V" یا "1.8V"). این رشته نه در کتابخانه‌ی ما تعریف شده و نه یک
# پارت‌نامبر واقعی است، پس ngspice با خطای "model not found" شکست می‌خورد
# (۵ مورد از ۲۴ خطای benchmark اولیه). به‌جای شکست، این مقدار را به‌عنوان
# ولتاژ شکست (Bv) یک دیود زنر سنتزشده تفسیر می‌کنیم — چون این دقیقاً
# همان چیزی است که کاربر با نوشتن "دیود زنر N ولت" قصد داشته.
_ZENER_VALUE_RE = re.compile(
    r"^(?:zener\s*)?(\d+(?:[.,]\d+)?)\s*v(?:olt)?s?$",
    re.IGNORECASE,
)


def _zener_model_name(voltage: float) -> str:
    """نام یکتای مدل بر اساس ولتاژ، مثل 5.1 -> 'ZD5V1'، 5.0 -> 'ZD5V0'."""
    whole = int(voltage)
    frac = round((voltage - whole) * 10)
    if frac == 10:  # گرد کردن اعشار مثل 4.99 -> 5.0
        whole += 1
        frac = 0
    return f"ZD{whole}V{frac}"


def _synthesize_zener_model(voltage: float) -> tuple[str, str]:
    """مدل .model یک دیود زنر با ولتاژ شکست داده‌شده می‌سازد.

    پارامترهای forward مشابه یک دیود سیلیکونی عمومی (1N4148-like) است؛
    Bv ولتاژ شکست خواسته‌شده است و Ibv/Nbv برای پایداری عددی (همگرایی
    نرم در ناحیه‌ی شکست) اضافه شده‌اند — بدون این دو، ngspice در ولتاژهای
    نزدیک Bv معمولاً همگرا نمی‌شود.
    """
    name = _zener_model_name(voltage)
    model_line = (
        f".model {name} D(Is=2.52n Rs=.568 N=1.752 Cjo=4p M=.4 tt=20n "
        f"Bv={voltage:.2f} Ibv=1m Nbv=1.5)"
    )
    return name, model_line


def _resolve_diode_value(value: str | None) -> tuple[str, str | None]:
    """مقدار/مدل یک دیود را resolve می‌کند.

    خروجی: (نامی که در خط نت‌لیست نوشته می‌شود، تعریف .model دینامیک
    در صورت نیاز یا None اگر مدل از BUILT_IN_MODELS تأمین می‌شود).
    """
    if not value:
        return DEFAULT_MODEL[ComponentType.DIODE], None

    builtin = _find_builtin_model(value)
    if builtin:
        return builtin, None

    match = _ZENER_VALUE_RE.match(value.strip())
    if match:
        voltage = float(match.group(1).replace(",", "."))
        name, model_line = _synthesize_zener_model(voltage)
        return name, model_line

    # نه در کتابخانه‌ی داخلی، نه به شکل ولتاژ زنر — همان‌طور که هست
    # منتقل می‌شود (فرض بر این‌که پارت‌نامبر واقعی دیگری است که کاربر
    # خودش تعریف .model آن را در نت‌لیست نهایی اضافه می‌کند).
    return value, None


# تعریف‌های .subckt برای المان‌هایی که با نام مرجع (X...) ارجاع داده می‌شوند.
# نکته مهم: این subckt با همان ۳ پایه ساده‌شده‌ای که در core/cir سازگار است
# تعریف شده: (out, in_pos, in_neg) — بدون پایه‌های تغذیه vcc/vee. این یک
# مدل رفتاری (behavioral) ساده‌شده از op-amp ایده‌آل است: بهره باز بسیار
# بالا با یک قطب غالب، به‌علاوه محدودسازی (saturation) خروجی در ±۱۳ ولت
# (مقدار معمول برای تغذیه‌ی متقارن ±۱۵ ولت).
#
# نکته طراحی: نسخه‌ی قبلی این مدل (Egain بدون محدودیت با بهره ۲۰۰k) در
# ۶ مدار از benchmark باعث عدم همگرایی عددی می‌شد — یک تقویت‌کننده با
# بهره باز واقعی و فیدبک منفی معمولاً به ولتاژ خروجی معقولی می‌رسد، اما
# بدون سقف صریح، ngspice گاهی هنگام حل مدار میانی (قبل از رسیدن فیدبک
# به تعادل) به ولتاژهای غیرفیزیکی برخورد می‌کند و همگرا نمی‌شود. تابع
# max/min داخلی ngspice (پشتیبانی‌شده در B-element) این را با یک سقف
# صریح و نرم حل می‌کند بدون این‌که رفتار خطی ناحیه‌ی فعال تغییر کند.
BUILT_IN_SUBCIRCUITS: dict[str, str] = {
    "LM741": (
        ".subckt LM741 out in_pos in_neg\n"
        "* مدل رفتاری ساده‌شده ۳-پایه (بدون vcc/vee) — بهره باز بالا + قطب\n"
        "* غالب + محدودسازی خروجی در ±13V برای جلوگیری از عدم همگرایی عددی\n"
        "Bgain n1 0 V = { max(min(200k*V(in_pos,in_neg), 13), -13) }\n"
        "Rout   n1   out 75\n"
        "Cpole  out  0   1.59n\n"
        ".ends LM741"
    ),
}


def _resolve_subckt_name(model: str) -> str | None:
    """اگر model به یکی از زیرمدارهای داخلی اشاره دارد، نام آن را برمی‌گرداند."""
    return model if model in BUILT_IN_SUBCIRCUITS else None


class CIRToSpiceError(Exception):
    pass


class BasicCIRToSpice(CIRToSpice):
    """تبدیل ساده CIR به نت‌لیست SPICE.

    opamp به‌صورت subcircuit (X...) نوشته می‌شود؛ تعریف .subckt آن از
    BUILT_IN_SUBCIRCUITS به‌صورت خودکار به نت‌لیست اضافه می‌شود (مشابه
    مکانیزم BUILT_IN_MODELS برای دیود/ترانزیستور). اگر مدل/زیرمداری در
    این دو دیکشنری تعریف نشده باشد، کاربر باید خودش آن را در نت‌لیست
    نهایی اضافه کند.

    برای دیود، اگر value یک پارت‌نامبر شناخته‌شده نباشد اما به شکل یک
    ولتاژ باشد (مثل "5.1V")، به‌صورت خودکار به‌عنوان دیود زنر با همان
    ولتاژ شکست تفسیر و یک مدل .model دینامیک برایش ساخته می‌شود.
    """

    def convert(self, circuit: Circuit) -> str:
        if not circuit.components:
            raise CIRToSpiceError("مدار خالی است؛ نمی‌توان نت‌لیست تولید کرد.")

        title = circuit.metadata.get("title", "Generated by ai-circuit-platform")
        lines: list[str] = [f".title {title}"]

        needed_models: set[str] = set()
        needed_subckts: set[str] = set()
        # نام مدل -> تعریف .model دینامیک (مثل زنرهای سنتزشده)
        dynamic_models: dict[str, str] = {}
        # comp.id -> رشته‌ای که باید در خط نت‌لیست به‌جای value نوشته شود
        resolved_values: dict[str, str] = {}

        for comp in circuit.components:
            if comp.type == ComponentType.DIODE:
                resolved, dynamic_def = _resolve_diode_value(comp.value)
                resolved_values[comp.id] = resolved
                if dynamic_def is not None:
                    dynamic_models[resolved] = dynamic_def
                elif resolved in BUILT_IN_MODELS:
                    needed_models.add(resolved)
            else:
                model = comp.value or DEFAULT_MODEL.get(comp.type, "")
                builtin = _find_builtin_model(model) if model else None
                resolved = builtin or model
                resolved_values[comp.id] = resolved
                if resolved in BUILT_IN_MODELS:
                    needed_models.add(resolved)
                subckt_name = _resolve_subckt_name(resolved)
                if subckt_name:
                    needed_subckts.add(subckt_name)

            lines.append(self._component_line(comp, resolved_values[comp.id]))

        for model_name in sorted(needed_models):
            lines.append(BUILT_IN_MODELS[model_name])

        for model_name in sorted(dynamic_models):
            lines.append(dynamic_models[model_name])

        for subckt_name in sorted(needed_subckts):
            lines.append(BUILT_IN_SUBCIRCUITS[subckt_name])

        lines.append(".end")
        return "\n".join(lines)

    def _component_line(self, comp: Component, value_or_model: str) -> str:
        prefix = SPICE_PREFIX.get(comp.type)
        if prefix is None:
            raise CIRToSpiceError(
                f"نوع المان '{comp.type.value}' در حال حاضر برای تبدیل به "
                f"SPICE پشتیبانی نمی‌شود."
            )

        # اگر id کاربر از قبل با پیشوند صحیح شروع شده، همان حفظ شود
        name = comp.id if comp.id.upper().startswith(prefix) else f"{prefix}{comp.id}"

        if not value_or_model:
            raise CIRToSpiceError(
                f"المان {comp.id} مقدار/مدل ندارد و مقدار پیش‌فرضی هم "
                f"برای نوع آن تعریف نشده است."
            )

        # برای MOSFET: اگر body/bulk داده نشده، به source وصل می‌شود (رایج‌ترین حالت)
        nodes = list(comp.nodes)
        if comp.type in (ComponentType.MOSFET_N, ComponentType.MOSFET_P) and len(nodes) == 3:
            nodes.append(nodes[2])  # bulk = source

        return f"{name} {' '.join(nodes)} {value_or_model}"

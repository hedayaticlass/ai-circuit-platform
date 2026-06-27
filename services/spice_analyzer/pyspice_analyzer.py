"""
تحلیل‌گر SPICE با استفاده از PySpice (که خودش wrapper روی ngspice است).

⚠️ نکته زیرساختی مهم: PySpice فقط یک پکیج Python نیست؛ برای اجرای واقعی
شبیه‌سازی نیاز به نصب باینری `ngspice` روی سیستم دارد (نه از طریق pip).
  - در Docker: با apt در Dockerfile نصب می‌شود (`ngspice` نصب شده است).
  - در ویندوز/محلی: باید جداگانه از https://ngspice.sourceforge.io نصب شود
    یا میتوان از طریق conda (`conda install -c conda-forge ngspice`) گرفت.

اگر ngspice پیدا نشود، PySpice موقع ساخت Simulator خطا می‌دهد؛ این کلاس آن
خطا را می‌گیرد و در قالب SpiceAnalysisError با پیام راهنما به کاربر برمی‌گرداند.
"""

from __future__ import annotations

from typing import Any

from core.cir import Circuit
from core.interfaces.spice_analyzer import SpiceAnalyzer


class SpiceAnalysisError(Exception):
    pass


class PySpiceAnalyzer(SpiceAnalyzer):
    """اجرای آنالیز نقطه‌کار DC (.op) با PySpice/ngspice.

    محدودیت فعلی: فقط آنالیز DC operating point پشتیبانی می‌شود (ولتاژ هر
    گره نسبت به زمین، و جریان عبوری از منابع ولتاژ). آنالیزهای AC/Transient
    در فازهای بعدی اضافه می‌شوند.
    """

    def analyze(self, circuit: Circuit, spice_netlist: str) -> dict[str, Any]:
        try:
            from PySpice.Spice.Parser import SpiceParser
        except ImportError as exc:
            raise SpiceAnalysisError(
                "کتابخانه PySpice نصب نیست. با 'pip install PySpice' نصب کنید."
            ) from exc

        try:
            parser = SpiceParser(source=spice_netlist)
            pyspice_circuit = parser.build_circuit()
        except Exception as exc:
            raise SpiceAnalysisError(
                f"خطا در parse کردن نت‌لیست توسط PySpice: {exc}"
            ) from exc

        try:
            simulator = pyspice_circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.operating_point()
        except Exception as exc:
            raise SpiceAnalysisError(
                "اجرای شبیه‌سازی ناموفق بود. معمولاً به این معنی است که "
                "ngspice روی سیستم نصب نیست یا در PATH قرار ندارد. "
                f"جزئیات: {exc}"
            ) from exc

        node_voltages: dict[str, float] = {}
        for node_name, node in analysis.nodes.items():
            node_voltages[str(node_name)] = _to_scalar_float(node)

        branch_currents: dict[str, float] = {}
        for branch_name, branch in analysis.branches.items():
            branch_currents[str(branch_name)] = _to_scalar_float(branch)

        return {
            "analysis_type": "operating_point",
            "node_voltages": node_voltages,
            "branch_currents": branch_currents,
            "warnings": circuit.metadata.get("validation_warnings", []),
        }


def _to_scalar_float(value: Any) -> float:
    """تبدیل امن مقدار خروجی PySpice (WaveForm، که خودش یک wrapper روی
    آرایه‌ی numpy است) به float پایتون.

    در نسخه‌های قدیمی‌تر numpy، float(value) مستقیماً کار می‌کرد چون
    WaveForm آرایه‌ی تک‌عنصری را implicit به اسکالر تبدیل می‌کرد. در
    نسخه‌های جدیدتر numpy این تبدیل ضمنی حذف شده و باید صریح انجام شود.
    """
    import numpy as np

    array = np.asarray(value)
    return float(array.reshape(-1)[0])

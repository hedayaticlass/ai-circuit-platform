import pytest

from core.cir import Circuit, Component, ComponentType
from services.spice_analyzer.pyspice_analyzer import PySpiceAnalyzer, SpiceAnalysisError


def test_analyze_raises_clear_error_without_pyspice_or_ngspice():
    """
    این تست فرض می‌کند PySpice یا ngspice ممکن است روی محیط CI نصب نباشند.
    هدف این نیست که شبیه‌سازی واقعی را تست کنیم (که نیاز به ngspice دارد)،
    بلکه این است که در صورت نبود این پیش‌نیازها، خطای قابل‌فهم برگردد
    (نه یک traceback خام).
    """
    circuit = Circuit(
        components=[
            Component(id="V1", type=ComponentType.VOLTAGE_SOURCE, value="5V", nodes=["1", "0"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "0"]),
        ]
    )
    netlist = "V1 1 0 5V\nR1 1 0 1k\n.end"

    try:
        import PySpice  # noqa: F401
    except ImportError:
        with pytest.raises(SpiceAnalysisError, match="PySpice"):
            PySpiceAnalyzer().analyze(circuit, netlist)
        return

    # اگر PySpice نصب است ولی ngspice نصب نیست، باید همچنان خطای واضح بدهد
    # (نه crash). اگر هر دو نصب باشند، این تست فقط بررسی می‌کند که
    # exception یا نتیجه دیکشنری معتبر برگردد.
    try:
        result = PySpiceAnalyzer().analyze(circuit, netlist)
        assert "node_voltages" in result
    except SpiceAnalysisError:
        pass  # ngspice نصب نیست؛ خطای کنترل‌شده قابل قبول است

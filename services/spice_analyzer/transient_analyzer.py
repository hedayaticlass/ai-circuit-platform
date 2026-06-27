"""
پیاده‌سازی تحلیل transient با PySpice/ngspice.

این ماژول دستور `.tran` را به نت‌لیست اضافه می‌کند و نتایج سری‌های
زمانی را به `TransientResult` تبدیل می‌کند.

نکته مهم درباره VAC: منبع ولتاژ AC در نت‌لیست SPICE باید به شکل
  V1 n+ n- SIN(offset amplitude freq)
باشد. این ماژول نت‌لیست موجود را می‌پذیرد (که قبلاً توسط cir_to_spice
ساخته شده) و فقط دستور .tran و .end را مدیریت می‌کند.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from core.interfaces.transient_analyzer import (
    TransientAnalyzer,
    TransientParams,
    TransientResult,
)


class TransientAnalysisError(Exception):
    pass


class PySpiceTransientAnalyzer(TransientAnalyzer):
    """اجرای .tran با PySpice + ngspice."""

    def simulate(self, spice_netlist: str, params: TransientParams) -> TransientResult:
        issues = params.validate()
        if issues:
            raise TransientAnalysisError("پارامترهای نامعتبر:\n" + "\n".join(issues))

        try:
            from PySpice.Spice.Parser import SpiceParser
        except ImportError as exc:
            raise TransientAnalysisError(
                "کتابخانه PySpice نصب نیست. با 'pip install PySpice' نصب کنید."
            ) from exc

        # اضافه کردن دستور .tran به نت‌لیست قبل از .end
        netlist = self._inject_tran(spice_netlist, params)

        try:
            parser = PySpiceParser(source=netlist)
            circuit = parser.build_circuit()
        except Exception as exc:
            raise TransientAnalysisError(
                f"خطا در parse کردن نت‌لیست: {exc}"
            ) from exc

        try:
            simulator = circuit.simulator(temperature=25, nominal_temperature=25)
            analysis = simulator.transient(
                step_time=params.step_time,
                end_time=params.end_time,
                start_time=params.start_time,
                **({"max_time": params.max_step} if params.max_step else {}),
            )
        except Exception as exc:
            raise TransientAnalysisError(
                f"اجرای شبیه‌سازی transient ناموفق بود. "
                f"مطمئن شوید ngspice نصب است. جزئیات: {exc}"
            ) from exc

        time_arr = _to_float_list(analysis.time)

        node_voltages: dict[str, list[float]] = {}
        for node_name, waveform in analysis.nodes.items():
            node_voltages[str(node_name)] = _to_float_list(waveform)

        branch_currents: dict[str, list[float]] = {}
        for branch_name, waveform in analysis.branches.items():
            branch_currents[str(branch_name)] = _to_float_list(waveform)

        return TransientResult(
            time=time_arr,
            node_voltages=node_voltages,
            branch_currents=branch_currents,
            metadata={
                "step_time": params.step_time,
                "end_time": params.end_time,
                "points": len(time_arr),
            },
        )

    @staticmethod
    def _inject_tran(netlist: str, params: TransientParams) -> str:
        """دستور .tran را قبل از .end در نت‌لیست قرار می‌دهد."""
        tran_line = (
            f".tran {params.step_time} {params.end_time} {params.start_time}"
        )
        if ".end" in netlist.lower():
            return re.sub(r"\.end\b", f"{tran_line}\n.end", netlist, flags=re.IGNORECASE)
        return netlist + f"\n{tran_line}\n.end"


# alias برای import راحت‌تر
PySpiceParser = None
try:
    from PySpice.Spice.Parser import SpiceParser as _SP
    PySpiceParser = _SP
except ImportError:
    pass


def _to_float_list(waveform: Any) -> list[float]:
    """تبدیل خروجی numpy/WaveForm از PySpice به list ساده از float."""
    arr = np.asarray(waveform).reshape(-1)
    return [float(v) for v in arr]

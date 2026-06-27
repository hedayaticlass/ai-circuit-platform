"""
Interface: SPICE Analysis

ماژولی که نت‌لیست SPICE را اجرا/تحلیل می‌کند (مثلاً با ngspice)
و نتایج عددی (ولتاژها، جریان‌ها، نمودارها) را برمی‌گرداند.

این بخش هنوز در پروژه پیاده‌سازی نشده؛ این interface محل قرارگیری
آن در آینده را مشخص می‌کند.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.cir import Circuit


class SpiceAnalyzer(ABC):
    """اجرای شبیه‌سازی SPICE و بازگرداندن نتایج تحلیل."""

    @abstractmethod
    def analyze(self, circuit: Circuit, spice_netlist: str) -> dict[str, Any]:
        """نت‌لیست را شبیه‌سازی کرده و نتایج را برمی‌گرداند.

        ساختار دقیق dict خروجی در نسخه‌های آینده تثبیت می‌شود
        (مثلاً شامل ولتاژهای گره‌ها، جریان‌ها، یا داده برای رسم نمودار).
        """
        raise NotImplementedError

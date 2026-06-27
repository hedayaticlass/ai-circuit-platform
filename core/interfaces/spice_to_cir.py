"""
Interface: SPICE netlist -> CIR

برخلاف ماژول‌های AI، این یک پارسر دترمینیستیک است (مثل parser.py
قدیمی پروژه که اکنون بازنویسی و یکپارچه شده است).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.cir import Circuit


class SpiceToCIR(ABC):
    """تبدیل متن نت‌لیست SPICE به CIR."""

    @abstractmethod
    def parse(self, netlist: str) -> Circuit:
        """متن نت‌لیست SPICE را parse کرده و Circuit برمی‌گرداند.

        خطوط کامنت (با * شروع می‌شوند) و دستورات (با . شروع می‌شوند)
        نادیده گرفته می‌شوند (مگر .title که می‌تواند در metadata
        ذخیره شود).
        """
        raise NotImplementedError

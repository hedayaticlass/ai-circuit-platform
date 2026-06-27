"""
Interface: CIR -> SPICE
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.cir import Circuit


class CIRToSpice(ABC):
    """تبدیل یک Circuit (CIR) به متن نت‌لیست SPICE."""

    @abstractmethod
    def convert(self, circuit: Circuit) -> str:
        """یک Circuit را گرفته و متن کامل نت‌لیست SPICE برمی‌گرداند.

        خروجی باید یک نت‌لیست معتبر و خوداتکا باشد (شامل خط .title
        و .end، اما بدون نیاز به .control برای تحلیل ساده).
        """
        raise NotImplementedError

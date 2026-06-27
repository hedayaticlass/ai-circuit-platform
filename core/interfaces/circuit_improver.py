"""
Interface: Circuit Improver (عامل بهبود مدار)

این ماژول هنوز پیاده‌سازی نشده — این فایل فقط interface را برای فاز بعدی
پروژه (طبق نقشه راه) از پیش تعریف می‌کند، تا وقتی ساخته شد، بقیه سیستم
(API, frontend) بدون تغییر ساختاری به آن وصل شوند.

ایده: کاربر هدف خود را به زبان طبیعی می‌نویسد (مثلاً «نویز را کم کن»)،
این عامل با توجه به CIR فعلی و (در صورت وجود) نتایج تحلیل قبلی، یک CIR
جدید + توضیح تغییرات برمی‌گرداند.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.cir import Circuit


class CircuitImprover(ABC):
    """بهبود یک مدار بر اساس هدف کاربر، با کمک نتایج تحلیل (اختیاری)."""

    @abstractmethod
    def improve(
        self,
        circuit: Circuit,
        goal: str,
        analysis_results: dict[str, Any] | None = None,
    ) -> tuple[Circuit, str]:
        """
        Args:
            circuit: CIR فعلی مدار
            goal: هدف کاربر به زبان طبیعی (مثلاً "نویز را کم کن")
            analysis_results: خروجی SpiceAnalyzer روی مدار فعلی، اگر موجود باشد

        Returns:
            (circuit_جدید, توضیح_تغییرات)
        """
        raise NotImplementedError

"""
Interface: Transient Analysis (تحلیل گذرا)

تحلیل وابسته به زمان (.tran در SPICE) که ولتاژ گره‌ها و جریان شاخه‌ها
را در بازه زمانی مشخص محاسبه می‌کند. این پایه ولتمتر/آمپرمتر و
اسیلوسکوپ داخلی است.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TransientParams:
    """پارامترهای شبیه‌سازی transient."""

    step_time: float = 1e-5       # گام زمانی (ثانیه) — مثلاً 10µs
    end_time: float  = 1e-3       # زمان پایان (ثانیه) — مثلاً 1ms
    start_time: float = 0.0       # زمان شروع ذخیره نتایج (معمولاً ۰)
    max_step: float | None = None  # حداکثر گام ngspice (اختیاری)

    def validate(self) -> list[str]:
        issues = []
        if self.step_time <= 0:
            issues.append("گام زمانی باید مثبت باشد.")
        if self.end_time <= self.start_time:
            issues.append("زمان پایان باید از زمان شروع بزرگتر باشد.")
        if self.end_time / self.step_time > 100_000:
            issues.append(
                "تعداد نقاط بیش از ۱۰۰٬۰۰۰ است. step_time را بزرگ‌تر کنید."
            )
        return issues


@dataclass
class TransientResult:
    """نتیجه‌ی تحلیل transient.

    همه آرایه‌ها هم‌طول هستند و ایندکس i متناظر با لحظه‌ی time[i] است.
    """

    time: list[float]                            # محور زمان (ثانیه)
    node_voltages: dict[str, list[float]]        # نام گره -> آرایه ولتاژ (ولت)
    branch_currents: dict[str, list[float]]      # نام شاخه -> آرایه جریان (آمپر)
    metadata: dict = field(default_factory=dict)


class TransientAnalyzer(ABC):
    """اجرای شبیه‌سازی transient و بازگرداندن سری‌های زمانی."""

    @abstractmethod
    def simulate(
        self,
        spice_netlist: str,
        params: TransientParams,
    ) -> TransientResult:
        raise NotImplementedError

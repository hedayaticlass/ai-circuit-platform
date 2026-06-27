"""
Interface: Text -> CIR

هر ماژولی که توضیح متنی (فارسی/انگلیسی) یک مدار را به CIR تبدیل می‌کند
باید این کلاس را implement کند. این یعنی در آینده می‌توانیم backend
هوش مصنوعی را عوض کنیم (OpenAI -> Claude -> مدل محلی) بدون تغییر در
بقیه سیستم.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.cir import Circuit


class TextToCIR(ABC):
    """تبدیل توضیح متنی یک مدار به CIR."""

    @abstractmethod
    def convert(self, description: str) -> Circuit:
        """توضیح متنی مدار را می‌گیرد و یک Circuit معتبر برمی‌گرداند.

        Args:
            description: توضیح مدار به زبان طبیعی (فارسی یا انگلیسی)

        Returns:
            یک نمونه Circuit. در صورت بروز خطا، باید Exception
            مناسب پرتاب شود (نه دیکشنری خطا)، تا لایه API
            مدیریت یکنواختی داشته باشد.
        """
        raise NotImplementedError

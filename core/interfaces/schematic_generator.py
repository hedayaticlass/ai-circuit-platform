"""
Interface: CIR -> Schematic Image
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.cir import Circuit


class SchematicGenerator(ABC):
    """تولید تصویر شماتیک از یک CIR."""

    @abstractmethod
    def render(self, circuit: Circuit, output_path: str | Path) -> Path:
        """شماتیک مدار را رسم کرده و به صورت فایل تصویری ذخیره می‌کند.

        Args:
            circuit: مدار ورودی
            output_path: مسیر فایل خروجی (مثلاً .png یا .svg)

        Returns:
            مسیر فایل ذخیره‌شده (Path)
        """
        raise NotImplementedError

"""
بارگذاری پرامپت‌ها از فایل‌های متنی در core/llm/prompts/

پرامپت‌ها عمداً از کد جدا شده‌اند تا:
- بدون نیاز به دانش پایتون، توسط دانشجویان قابل ویرایش باشند
- تغییرات پرامپت در git diff واضح و مجزا از منطق کد دیده شود
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    """متن یک پرامپت را با نام فایل (بدون پسوند) بار می‌گذارد.

    مثال: load_prompt("text_to_cir_system") فایل
    text_to_cir_system.txt را می‌خواند.
    """
    path = PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"فایل پرامپت یافت نشد: {path}")
    return path.read_text(encoding="utf-8").strip()

"""
پیاده‌سازی TextToCIR با استفاده از یک LLM سازگار با OpenAI API.

این ماژول جایگزین منطق قدیمی موجود در r/api_client.py است که
پرامپت‌های کد matplotlib را داخل خودش داشت. اینجا فقط CIR تولید
می‌شود؛ تولید SPICE و رسم شماتیک به ماژول‌های جدا منتقل شده‌اند.
"""

from __future__ import annotations

from core.cir import Circuit
from core.interfaces.text_to_cir import TextToCIR
from core.llm.client import LLMClient, LLMError
from core.llm.prompt_loader import load_prompt


class TextToCIRError(Exception):
    """خطای مخصوص این ماژول؛ پیام آن قابل نمایش به کاربر است."""


class OpenAITextToCIR(TextToCIR):
    """تبدیل متن به CIR با استفاده از یک مدل زبانی."""

    def __init__(self, client: LLMClient | None = None) -> None:
        self.client = client or LLMClient()
        self.system_prompt = load_prompt("text_to_cir_system")

    def convert(self, description: str) -> Circuit:
        if not description or not description.strip():
            raise TextToCIRError("توضیح مدار نمی‌تواند خالی باشد.")

        try:
            data = self.client.chat_json(self.system_prompt, description)
        except LLMError as exc:
            raise TextToCIRError(str(exc)) from exc

        try:
            circuit = Circuit.model_validate(data)
        except Exception as exc:  # pydantic ValidationError و غیره
            raise TextToCIRError(
                f"خروجی مدل با ساختار CIR مطابقت ندارد: {exc}"
            ) from exc

        issues = circuit.validate_circuit()
        if issues:
            # خطاهای اعتبارسنجی را به عنوان بخشی از metadata نگه می‌داریم
            # تا لایه بالاتر بتواند به کاربر هشدار نشان دهد، بدون اینکه
            # کل درخواست شکست بخورد.
            circuit.metadata["validation_warnings"] = issues

        return circuit

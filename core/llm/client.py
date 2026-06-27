"""
Wrapper مشترک برای صدا زدن سرویس‌های LLM (OpenAI / OpenRouter / ...).

تمام ماژول‌هایی که نیاز به AI دارند (text_to_cir, ...) باید از این
کلاینت استفاده کنند تا:
- تنظیمات (API key, base URL, model) یکجا مدیریت شود
- در آینده تغییر provider فقط در یک فایل انجام شود
- خروجی JSON به صورت یکنواخت parse و خطادهی شود
"""

from __future__ import annotations

import json
import os
import re

import requests


class LLMError(Exception):
    """خطای عمومی برای مشکلات ارتباط با LLM یا parse خروجی."""


class LLMClient:
    """کلاینت ساده برای APIهای سازگار با OpenAI (chat completions)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or os.environ.get("LLM_API_KEY") or os.environ.get(
            "OPENAI_API_KEY"
        )
        self.base_url = (
            base_url
            or os.environ.get("LLM_BASE_URL")
            or "https://api.openai.com/v1"
        )
        self.model = model or os.environ.get("LLM_MODEL") or "gpt-4o-mini"
        self.timeout = timeout

        if not self.api_key:
            raise LLMError(
                "API key تنظیم نشده است. متغیر محیطی LLM_API_KEY یا "
                "OPENAI_API_KEY را تنظیم کنید، یا api_key را مستقیم پاس دهید."
            )

    def chat(self, system_prompt: str, user_message: str) -> str:
        """یک درخواست chat completion ارسال می‌کند و متن پاسخ را برمی‌گرداند."""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.2,
        }

        try:
            response = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMError(f"خطا در ارتباط با سرویس LLM: {exc}") from exc

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMError(f"پاسخ نامعتبر از سرویس LLM: {exc}") from exc

    def chat_json(self, system_prompt: str, user_message: str) -> dict:
        """مثل chat، اما خروجی را به صورت dict پارس‌شده برمی‌گرداند.

        مدل ممکن است JSON را داخل ```json ... ``` بپیچد؛ این متد
        آن را تشخیص و حذف می‌کند.
        """
        raw = self.chat(system_prompt, user_message)
        cleaned = _strip_code_fences(raw)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMError(
                f"پاسخ مدل JSON معتبر نبود: {exc}\n--- raw output ---\n{raw}"
            ) from exc


def _strip_code_fences(text: str) -> str:
    """حذف بلوک‌های ```json ... ``` یا ``` ... ``` در صورت وجود."""
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text

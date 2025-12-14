# api_client.py
import os
import json
from openai import OpenAI

# ------------------------------
# تنظیمات
# ------------------------------
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

PROMPT = """
You are an expert analog/digital circuit designer.
User will describe a circuit in natural language.
Respond ONLY with a JSON object:
{
  "spice": "...",
  "components": [...]
}
""".strip()


def _get_client() -> OpenAI:
    """ساخت کلاینت به صورت lazy تا import کردن فایل خطا ندهد."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )


def _extract_json(text: str) -> str:
    """جدا کردن JSON حتی اگر داخل ```json``` یا ``` باشد"""
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            s = part.strip()
            # اگر با json شروع شود، آن را حذف کن
            if s.lower().startswith("json"):
                s = s[4:].strip()
            if s.startswith("{") and s.endswith("}"):
                return s

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]

    raise ValueError("No JSON object found")


def analyze_text(user_text: str) -> dict:
    client = _get_client()

    msg = PROMPT + "\n\nUser:\n" + user_text

    resp = client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        messages=[{"role": "user", "content": msg}],
        temperature=0.1,
    )

    raw = resp.choices[0].message.content or ""

    try:
        json_str = _extract_json(raw)
        data = json.loads(json_str)

        # تضمین اینکه خروجی همیشه کلیدهای مورد انتظار را دارد
        if not isinstance(data, dict):
            raise ValueError("JSON is not an object")

        data.setdefault("spice", "")
        data.setdefault("components", [])
        return data

    except Exception:
        # اگر مدل JSON نداد، حداقل spice را همان متن برگردان
        return {"spice": raw, "components": []}


def transcribe_audio(audio_bytes):
    return "Audio transcription not implemented yet."

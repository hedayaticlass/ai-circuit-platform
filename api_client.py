# api_client.py
import os
import json
import re
from openai import OpenAI

# ------------------------------
# 1) «اول» سعی کن از محیط بخوانی
# ------------------------------
API_KEY = os.environ.get("OPENROUTER_API_KEY")

# ------------------------------
# 2) اگر نبود، از کلید پشتیبان استفاده کن
#    (اینجا خودت کلید را می‌گذاری)
# ------------------------------
if not API_KEY:
	raise
    RuntimeError("API KEY is not set")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

PROMPT = """
You are an expert analog/digital circuit designer.
User will describe a circuit in natural language.
Respond ONLY with a JSON object:
{
  "spice": "...",
  "components": [...]
}
"""

def _extract_json(text: str) -> str:
    """جدا کردن JSON حتی اگر داخل ```json``` باشد"""
    if "```" in text:
        for part in text.split("```"):
            s = part.strip()
            if s.startswith("{") and s.endswith("}"):
                return s
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end+1]
    raise ValueError("No JSON object found")

def analyze_text(user_text: str) -> dict:
    msg = PROMPT + "\nUser:\n" + user_text

    resp = client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        messages=[{"role": "user", "content": msg}],
        temperature=0.1,
    )
    raw = resp.choices[0].message.content

    try:
        json_str = _extract_json(raw)
        return json.loads(json_str)
    except:
        return {"spice": raw, "components": []}

def transcribe_audio(audio_bytes):
    return "Audio transcription not implemented yet."

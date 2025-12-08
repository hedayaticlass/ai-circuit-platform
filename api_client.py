# api_client.py
import os
import json
import re
from openai import OpenAI

API_KEY = os.environ.get("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")
if not API_KEY:
    raise ValueError("Environment variable OPENROUTER_API_KEY is not set")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

PROMPT = """
You are an expert analog/digital circuit designer.
User will describe a circuit in natural language.
You MUST respond ONLY with a single JSON object in this exact format:

{
  "spice": "SPICE netlist as plain text, lines separated by \\n",
  "components": [
    {
      "type": "Resistor | Capacitor | Inductor | VoltageSource | CurrentSource | Diode | BJT | MOSFET",
      "name": "R1",
      "nodes": ["n1","n2"],
      "value": "10k"
    }
  ]
}

Do NOT add explanations, markdown, or ``` fences. Just the JSON.
"""

def _extract_json(text: str) -> str:
    """
    سعی می‌کنیم JSON را از خروجی مدل جدا کنیم،
    حتی اگر ```json ... ``` داخلش باشد.
    """
    # اگر مدل سه‌تا backtick گذاشته
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            s = part.strip()
            if s.startswith("{") and s.endswith("}"):
                return s

    # در غیر این صورت، از اولین { تا آخرین } را برمی‌داریم
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]

    # اگر هیچ‌کدام جواب نداد، استثناء
    raise ValueError("No JSON object found in model output")


def analyze_text(user_text: str) -> dict:
    """متن کاربر → تماس با مدل → دیکشنری با spice و components"""
    msg = PROMPT + "\nUser description:\n" + user_text

    resp = client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        messages=[{"role": "user", "content": msg}],
        temperature=0.1,
    )

    raw = resp.choices[0].message.content
    try:
        json_str = _extract_json(raw)
        data = json.loads(json_str)
        if "spice" not in data:
            data["spice"] = ""
        if "components" not in data:
            data["components"] = []
        return data
    except Exception:
        # اگر JSON خراب بود، حداقل SPICE را به صورت متن خام بدهیم
        return {"spice": raw, "components": []}


def transcribe_audio(audio_bytes: bytes) -> str:
    # در این مرحله برای MVP فقط placeholder:
    return "Audio transcription not implemented yet."

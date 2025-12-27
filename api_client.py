# api_client.py
import os
import json
from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

PROMPT = """
You are an expert circuit designer. 
Convert the user's description into a standard SPICE netlist.

Rules:
1. Return ONLY a JSON object. No markdown, no conversational text.
2. Structure:
{
  "spice": "Netlist lines separated by \\n (do not include .control blocks)",
  "components": [
     {"type": "Resistor", "name": "R1", "value": "1k", "nodes": ["1", "2"]},
     {"type": "Voltage Source", "name": "V1", "value": "DC 5", "nodes": ["1", "0"]}
  ]
}
3. Use '0' for ground.
""".strip()

def _get_client() -> OpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("API Key not found in .env")
    return OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key)

def _extract_json(text: str) -> str:
    """استخراج JSON تمیز از پاسخ مدل"""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if "{" in part and "}" in part:
                text = part
                break
    
    if text.lower().startswith("json"):
        text = text[4:].strip()
        
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

def analyze_text(user_text: str) -> dict:
    client = _get_client()
    msg = f"{PROMPT}\n\nUser: {user_text}"
    
    try:
        resp = client.chat.completions.create(
            model="openai/gpt-oss-20b:free", # یا google/gemini-2.0-flash-exp:free
            messages=[{"role": "user", "content": msg}],
            temperature=0.1,
        )
        raw = resp.choices[0].message.content or ""
        json_str = _extract_json(raw)
        data = json.loads(json_str)
        
        data.setdefault("spice", "")
        data.setdefault("components", [])
        return data
    except Exception as e:
        return {"spice": f"* Error: {str(e)}", "components": []}

def transcribe_audio(audio_bytes):
    return "Not implemented."
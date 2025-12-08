# api_client.py
from openai import OpenAI
import json

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

PROMPT = """
You convert human text into electronic circuits.
Return JSON: {"spice": "...", "components": [...]}
"""

def analyze_text(text):
    msg = PROMPT + "\n" + text
    r = client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        messages=[{"role":"user","content":msg}],
        temperature=0.1
    )
    raw = r.choices[0].message.content
    try:
        return json.loads(raw)
    except:
        return {"spice": raw, "components": []}

def transcribe_audio(audio_bytes):
    return "Transcription placeholder"  # optional

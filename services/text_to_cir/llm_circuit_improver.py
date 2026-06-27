"""
پیاده‌سازی CircuitImprover با استفاده از LLM.

کاربر می‌تواند دستوری مثل «ولتاژ گره ۲ را بیشتر کن» یا «نویز را کم کن»
بنویسد. این ماژول CIR فعلی + نتایج آنالیز (اختیاری) + دستور کاربر را به
LLM می‌فرستد و CIR اصلاح‌شده + توضیح تغییرات را برمی‌گرداند.
"""

from __future__ import annotations

import json
from typing import Any

from core.cir import Circuit
from core.interfaces.circuit_improver import CircuitImprover
from core.llm.client import LLMClient, LLMError
from core.llm.prompt_loader import load_prompt


class CircuitImproverError(Exception):
    pass


class LLMCircuitImprover(CircuitImprover):
    """بهبود مدار با راهنمایی LLM."""

    def __init__(self, client: LLMClient | None = None) -> None:
        self.client = client or LLMClient()
        self.system_prompt = load_prompt("circuit_improver_system")

    def improve(
        self,
        circuit: Circuit,
        goal: str,
        analysis_results: dict[str, Any] | None = None,
    ) -> tuple[Circuit, str]:
        if not goal.strip():
            raise CircuitImproverError("هدف بهبود مدار نمی‌تواند خالی باشد.")

        cir_json = circuit.model_dump()
        analysis_text = ""
        if analysis_results:
            voltages = analysis_results.get("node_voltages", {})
            currents = analysis_results.get("branch_currents", {})
            lines = ["نتایج تحلیل DC فعلی:"]
            for node, v in voltages.items():
                lines.append(f"  ولتاژ گره {node}: {v:.4f} V")
            for branch, i in currents.items():
                lines.append(f"  جریان {branch}: {i:.4e} A")
            analysis_text = "\n".join(lines)

        user_message = f"""مدار فعلی (CIR):
{json.dumps(cir_json, ensure_ascii=False, indent=2)}

{analysis_text}

دستور بهبود: {goal}"""

        try:
            raw = self.client.chat(self.system_prompt, user_message)
        except LLMError as exc:
            raise CircuitImproverError(str(exc)) from exc

        # پاسخ باید JSON باشد با دو کلید: "circuit" و "explanation"
        from core.llm.client import _strip_code_fences
        cleaned = _strip_code_fences(raw)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # اگر LLM فقط JSON نبود، سعی می‌کنیم circuit را از text استخراج کنیم
            raise CircuitImproverError(
                f"مدل پاسخ JSON معتبر ندهاد. پاسخ خام:\n{raw[:500]}"
            ) from None

        explanation = data.get("explanation", "تغییرات اعمال شد.")

        try:
            new_circuit = Circuit.model_validate(data["circuit"])
        except Exception as exc:
            raise CircuitImproverError(
                f"CIR بازگشتی از مدل معتبر نیست: {exc}"
            ) from exc

        issues = new_circuit.validate_circuit()
        if issues:
            new_circuit.metadata["validation_warnings"] = issues

        return new_circuit, explanation

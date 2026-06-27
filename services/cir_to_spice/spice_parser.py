"""
پارسر نت‌لیست SPICE -> CIR

این فایل جایگزین r/parser.py قدیمی است. به جای دیکشنری‌های
heterogeneous (که برای هر نوع المان کلیدهای متفاوتی داشتند)،
خروجی همیشه یک `Circuit` معتبر است.
"""

from __future__ import annotations

from core.cir import Circuit, Component, ComponentType
from core.interfaces.spice_to_cir import SpiceToCIR

# نگاشت پیشوند SPICE به نوع CIR.
# توجه: Q و M و J و D و X به صورت جدا مدیریت می‌شوند چون نوع دقیق
# (NPN/PNP, N/P-MOSFET, opamp/IC) از روی نت‌لیست خام به‌سختی قابل تشخیص
# است؛ مقدار پیش‌فرض منطقی انتخاب می‌شود و کاربر می‌تواند بعداً اصلاح کند.
PREFIX_TO_TYPE: dict[str, ComponentType] = {
    "R": ComponentType.RESISTOR,
    "C": ComponentType.CAPACITOR,
    "L": ComponentType.INDUCTOR,
    "V": ComponentType.VOLTAGE_SOURCE,
    "I": ComponentType.CURRENT_SOURCE,
    "D": ComponentType.DIODE,
    "Q": ComponentType.BJT_NPN,
    "M": ComponentType.MOSFET_N,
    "J": ComponentType.JFET,
    "X": ComponentType.IC,
    "U": ComponentType.IC,
}

# حداقل تعداد توکن (شامل نام المان) برای هر پیشوند، یعنی نام + گره‌ها + مقدار/مدل
MIN_TOKENS: dict[str, int] = {
    "D": 4,  # D1 a k MODEL
    "Q": 5,  # Q1 c b e MODEL
    "M": 6,  # M1 d g s b MODEL
    "J": 5,  # J1 d g s MODEL
}
DEFAULT_MIN_TOKENS = 4  # name node1 node2 value


class SpiceParseError(Exception):
    pass


class BasicSpiceToCIR(SpiceToCIR):
    """پارسر ساده نت‌لیست SPICE برای المان‌های دو و چندپایه پایه."""

    def parse(self, netlist: str) -> Circuit:
        components: list[Component] = []
        metadata: dict = {}

        for raw_line in netlist.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line.lower().startswith(".title"):
                metadata["title"] = line[len(".title"):].strip()
                continue

            if line.startswith("*") or line.startswith("."):
                continue  # کامنت یا دستور SPICE؛ نادیده گرفته می‌شود

            comp = self._parse_line(line)
            if comp is not None:
                components.append(comp)

        circuit = Circuit(components=components, metadata=metadata)
        return circuit

    def _parse_line(self, line: str) -> Component | None:
        parts = line.split()
        if not parts:
            return None

        name = parts[0]
        prefix = name[0].upper()
        comp_type = PREFIX_TO_TYPE.get(prefix)
        if comp_type is None:
            # نوع ناشناخته؛ به جای شکستن کل پارس، این خط نادیده گرفته می‌شود
            return None

        min_tokens = MIN_TOKENS.get(prefix, DEFAULT_MIN_TOKENS)
        if len(parts) < min_tokens:
            return None

        if prefix in ("D",):
            nodes = parts[1:3]
            value = parts[3] if len(parts) > 3 else None
        elif prefix == "Q":
            nodes = parts[1:4]  # collector, base, emitter
            value = parts[4] if len(parts) > 4 else None
        elif prefix == "M":
            nodes = parts[1:5]  # drain, gate, source, body
            value = parts[5] if len(parts) > 5 else None
        elif prefix == "J":
            nodes = parts[1:4]  # drain, gate, source
            value = parts[4] if len(parts) > 4 else None
        elif prefix in ("X", "U"):
            # آخرین توکن مدل/زیرمدار، بقیه گره‌ها هستند
            nodes = parts[1:-1]
            value = parts[-1]
        else:
            nodes = parts[1:3]
            value = " ".join(parts[3:]) if len(parts) > 3 else None

        return Component(
            id=name,
            type=comp_type,
            value=value,
            nodes=nodes,
            label=name,
        )

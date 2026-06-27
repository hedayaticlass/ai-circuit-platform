"""
ترتیب استاندارد پایه‌های هر نوع المان.

این فایل به صورت مرکزی تعریف می‌کند که آرایه `nodes` در یک Component
برای هر نوع المان به چه معناست. تمام ماژول‌هایی که با پایه‌های
چندتایی (ترانزیستور، MOSFET، opamp، ...) کار می‌کنند باید از این
مرجع استفاده کنند تا ناهماهنگی بین ماژول‌ها رخ ندهد.
"""

from __future__ import annotations

from core.cir.schema import ComponentType

# نام هر پایه به ترتیب در آرایه nodes
PIN_ORDER: dict[ComponentType, list[str]] = {
    ComponentType.RESISTOR: ["a", "b"],
    ComponentType.CAPACITOR: ["a", "b"],
    ComponentType.INDUCTOR: ["a", "b"],
    ComponentType.VOLTAGE_SOURCE: ["positive", "negative"],
    ComponentType.CURRENT_SOURCE: ["positive", "negative"],
    ComponentType.DIODE: ["anode", "cathode"],
    ComponentType.BJT_NPN: ["collector", "base", "emitter"],
    ComponentType.BJT_PNP: ["collector", "base", "emitter"],
    ComponentType.MOSFET_N: ["drain", "gate", "source", "body"],
    ComponentType.MOSFET_P: ["drain", "gate", "source", "body"],
    ComponentType.JFET: ["drain", "gate", "source"],
    ComponentType.OPAMP: ["out", "in_pos", "in_neg", "vcc", "vee"],
    ComponentType.IC: [],  # متغیر است؛ به properties["pin_names"] مراجعه شود
    ComponentType.GROUND: ["node"],
}


def pin_name(component_type: ComponentType, index: int) -> str:
    """نام پایه را بر اساس اندیس آن در آرایه nodes برمی‌گرداند.

    اگر تعریف نشده باشد، یک نام عمومی برمی‌گرداند (pin0, pin1, ...).
    """
    names = PIN_ORDER.get(component_type, [])
    if index < len(names):
        return names[index]
    return f"pin{index}"

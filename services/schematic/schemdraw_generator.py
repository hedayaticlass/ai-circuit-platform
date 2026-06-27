"""
تولید شماتیک از CIR با استفاده از schemdraw.

این ماژول جایگزین رویکرد قدیمی است که از AI می‌خواست کد matplotlib
کامل تولید کند (که غیرقابل‌اعتماد و سخت برای نگهداری بود). اینجا
رسم به صورت دترمینیستیک و بر اساس نوع المان در CIR انجام می‌شود.

محدودیت فعلی: چیدمان (layout) ساده و خطی است؛ المان‌ها به ترتیب
از چپ به راست روی یک خط افقی چیده می‌شوند و گره‌های مشترک با سیم
به هم وصل می‌شوند. برای مدارهای پیچیده، در آینده یک الگوریتم
layout مناسب‌تر (graph-based) جایگزین می‌شود.
"""

from __future__ import annotations

from pathlib import Path

import schemdraw
import schemdraw.elements as elm

from core.cir import Circuit, Component, ComponentType
from core.interfaces.schematic_generator import SchematicGenerator

# نگاشت نوع CIR به المان schemdraw
ELEMENT_MAP = {
    ComponentType.RESISTOR: elm.Resistor,
    ComponentType.CAPACITOR: elm.Capacitor,
    ComponentType.INDUCTOR: elm.Inductor,
    ComponentType.VOLTAGE_SOURCE: elm.SourceV,
    ComponentType.CURRENT_SOURCE: elm.SourceI,
    ComponentType.DIODE: elm.Diode,
    ComponentType.BJT_NPN: elm.BjtNpn,
    ComponentType.BJT_PNP: elm.BjtPnp,
    ComponentType.MOSFET_N: elm.NMos,
    ComponentType.MOSFET_P: elm.PMos,
}


class SchematicGenerationError(Exception):
    pass


class SchemdrawSchematicGenerator(SchematicGenerator):
    """تولید شماتیک ساده و خطی با schemdraw."""

    def render(self, circuit: Circuit, output_path: str | Path) -> Path:
        if not circuit.components:
            raise SchematicGenerationError("مدار خالی است؛ شماتیکی برای رسم وجود ندارد.")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with schemdraw.Drawing(file=str(output_path), show=False) as d:
            for comp in circuit.components:
                self._add_element(d, comp)

        return output_path

    def _add_element(self, drawing: schemdraw.Drawing, comp: Component) -> None:
        element_cls = ELEMENT_MAP.get(comp.type)

        if element_cls is None:
            # برای انواعی که هنوز map نشده‌اند (opamp, ic, ...) یک
            # placeholder ساده (مستطیل با برچسب) رسم می‌شود.
            element = elm.RBox().label(self._label(comp))
            drawing.add(element)
            return

        element = element_cls().label(self._label(comp))
        drawing.add(element)

    @staticmethod
    def _label(comp: Component) -> str:
        text = comp.label or comp.id
        if comp.value:
            text += f"\n{comp.value}"
        return text

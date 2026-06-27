"""
Circuit Intermediate Representation (CIR)
==========================================

این فایل قلب پروژه است. تمام ماژول‌ها (text-to-CIR، CIR-to-SPICE،
schematic generator، تحلیل‌گر و غیره) باید ورودی/خروجی خود را بر
اساس این schema تعریف کنند.

هر تغییری در این فایل باید با دقت و با هماهنگی کل تیم انجام شود،
چون همه ماژول‌ها به آن وابسته‌اند.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ComponentType(str, Enum):
    """انواع پشتیبانی‌شده‌ی المان‌های مدار.

    در صورت نیاز به نوع جدید، اینجا اضافه کنید و مطمئن شوید
    ماژول‌های cir_to_spice و schematic هم آن را پشتیبانی می‌کنند.
    """

    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    VOLTAGE_SOURCE = "voltage_source"
    AC_VOLTAGE_SOURCE = "ac_voltage_source"   # VAC: سینوسی با دامنه/فرکانس/offset
    CURRENT_SOURCE = "current_source"
    DIODE = "diode"
    BJT_NPN = "bjt_npn"
    BJT_PNP = "bjt_pnp"
    MOSFET_N = "mosfet_n"
    MOSFET_P = "mosfet_p"
    JFET = "jfet"
    OPAMP = "opamp"
    IC = "ic"
    GROUND = "ground"


# تعداد پایه‌های استاندارد برای هر نوع المان.
# برای IC و opamp ممکن است متغیر باشد، پس اینجا فقط حداقل را مشخص می‌کنیم.
COMPONENT_PIN_COUNT: dict[ComponentType, int] = {
    ComponentType.RESISTOR: 2,
    ComponentType.CAPACITOR: 2,
    ComponentType.INDUCTOR: 2,
    ComponentType.VOLTAGE_SOURCE: 2,
    ComponentType.AC_VOLTAGE_SOURCE: 2,
    ComponentType.CURRENT_SOURCE: 2,
    ComponentType.DIODE: 2,
    ComponentType.BJT_NPN: 3,
    ComponentType.BJT_PNP: 3,
    ComponentType.MOSFET_N: 4,
    ComponentType.MOSFET_P: 4,
    ComponentType.JFET: 3,
    ComponentType.OPAMP: 5,
    ComponentType.IC: 2,  # حداقل؛ IC می‌تواند بیشتر داشته باشد
    ComponentType.GROUND: 1,
}


class Component(BaseModel):
    """یک المان مدار.

    `nodes` ترتیب پایه‌ها را مشخص می‌کند. ترتیب برای هر نوع المان
    معنی‌دار است (مثلاً برای BJT_NPN: [collector, base, emitter]).
    این ترتیب در `core/cir/pin_order.py` به صورت مرکزی تعریف شده است.
    """

    id: str = Field(..., description="شناسه یکتای المان، مثل R1, C2, Q1")
    type: ComponentType
    value: str | None = Field(
        default=None,
        description="مقدار المان به صورت رشته، مثل '1k', '10uF', '5V'. "
        "برای ترانزیستور/دیود/IC می‌تواند نام مدل باشد، مثل '2N2222'.",
    )
    nodes: list[str] = Field(
        ..., description="فهرست گره‌های متصل به این المان، به ترتیب پایه‌ها"
    )
    label: str | None = Field(
        default=None, description="برچسب نمایشی اختیاری (برای شماتیک)"
    )
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="ویژگی‌های اضافی خاص نوع المان یا ابزار (مثل موقعیت در شماتیک)",
    )

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("شناسه المان نمی‌تواند خالی باشد")
        return v.strip()

    @field_validator("nodes")
    @classmethod
    def nodes_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("یک المان باید حداقل یک گره داشته باشد")
        return v


class Circuit(BaseModel):
    """نمایش کامل یک مدار: لیستی از المان‌ها به همراه متادیتا.

    گره "0" به صورت قراردادی به عنوان زمین (ground) در نظر گرفته می‌شود،
    مگر اینکه در metadata مقدار دیگری مشخص شود.
    """

    components: list[Component] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="اطلاعات اضافی مثل عنوان مدار، توضیحات، زبان، نسخه CIR و ...",
    )

    @property
    def ground_node(self) -> str:
        return str(self.metadata.get("ground_node", "0"))

    def get_node_names(self) -> set[str]:
        """مجموعه‌ی تمام گره‌های استفاده‌شده در مدار."""
        nodes: set[str] = set()
        for comp in self.components:
            nodes.update(comp.nodes)
        return nodes

    def find_component(self, component_id: str) -> Component | None:
        for comp in self.components:
            if comp.id == component_id:
                return comp
        return None

    def validate_circuit(self) -> list[str]:
        """بررسی‌های منطقی ساده روی مدار و بازگرداندن فهرست هشدارها/خطاها.

        این متد استثنا پرتاب نمی‌کند؛ فقط فهرستی از پیام‌ها برمی‌گرداند
        تا لایه‌های بالاتر (API) تصمیم بگیرند چطور به کاربر نشان دهند.
        """
        issues: list[str] = []

        if not self.components:
            issues.append("مدار هیچ المانی ندارد.")
            return issues

        seen_ids: set[str] = set()
        for comp in self.components:
            if comp.id in seen_ids:
                issues.append(f"شناسه تکراری: {comp.id}")
            seen_ids.add(comp.id)

            expected = COMPONENT_PIN_COUNT.get(comp.type)
            if expected is not None and len(comp.nodes) < expected:
                issues.append(
                    f"المان {comp.id} از نوع {comp.type.value} باید حداقل "
                    f"{expected} گره داشته باشد، اما {len(comp.nodes)} گره دارد."
                )

        if self.ground_node not in self.get_node_names():
            issues.append(
                f"گره زمین ('{self.ground_node}') در هیچ المانی استفاده نشده است."
            )

        issues.extend(self._find_floating_nodes())
        issues.extend(self._find_shorted_voltage_sources())

        return issues

    def _find_floating_nodes(self) -> list[str]:
        """گره‌هایی که فقط یک پایه به آن‌ها وصل است (بن‌بست الکتریکی).

        چنین گره‌ای مسیر کامل برای جریان نمی‌سازد و باعث می‌شود ngspice
        نتواند آنالیز DC را حل کند (یا هشدار/خطای داخلی بدهد).
        """
        node_degree: dict[str, int] = {}
        for comp in self.components:
            for node in comp.nodes:
                node_degree[node] = node_degree.get(node, 0) + 1

        issues = []
        for node, degree in node_degree.items():
            if degree == 1 and node != self.ground_node:
                issues.append(
                    f"گره '{node}' فقط به یک پایه وصل است (مسیر بسته‌ای برای "
                    f"جریان وجود ندارد). هر گره باید حداقل به دو پایه از دو "
                    f"المان مختلف (یا یک حلقه‌ی کامل تا زمین) وصل باشد."
                )
        return issues

    def _find_shorted_voltage_sources(self) -> list[str]:
        """منبع ولتاژ ایده‌آلی که مستقیماً موازی با یک مسیر مقاومت-صفر
        (سلف در DC، یا منبع ولتاژ دیگر) قرار گرفته باشد.

        این حالت از نظر ریاضی برای SPICE قابل‌حل نیست (ماتریس singular) و
        دقیقاً همان چیزی است که خطای مبهم 'Command run failed' را در
        ngspice ایجاد می‌کند. اینجا قبل از رسیدن به ngspice تشخیص داده
        و با پیام واضح فارسی گزارش می‌شود.
        """
        # مجموعه‌ی (frozenset از دو گره) برای هر منبع ولتاژ و هر سلف
        voltage_pairs: dict[frozenset, list[str]] = {}
        zero_dc_resistance_pairs: dict[frozenset, list[str]] = {}

        for comp in self.components:
            if len(comp.nodes) != 2:
                continue
            pair = frozenset(comp.nodes)
            if comp.type == ComponentType.VOLTAGE_SOURCE:
                voltage_pairs.setdefault(pair, []).append(comp.id)
            elif comp.type == ComponentType.INDUCTOR:
                zero_dc_resistance_pairs.setdefault(pair, []).append(comp.id)

        issues = []
        for pair, v_ids in voltage_pairs.items():
            # دو منبع ولتاژ مختلف روی یک جفت گره
            if len(v_ids) > 1:
                issues.append(
                    f"منابع ولتاژ {', '.join(v_ids)} هر دو دقیقاً بین گره‌های "
                    f"یکسان قرار دارند (موازی با هم) — این برای SPICE قابل‌حل نیست."
                )
            # منبع ولتاژ موازی با سلف (که در DC اتصال کوتاه است)
            shorting = zero_dc_resistance_pairs.get(pair, [])
            if shorting:
                issues.append(
                    f"منبع ولتاژ {', '.join(v_ids)} مستقیماً موازی با سلف "
                    f"{', '.join(shorting)} است. سلف در تحلیل DC مانند یک سیم "
                    f"بدون مقاومت عمل می‌کند، پس این منبع ولتاژ توسط آن اتصال "
                    f"کوتاه می‌شود (خطای حل‌ناپذیر برای SPICE). یک مقاومت کوچک "
                    f"بین این دو المان اضافه کنید یا توپولوژی را اصلاح کنید."
                )
        return issues


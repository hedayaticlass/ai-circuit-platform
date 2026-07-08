from core.cir import Circuit, Component, ComponentType
from services.cir_to_spice.basic_converter import BasicCIRToSpice


def test_expanded_model_library_1n4007_2n3904_irf540():
    """پارت‌نامبرهای واقعی رایج که LLM اغلب تولید می‌کند (خارج از کتابخانه‌ی
    اولیه) باید بدون خطا با تعریف .model درست پشتیبانی شوند."""
    circuit = Circuit(
        components=[
            Component(id="D1", type=ComponentType.DIODE, value="1N4007", nodes=["1", "0"]),
            Component(id="Q1", type=ComponentType.BJT_NPN, value="2N3904", nodes=["1", "2", "0"]),
            Component(id="M1", type=ComponentType.MOSFET_N, value="IRF540", nodes=["1", "2", "0"]),
        ]
    )
    netlist = BasicCIRToSpice().convert(circuit)

    assert "D1 1 0 1N4007" in netlist
    assert ".model 1N4007 D(" in netlist
    assert "Q1 1 2 0 2N3904" in netlist
    assert ".model 2N3904 NPN(" in netlist
    assert "M1 1 2 0 0 IRF540" in netlist
    assert ".model IRF540 NMOS(" in netlist


def test_model_lookup_is_case_insensitive():
    circuit = Circuit(
        components=[
            Component(id="D1", type=ComponentType.DIODE, value="1n4007", nodes=["1", "0"]),
        ]
    )
    netlist = BasicCIRToSpice().convert(circuit)
    # نام کانونیک با حروف بزرگ در نت‌لیست نوشته شود، نه ورودی خام
    assert "D1 1 0 1N4007" in netlist
    assert ".model 1N4007 D(" in netlist


def test_zener_voltage_value_synthesizes_dynamic_model():
    """وقتی value یک دیود پارت‌نامبر واقعی نیست بلکه یک ولتاژ است (مثل
    توصیف «دیود زنر ۵ ولت»)، باید به‌جای خطای ngspice، یک مدل زنر
    سنتزشده با همان ولتاژ شکست (Bv) تولید شود."""
    circuit = Circuit(
        components=[
            Component(id="V1", type=ComponentType.VOLTAGE_SOURCE, value="12V", nodes=["1", "0"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="470", nodes=["1", "2"]),
            Component(id="D1", type=ComponentType.DIODE, value="5.1V", nodes=["0", "2"]),
        ],
        metadata={"title": "Zener regulator"},
    )
    netlist = BasicCIRToSpice().convert(circuit)

    assert "D1 0 2 ZD5V1" in netlist
    assert ".model ZD5V1 D(" in netlist
    assert "Bv=5.10" in netlist


def test_zener_value_with_comma_decimal_and_zener_prefix():
    circuit = Circuit(
        components=[
            Component(id="D1", type=ComponentType.DIODE, value="zener 3,3V", nodes=["1", "0"]),
        ]
    )
    netlist = BasicCIRToSpice().convert(circuit)
    assert "D1 1 0 ZD3V3" in netlist
    assert "Bv=3.30" in netlist


def test_unknown_diode_value_passes_through_unchanged():
    """اگر value نه پارت‌نامبر شناخته‌شده باشد و نه به شکل ولتاژ، بدون
    تغییر منتقل می‌شود (کاربر باید .model آن را خودش اضافه کند)."""
    circuit = Circuit(
        components=[
            Component(id="D1", type=ComponentType.DIODE, value="BAT54", nodes=["1", "0"]),
        ]
    )
    netlist = BasicCIRToSpice().convert(circuit)
    assert "D1 1 0 BAT54" in netlist
    assert ".model BAT54" not in netlist


def test_opamp_model_output_is_bounded():
    """مدل op-amp باید بهره را با max/min به ±13V محدود کند تا مدارهای
    فیدبک‌دار با بهره باز واقعی همگرا شوند (نه یک Egain بدون سقف)."""
    circuit = Circuit(
        components=[
            Component(id="V1", type=ComponentType.VOLTAGE_SOURCE, value="5V", nodes=["1", "0"]),
            Component(id="X1", type=ComponentType.OPAMP, value="LM741", nodes=["3", "1", "2"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["2", "0"]),
            Component(id="R2", type=ComponentType.RESISTOR, value="10k", nodes=["2", "3"]),
        ]
    )
    netlist = BasicCIRToSpice().convert(circuit)

    assert "max(min(200k*V(in_pos,in_neg), 13), -13)" in netlist
    assert ".subckt LM741" in netlist
    assert ".ends LM741" in netlist

from core.cir import Circuit, Component, ComponentType


def test_circuit_validate_simple_ok():
    circuit = Circuit(
        components=[
            Component(id="V1", type=ComponentType.VOLTAGE_SOURCE, value="5V", nodes=["1", "0"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "0"]),
        ],
        metadata={"title": "ساده‌ترین مدار ممکن"},
    )
    assert circuit.validate_circuit() == []


def test_circuit_validate_missing_ground():
    circuit = Circuit(
        components=[
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "2"]),
        ]
    )
    issues = circuit.validate_circuit()
    assert any("زمین" in issue for issue in issues)


def test_circuit_validate_duplicate_id():
    circuit = Circuit(
        components=[
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "0"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="2k", nodes=["1", "0"]),
        ]
    )
    issues = circuit.validate_circuit()
    assert any("تکراری" in issue for issue in issues)


def test_circuit_validate_insufficient_pins():
    circuit = Circuit(
        components=[
            Component(id="Q1", type=ComponentType.BJT_NPN, value="2N2222", nodes=["1", "2"]),
        ]
    )
    issues = circuit.validate_circuit()
    assert any("Q1" in issue for issue in issues)

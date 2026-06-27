import pytest

from core.cir import Circuit, Component, ComponentType
from services.cir_to_spice.basic_converter import BasicCIRToSpice, CIRToSpiceError


def test_simple_rc_circuit_to_spice():
    circuit = Circuit(
        components=[
            Component(id="V1", type=ComponentType.VOLTAGE_SOURCE, value="5V", nodes=["1", "0"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "2"]),
            Component(id="C1", type=ComponentType.CAPACITOR, value="10uF", nodes=["2", "0"]),
        ],
        metadata={"title": "RC Circuit"},
    )

    netlist = BasicCIRToSpice().convert(circuit)
    lines = netlist.splitlines()

    assert lines[0] == ".title RC Circuit"
    assert "V1 1 0 5V" in lines
    assert "R1 1 2 1k" in lines
    assert "C1 2 0 10uF" in lines
    assert lines[-1] == ".end"


def test_diode_uses_default_model_when_no_value():
    circuit = Circuit(
        components=[
            Component(id="D1", type=ComponentType.DIODE, nodes=["1", "0"]),
        ]
    )
    netlist = BasicCIRToSpice().convert(circuit)
    assert "D1 1 0 D1N4148" in netlist


def test_empty_circuit_raises():
    circuit = Circuit(components=[])
    with pytest.raises(CIRToSpiceError):
        BasicCIRToSpice().convert(circuit)


def test_unsupported_type_raises():
    circuit = Circuit(
        components=[
            Component(id="G1", type=ComponentType.GROUND, nodes=["0"]),
        ]
    )
    with pytest.raises(CIRToSpiceError):
        BasicCIRToSpice().convert(circuit)

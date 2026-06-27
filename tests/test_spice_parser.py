from core.cir import ComponentType
from services.cir_to_spice.spice_parser import BasicSpiceToCIR


NETLIST = """\
.title RC Circuit
V1 1 0 5V
R1 1 2 1k
C1 2 0 10uF
.end
"""


def test_parse_basic_netlist():
    circuit = BasicSpiceToCIR().parse(NETLIST)

    assert circuit.metadata["title"] == "RC Circuit"
    assert len(circuit.components) == 3

    v1 = circuit.find_component("V1")
    assert v1.type == ComponentType.VOLTAGE_SOURCE
    assert v1.nodes == ["1", "0"]
    assert v1.value == "5V"

    r1 = circuit.find_component("R1")
    assert r1.type == ComponentType.RESISTOR
    assert r1.nodes == ["1", "2"]
    assert r1.value == "1k"


def test_parse_transistor():
    netlist = "Q1 2 1 0 2N3904\n"
    circuit = BasicSpiceToCIR().parse(netlist)
    q1 = circuit.find_component("Q1")
    assert q1.type == ComponentType.BJT_NPN
    assert q1.nodes == ["2", "1", "0"]  # collector, base, emitter
    assert q1.value == "2N3904"


def test_parse_ignores_comments_and_unknown_prefixes():
    netlist = "* this is a comment\n.options foo\nZ1 1 0 weird\nR1 1 0 1k\n"
    circuit = BasicSpiceToCIR().parse(netlist)
    assert len(circuit.components) == 1
    assert circuit.components[0].id == "R1"

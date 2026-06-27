from core.cir import Circuit, Component, ComponentType


def test_floating_node_detected():
    circuit = Circuit(
        components=[
            Component(id="V1", type=ComponentType.VOLTAGE_SOURCE, value="5V", nodes=["1", "0"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "2"]),
            # گره '2' فقط یک پایه دارد (بن‌بست)
        ]
    )
    issues = circuit.validate_circuit()
    assert any("بن‌بست" in issue or "فقط به یک پایه" in issue for issue in issues)


def test_voltage_source_parallel_with_inductor_detected():
    """دقیقاً سناریوی واقعی گزارش‌شده توسط کاربر:
    R1(1-2), L1(2-3), C1(3-0), V2(3-2) -> V2 موازی با L1
    """
    circuit = Circuit(
        components=[
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "2"]),
            Component(id="L1", type=ComponentType.INDUCTOR, value="10mH", nodes=["2", "3"]),
            Component(id="C1", type=ComponentType.CAPACITOR, value="100nF", nodes=["3", "0"]),
            Component(id="V2", type=ComponentType.VOLTAGE_SOURCE, value="5", nodes=["3", "2"]),
        ]
    )
    issues = circuit.validate_circuit()
    assert any("موازی با سلف" in issue for issue in issues)
    # گره ۱ هم در این مدار بلاتکلیف است (فقط R1 به آن وصل است)
    assert any("بن‌بست" in issue or "فقط به یک پایه" in issue for issue in issues)


def test_two_voltage_sources_same_nodes_detected():
    circuit = Circuit(
        components=[
            Component(id="V1", type=ComponentType.VOLTAGE_SOURCE, value="5V", nodes=["1", "0"]),
            Component(id="V2", type=ComponentType.VOLTAGE_SOURCE, value="3V", nodes=["1", "0"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "0"]),
        ]
    )
    issues = circuit.validate_circuit()
    assert any("هر دو دقیقاً بین گره‌های یکسان" in issue for issue in issues)


def test_valid_series_circuit_has_no_topology_issues():
    circuit = Circuit(
        components=[
            Component(id="V1", type=ComponentType.VOLTAGE_SOURCE, value="5V", nodes=["1", "0"]),
            Component(id="R1", type=ComponentType.RESISTOR, value="1k", nodes=["1", "2"]),
            Component(id="L1", type=ComponentType.INDUCTOR, value="10mH", nodes=["2", "3"]),
            Component(id="C1", type=ComponentType.CAPACITOR, value="100nF", nodes=["3", "0"]),
        ]
    )
    assert circuit.validate_circuit() == []

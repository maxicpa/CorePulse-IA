from corepulse_ai.context import compact_measured_data, normalize_telemetry


def test_missing_temperature_becomes_na():
    data = compact_measured_data(normalize_telemetry({"cpu_usage": 96}))
    assert data["cpu_temperature"] == "N/A"


def test_real_values_are_preserved():
    data = compact_measured_data(normalize_telemetry({"cpu_usage": 96, "cpu_temperature": 94, "ram_usage": 72}))
    assert data["cpu_usage"] == "96 %"
    assert data["cpu_temperature"] == "94 °C"
    assert data["ram_usage"] == "72 %"

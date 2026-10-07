from pathlib import Path
import json
import pytest

from corepulse_ai.pipeline import CorePulseAIPipeline
from corepulse_ai.providers import MockProvider

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "knowledge" / "corepulse_ai"
EXAMPLES = ROOT / "examples" / "corepulse_ai"

CASES = [
    ("gpu", "Analiza la GPU y su temperatura.", "telemetry_gpu_load.json", "gpu_usage"),
    ("memory", "Analiza el uso de RAM y memoria.", "telemetry_memory_high.json", "ram_usage"),
    ("storage", "Analiza el uso del SSD y almacenamiento.", "telemetry_storage_high.json", "storage_usage"),
    ("network", "Analiza la latencia de red y ping.", "telemetry_network_latency.json", "network_latency_ms"),
    ("system", "Analiza la salud del sistema Windows.", "telemetry_system_mixed.json", "system_status"),
    ("general", "Dame una evaluación general del equipo.", "telemetry_general.json", "cpu_usage"),
]

@pytest.mark.parametrize("route,query,filename,field", CASES)
def test_all_routes_are_reproducible(route, query, filename, field):
    telemetry = json.loads((EXAMPLES / filename).read_text(encoding="utf-8"))
    result = CorePulseAIPipeline(MockProvider(), KNOWLEDGE).run(query, telemetry)
    assert result["route"] == route
    assert result["measured_data"][field] != "N/A"
    assert result["validation"]["valid"] is True
    assert 1 <= len(result["retrieved_sources"]) <= 4
    types = {s["type"] for s in result["retrieved_sources"]}
    assert "internal" in types
    assert "external" in types

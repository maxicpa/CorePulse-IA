from pathlib import Path

from corepulse_ai.pipeline import CorePulseAIPipeline
from corepulse_ai.providers import MockProvider


ROOT = Path(__file__).resolve().parents[2]


def test_traceability_assigns_s_ids():
    result = CorePulseAIPipeline(MockProvider(), ROOT / "knowledge" / "corepulse_ai").run(
        "Analiza CPU y temperatura",
        {"cpu_usage": 96, "cpu_temperature": 94, "ram_usage": 72},
    )
    ids = [item["id"] for item in result["retrieved_sources"]]
    assert ids
    assert ids[0] == "S1"
    assert len(ids) <= 4
    assert ids == [item["source_id"] for item in result["retrieval_trace"]]
    assert {item["type"] for item in result["retrieved_sources"]} >= {"internal", "external"}
    assert result["prompt_contract_version"] == "3.2"
    assert result["validation"]["valid"] is True

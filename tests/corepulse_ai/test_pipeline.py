import json
from pathlib import Path

from corepulse_ai.pipeline import CorePulseAIPipeline
from corepulse_ai.providers import LLMProvider, MockProvider


ROOT = Path(__file__).resolve().parents[2]


class HallucinatingProvider(LLMProvider):
    provider_name = "hallucinating-test-provider"
    model_name = "malicious-fixture"
    is_real_llm = False

    def __init__(self):
        self.last_prompt = ""

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return json.dumps(
            {
                "measured_data": {"cpu_temperature": "81 °C"},
                "interpretation": "La temperatura de CPU está alta en 81 °C.",
                "retrieved_information": ["Información técnica controlada [S1]."],
                "recommendations": ["Revisar refrigeración [S1]."],
                "sources": [{"id": "S99", "title": "inventada", "source": "inventada"}],
            },
            ensure_ascii=False,
        )


def test_pipeline_does_not_invent_missing_temperature():
    telemetry = {"cpu_usage": 96, "cpu_temperature": "N/A", "ram_usage": 72}

    # Caso normal: N/A permanece N/A y la salida supera validación.
    result = CorePulseAIPipeline(MockProvider(), ROOT / "knowledge" / "corepulse_ai").run(
        "Analiza la CPU",
        telemetry,
    )
    assert result["response"]["measured_data"]["cpu_temperature"] == "N/A"
    assert result["validation"]["valid"] is True

    # Caso adversarial: aunque el proveedor intente cambiar el sensor, el dato
    # medido es impuesto por Python y la interpretación inventada se rechaza.
    malicious = HallucinatingProvider()
    rejected = CorePulseAIPipeline(malicious, ROOT / "knowledge" / "corepulse_ai").run(
        "Analiza la CPU",
        telemetry,
    )
    assert rejected["response"]["measured_data"]["cpu_temperature"] == "N/A"
    assert rejected["validation"]["valid"] is False
    assert any("cpu_temperature" in error for error in rejected["validation"]["errors"])

    # El contrato está presente en el prompt que vio el modelo.
    assert "<VERIFIED_TELEMETRY>" in malicious.last_prompt
    assert "<RAG_SOURCES>" in malicious.last_prompt
    assert "REAL_OR_NA" in malicious.last_prompt
    assert "USER_QUERY_UNTRUSTED" in malicious.last_prompt

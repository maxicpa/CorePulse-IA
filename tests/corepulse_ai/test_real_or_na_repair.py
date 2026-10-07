import json
from pathlib import Path

from corepulse_ai.pipeline import CorePulseAIPipeline
from corepulse_ai.providers import LLMProvider
from corepulse_ai.validator import validate_response


ROOT = Path(__file__).resolve().parents[2]


class RepairOnceProvider(LLMProvider):
    provider_name = "repair-once-test"
    model_name = "fixture"
    is_real_llm = True

    def __init__(self):
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return json.dumps(
                {
                    "measured_data": {},
                    "interpretation": "La temperatura de CPU está alta en 81 °C.",
                    "retrieved_information": ["Información técnica [S1]."],
                    "recommendations": ["Revisar la carga [S1]."],
                    "sources": [],
                },
                ensure_ascii=False,
            )
        return json.dumps(
            {
                "measured_data": {},
                "interpretation": (
                    "El uso de CPU es alto. La temperatura de CPU está N/A, "
                    "por lo que no se puede evaluar si es alta, normal o baja."
                ),
                "retrieved_information": ["La política exige conservar N/A [S1]."],
                "recommendations": ["Revisar procesos activos sin asumir estado térmico [S1]."],
                "sources": [],
            },
            ensure_ascii=False,
        )


def test_na_uncertainty_can_mention_states_when_explicitly_negated():
    measured = {
        "cpu_usage": "96 %",
        "cpu_temperature": "N/A",
        "gpu_usage": "N/A",
        "gpu_temperature": "N/A",
        "ram_usage": "72 %",
        "storage_usage": "N/A",
        "network_latency_ms": "N/A",
        "system_status": "N/A",
    }
    response = {
        "measured_data": measured,
        "interpretation": (
            "La temperatura de CPU no está disponible; no se puede evaluar "
            "si es alta, normal o baja."
        ),
        "retrieved_information": [],
        "recommendations": [],
        "sources": [],
    }
    report = validate_response(response, measured, [])
    assert report.valid is True


def test_real_llm_gets_one_controlled_repair_attempt():
    telemetry = {
        "cpu_vendor": "AMD",
        "cpu_model": "AMD Ryzen 7 5800H",
        "cpu_usage": 96,
        "cpu_temperature": "N/A",
        "ram_usage": 72,
    }
    provider = RepairOnceProvider()
    result = CorePulseAIPipeline(provider, ROOT / "knowledge" / "corepulse_ai").run(
        "Analiza la CPU sin inventar la temperatura.",
        telemetry,
    )
    assert provider.calls == 2
    assert result["generation_attempts"] == 2
    assert result["validation_attempts"][0]["valid"] is False
    assert result["validation_attempts"][1]["valid"] is True
    assert result["validation"]["valid"] is True
    assert result["response"]["measured_data"]["cpu_temperature"] == "N/A"

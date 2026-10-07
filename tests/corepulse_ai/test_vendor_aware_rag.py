from pathlib import Path

from corepulse_ai.context import extract_hardware_context
from corepulse_ai.pipeline import CorePulseAIPipeline
from corepulse_ai.providers import MockProvider
from corepulse_ai.retriever import CorePulseRetriever

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "knowledge" / "corepulse_ai"


def test_amd_context_is_detected_from_model():
    ctx = extract_hardware_context({"cpu_model": "AMD Ryzen 7 5800H"})
    assert ctx == {"cpu_vendor": "AMD", "cpu_model": "AMD Ryzen 7 5800H"}


def test_amd_rag_prefers_amd_and_excludes_intel_specific_source():
    retriever = CorePulseRetriever(KNOWLEDGE)
    chunks, trace = retriever.retrieve_with_trace(
        "Analiza temperatura CPU",
        "cpu",
        hardware_context={"cpu_vendor": "AMD", "cpu_model": "AMD Ryzen 7 5800H"},
    )
    ids = {chunk.chunk_id for chunk in chunks}
    assert "EXT-AMD-RYZEN-5800H" in ids or "EXT-AMD-PROCESSOR-SPECS" in ids
    assert "EXT-INTEL-TJUNCTION" not in ids
    assert any(item.get("vendor_policy") == "vendor_match" for item in trace)


def test_intel_rag_excludes_amd_specific_sources():
    retriever = CorePulseRetriever(KNOWLEDGE)
    chunks, _ = retriever.retrieve_with_trace(
        "Analiza temperatura CPU",
        "cpu",
        hardware_context={"cpu_vendor": "Intel", "cpu_model": "Intel Core i7"},
    )
    ids = {chunk.chunk_id for chunk in chunks}
    assert "EXT-INTEL-TJUNCTION" in ids
    assert "EXT-AMD-RYZEN-5800H" not in ids
    assert "EXT-AMD-PROCESSOR-SPECS" not in ids


def test_pipeline_exposes_verified_hardware_context_and_prompt_contract_31():
    result = CorePulseAIPipeline(MockProvider(), KNOWLEDGE).run(
        "Analiza CPU",
        {"cpu_vendor": "AMD", "cpu_model": "AMD Ryzen 7 5800H", "cpu_usage": 96, "cpu_temperature": 94},
    )
    assert result["hardware_context"]["cpu_vendor"] == "AMD"
    assert result["prompt_contract_version"] == "3.2"
    assert all("INTEL" not in item["chunk_id"] for item in result["retrieved_sources"])

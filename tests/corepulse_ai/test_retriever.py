from pathlib import Path

from corepulse_ai.retriever import CorePulseRetriever


ROOT = Path(__file__).resolve().parents[2]


def test_rag_returns_internal_source():
    retriever = CorePulseRetriever(ROOT / "knowledge" / "corepulse_ai")
    chunks, trace = retriever.retrieve_with_trace("CPU temperatura telemetría", "cpu")
    assert any(c.source_type == "internal" for c in chunks)
    assert 1 <= len(chunks) <= 4
    assert len(trace) == len(chunks)
    assert all("score_components" in item for item in trace)


def test_rag_returns_external_source():
    retriever = CorePulseRetriever(ROOT / "knowledge" / "corepulse_ai")
    chunks, trace = retriever.retrieve_with_trace("CPU temperatura Intel", "cpu")
    assert any(c.source_type == "external" for c in chunks)
    assert any(c.source_type == "internal" for c in chunks)
    assert [item["source_id"] for item in trace] == [f"S{i}" for i in range(1, len(chunks) + 1)]

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core"))

from corepulse_ai.live_adapter import collect_live_corepulse_telemetry  # noqa: E402
from corepulse_ai.runtime_config import load_shared_env  # noqa: E402
from corepulse_ai.pipeline import CorePulseAIPipeline  # noqa: E402
from corepulse_ai.providers import GroqProvider, MockProvider, OllamaProvider  # noqa: E402


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def make_provider(name: str):
    if name == "mock":
        return MockProvider()
    if name == "groq":
        return GroqProvider()
    if name == "ollama":
        return OllamaProvider()
    raise ValueError(f"Proveedor no soportado: {name}")


def main() -> int:
    load_shared_env(ROOT)

    parser = argparse.ArgumentParser(description="CorePulse AI - CLI académico ISY0101")
    parser.add_argument("--provider", choices=["mock", "groq", "ollama"], default="mock")
    parser.add_argument("--query", default="¿Qué observas en el uso y temperatura de CPU?")
    parser.add_argument("--telemetry", default=str(ROOT / "examples" / "corepulse_ai" / "telemetry_cpu_hot.json"))
    parser.add_argument("--live", action="store_true", help="Usa telemetría real de core.telemetry en vez de un JSON de ejemplo.")
    parser.add_argument("--history", help="JSON opcional con historial [{role, content}, ...].")
    parser.add_argument("--evidence", help="Guarda evidencia JSON; demo_llm_real.json exige proveedor LLM real.")
    args = parser.parse_args()

    provider = make_provider(args.provider)
    pipeline = CorePulseAIPipeline(provider, ROOT / "knowledge" / "corepulse_ai")
    telemetry = collect_live_corepulse_telemetry() if args.live else load_json(args.telemetry)
    history = load_json(args.history) if args.history else None
    result = pipeline.run(args.query, telemetry, history=history)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.evidence:
        pipeline.save_evidence(result, args.evidence)

    return 0 if result["validation"]["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

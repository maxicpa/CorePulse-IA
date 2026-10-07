from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .context import compact_measured_data, extract_hardware_context, normalize_telemetry
from .conversation import normalize_history
from .models import KnowledgeChunk
from .prompts import PROMPT_CONTRACT_VERSION, build_prompt
from .providers import LLMProvider
from .retriever import CorePulseRetriever
from .routing import route_query
from .sanitization import sanitize_query
from .validator import parse_json_response, validate_response


class CorePulseAIPipeline:
    """Entrada -> sanitización -> routing -> RAG -> prompt -> LLM -> validación."""

    def __init__(self, provider: LLMProvider, knowledge_dir: str | Path):
        self.provider = provider
        self.retriever = CorePulseRetriever(knowledge_dir)

    @staticmethod
    def _source_manifest(chunks: list[KnowledgeChunk]) -> list[dict[str, str]]:
        return [
            {
                "id": f"S{idx}",
                "chunk_id": chunk.chunk_id,
                "type": chunk.source_type,
                "topic": chunk.topic,
                "title": chunk.title,
                "source": chunk.source,
            }
            for idx, chunk in enumerate(chunks, start=1)
        ]

    def run(
        self,
        query: str,
        telemetry: dict[str, Any],
        *,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        sanitized_query = sanitize_query(query)
        route = route_query(sanitized_query)
        normalized_history = normalize_history(history)
        hardware_context = extract_hardware_context(telemetry)
        normalized = normalize_telemetry(telemetry)
        measured_data = compact_measured_data(normalized)
        chunks, retrieval_trace = self.retriever.retrieve_with_trace(
            sanitized_query,
            route=route,
            limit=4,
            hardware_context=hardware_context,
        )
        prompt = build_prompt(
            sanitized_query, route, measured_data, chunks, normalized_history,
            hardware_context=hardware_context,
        )
        raw = self.provider.generate(prompt)
        response = parse_json_response(raw)

        # Controles duros: el LLM nunca decide los sensores mostrados, sus
        # valores ni el manifiesto de fuentes recuperadas.
        response["measured_data"] = measured_data
        response["sources"] = self._source_manifest(chunks)

        validation = validate_response(response, measured_data, chunks)
        validation_attempts = [
            {
                "attempt": 1,
                "valid": validation.valid,
                "errors": list(validation.errors),
                "warnings": list(validation.warnings),
            }
        ]

        # Un LLM real puede variar ligeramente su redacción aunque el contrato
        # sea correcto. Si la salida falla la validación, hacemos UNA
        # sola corrección controlada usando los errores deterministas del
        # validator. Nunca se alteran measured_data ni sources desde el LLM.
        if self.provider.is_real_llm and not validation.valid:
            repair_feedback = {
                "validation_errors": list(validation.errors),
                "required_measured_data": measured_data,
                "rules": [
                    "Devuelve el objeto JSON completo nuevamente.",
                    "No modifiques datos medidos.",
                    "Si una métrica es N/A, no le asignes un valor ni un estado cualitativo.",
                    "Cada elemento de retrieved_information y recommendations debe incluir [S#].",
                    "Usa solo los identificadores de fuente existentes.",
                ],
            }
            repair_prompt = (
                prompt
                + "\n\n<VALIDATION_FEEDBACK>\n"
                + json.dumps(repair_feedback, ensure_ascii=False, indent=2)
                + "\n</VALIDATION_FEEDBACK>"
            )
            raw = self.provider.generate(repair_prompt)
            response = parse_json_response(raw)
            response["measured_data"] = measured_data
            response["sources"] = self._source_manifest(chunks)
            validation = validate_response(response, measured_data, chunks)
            validation_attempts.append(
                {
                    "attempt": 2,
                    "valid": validation.valid,
                    "errors": list(validation.errors),
                    "warnings": list(validation.warnings),
                }
            )

        return {
            "schema_version": "1.2",
            "prompt_contract_version": PROMPT_CONTRACT_VERSION,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "query": sanitized_query,
            "route": route,
            "conversation_context": normalized_history,
            "telemetry_input": telemetry,
            "hardware_context": hardware_context,
            "measured_data": measured_data,
            "retrieved_sources": self._source_manifest(chunks),
            "retrieval_trace": retrieval_trace,
            "provider": {
                "name": self.provider.provider_name,
                "model": self.provider.model_name,
                "real_llm": self.provider.is_real_llm,
            },
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "generation_attempts": len(validation_attempts),
            "validation_attempts": validation_attempts,
            "response": response,
            "validation": validation.to_dict(),
        }

    def save_evidence(self, result: dict[str, Any], path: str | Path) -> Path:
        if not result.get("provider", {}).get("real_llm"):
            raise ValueError("demo_llm_real.json solo puede generarse con un proveedor LLM real.")
        if not result.get("validation", {}).get("valid"):
            raise ValueError("No se guarda evidencia final si la salida del LLM no supera la validación.")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

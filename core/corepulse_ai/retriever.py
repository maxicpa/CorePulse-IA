from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .models import KnowledgeChunk
from .sanitization import sanitize_context


TOKEN_RE = re.compile(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9_]+")


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text) if len(t) >= 3}


class CorePulseRetriever:
    """Retriever ligero, determinista y auditable para el prototipo académico.

    La colección se compone de conocimiento interno de CorePulse y fuentes
    técnicas externas previamente curadas. No existe navegación web autónoma en
    tiempo de inferencia y el LLM no decide qué documentos recuperar.
    """

    def __init__(self, knowledge_dir: str | Path):
        self.knowledge_dir = Path(knowledge_dir)
        self._chunks = self._load_all()

    def _load_file(self, path: Path, source_type: str) -> list[KnowledgeChunk]:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        chunks: list[KnowledgeChunk] = []
        for item in data:
            chunks.append(
                KnowledgeChunk(
                    chunk_id=str(item["id"]),
                    topic=str(item.get("topic", "general")),
                    source_type=source_type,  # type: ignore[arg-type]
                    title=str(item["title"]),
                    content=sanitize_context(str(item["content"])),
                    source=str(item["source"]),
                    tags=tuple(str(tag) for tag in item.get("tags", [])),
                )
            )
        return chunks

    def _load_all(self) -> list[KnowledgeChunk]:
        internal = self._load_file(self.knowledge_dir / "internal_corepulse.json", "internal")
        external = self._load_file(self.knowledge_dir / "external_controlled.json", "external")
        return internal + external

    @property
    def chunks(self) -> tuple[KnowledgeChunk, ...]:
        return tuple(self._chunks)

    @staticmethod
    def _vendor_tag(chunk: KnowledgeChunk) -> str | None:
        tags = {str(tag).casefold() for tag in chunk.tags}
        text = f"{chunk.title} {' '.join(chunk.tags)}".casefold()
        if "amd" in tags or "ryzen" in tags or " amd " in f" {text} ":
            return "amd"
        if "intel" in tags or " intel " in f" {text} ":
            return "intel"
        return None

    def _rank(
        self, query: str, route: str, hardware_context: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        query_tokens = _tokens(query)
        hardware_context = hardware_context or {}
        cpu_vendor = str(hardware_context.get("cpu_vendor") or "N/A").strip().casefold()
        cpu_model_tokens = _tokens(str(hardware_context.get("cpu_model") or ""))
        ranked: list[dict[str, Any]] = []
        for chunk in self._chunks:
            # Coherencia contextual: una ruta específica solo compite con
            # conocimiento de esa ruta y con políticas generales. Esto evita
            # que coincidencias léxicas como "temperatura" introduzcan fuentes
            # de GPU o almacenamiento en una consulta de CPU.
            if route != "general" and chunk.topic not in {route, "general"}:
                continue

            vendor_tag = self._vendor_tag(chunk) if chunk.topic == "cpu" else None
            vendor_bonus = 0.0
            vendor_policy = "not_applicable"
            model_bonus = 0.0
            # Fuentes externas específicas de fabricante sólo compiten si son
            # compatibles con la identidad real del CPU. Con fabricante N/A no
            # se excluyen, pero tampoco reciben bonificación.
            if route == "cpu" and vendor_tag:
                if cpu_vendor in {"amd", "intel"}:
                    if vendor_tag != cpu_vendor:
                        if chunk.source_type == "external":
                            continue
                        vendor_policy = "mismatch_internal_kept"
                    else:
                        vendor_bonus = 3.0
                        vendor_policy = "vendor_match"
                else:
                    vendor_policy = "vendor_unknown"

            haystack = " ".join((chunk.topic, chunk.title, chunk.content, " ".join(chunk.tags)))
            chunk_tokens = _tokens(haystack)
            token_overlap = len(query_tokens & chunk_tokens)
            route_bonus = 4.0 if chunk.topic == route else 0.0
            general_bonus = 1.0 if chunk.topic == "general" else 0.0
            source_type_bonus = 0.15 if chunk.source_type == "internal" else 0.10
            if route == "cpu" and cpu_model_tokens:
                chunk_model_tokens = _tokens(" ".join((chunk.title, chunk.content, " ".join(chunk.tags))))
                model_overlap = len(cpu_model_tokens & chunk_model_tokens)
                model_bonus = min(2.0, float(model_overlap) * 0.5)
            score = float(token_overlap) + route_bonus + general_bonus + source_type_bonus + vendor_bonus + model_bonus
            if score > 0:
                ranked.append(
                    {
                        "chunk": chunk,
                        "score": round(score, 3),
                        "token_overlap": token_overlap,
                        "route_bonus": route_bonus,
                        "general_bonus": general_bonus,
                        "source_type_bonus": source_type_bonus,
                        "vendor_bonus": vendor_bonus,
                        "model_bonus": model_bonus,
                        "vendor_policy": vendor_policy,
                        "selection_reason": "ranked_vendor_match" if vendor_bonus else "ranked",
                    }
                )
        ranked.sort(key=lambda item: (-float(item["score"]), item["chunk"].chunk_id))
        return ranked

    def retrieve_with_trace(
        self,
        query: str,
        route: str,
        limit: int = 4,
        hardware_context: dict[str, str] | None = None,
    ) -> tuple[list[KnowledgeChunk], list[dict[str, Any]]]:
        """Recupera hasta ``limit`` fuentes y expone el porqué de la selección."""
        limit = max(1, min(int(limit), 4))
        ranked = self._rank(query, route, hardware_context=hardware_context)
        selected = [dict(item) for item in ranked[:limit]]

        # Balance académico: cuando existe evidencia suficiente, conservamos al
        # menos una fuente interna y una externa sin superar cuatro fragmentos.
        if selected:
            selected_types = {item["chunk"].source_type for item in selected}
            for desired in ("internal", "external"):
                if desired in selected_types:
                    continue
                candidate = next(
                    (
                        dict(item)
                        for item in ranked
                        if item["chunk"].source_type == desired
                        and all(item["chunk"] != current["chunk"] for current in selected)
                    ),
                    None,
                )
                if candidate is None:
                    continue
                candidate["selection_reason"] = "source_balance"
                if len(selected) >= limit:
                    selected[-1] = candidate
                else:
                    selected.append(candidate)
                selected_types.add(desired)

        chunks = [item["chunk"] for item in selected[:limit]]
        trace: list[dict[str, Any]] = []
        for idx, item in enumerate(selected[:limit], start=1):
            chunk: KnowledgeChunk = item["chunk"]
            trace.append(
                {
                    "source_id": f"S{idx}",
                    "chunk_id": chunk.chunk_id,
                    "topic": chunk.topic,
                    "source_type": chunk.source_type,
                    "score": item["score"],
                    "score_components": {
                        "token_overlap": item["token_overlap"],
                        "route_bonus": item["route_bonus"],
                        "general_bonus": item["general_bonus"],
                        "source_type_bonus": item["source_type_bonus"],
                        "vendor_bonus": item.get("vendor_bonus", 0.0),
                        "model_bonus": item.get("model_bonus", 0.0),
                    },
                    "vendor_policy": item.get("vendor_policy", "not_applicable"),
                    "selection_reason": item["selection_reason"],
                }
            )
        return chunks, trace

    def retrieve(
        self, query: str, route: str, limit: int = 4,
        hardware_context: dict[str, str] | None = None,
    ) -> list[KnowledgeChunk]:
        chunks, _ = self.retrieve_with_trace(
            query, route, limit=limit, hardware_context=hardware_context
        )
        return chunks

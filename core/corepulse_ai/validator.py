from __future__ import annotations

import json
import re
from typing import Any

from .context import REAL_OR_NA
from .models import KnowledgeChunk, ValidationReport


REQUIRED_KEYS = {
    "measured_data",
    "interpretation",
    "retrieved_information",
    "recommendations",
    "sources",
}
CITATION_RE = re.compile(r"\[S(\d+)\]")
UNCERTAINTY_RE = re.compile(
    r"(?i)("
    r"n/?a|"
    r"no\s+(?:se\s+)?puede\s+(?:determinar|evaluar|afirmar|concluir|confirmar|saber|establecer)|"
    r"no\s+es\s+posible\s+(?:determinar|evaluar|afirmar|concluir|confirmar|saber|establecer)|"
    r"no\s+se\s+sabe|"
    r"no\s+disponible|"
    r"sin\s+(?:lectura|dato|datos|medici[oó]n|mediciones)|"
    r"no\s+hay\s+(?:lectura|dato|datos|medici[oó]n|mediciones)|"
    r"dato\s+ausente|"
    r"desconocid[oa]|indeterminad[oa]"
    r")"
)


def parse_json_response(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("La respuesta del LLM debe ser un objeto JSON.")
    return data


def _citations(text: str) -> set[str]:
    return {f"S{match}" for match in CITATION_RE.findall(text or "")}


def _validate_cited_list(
    value: Any,
    *,
    field_name: str,
    allowed_ids: set[str],
    require_citation: bool,
    errors: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append(f"{field_name} debe ser una lista.")
        return
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str):
            errors.append(f"{field_name}[{index}] debe ser texto.")
            continue
        used = _citations(item)
        invalid = used - allowed_ids
        if invalid:
            errors.append(
                f"{field_name}[{index}] cita fuentes inexistentes: " + ", ".join(sorted(invalid))
            )
        if require_citation and allowed_ids and not used:
            errors.append(f"{field_name}[{index}] carece de referencia [S#].")


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?;])\s+|\n+", text or "") if part.strip()]


def _na_interpretation_violations(interpretation: str, measured_data: dict[str, str]) -> list[str]:
    """Detecta algunas alucinaciones verificables sobre métricas N/A.

    No intenta resolver semántica general. Aplica guardas deterministas a las
    afirmaciones más riesgosas: valores concretos o estados cualitativos de una
    temperatura/uso que el contexto marcado como verificado declara N/A.
    """
    violations: list[str] = []
    specs = {
        "cpu_temperature": {
            "subject": re.compile(r"(?i)\b(cpu|procesador)\b"),
            "concept": re.compile(r"(?i)\btemperatura\b|°\s*c|celsius"),
            "number": re.compile(r"(?i)\b\d{1,3}(?:[.,]\d+)?\s*(?:°\s*c|celsius)\b"),
            "state": re.compile(r"(?i)\b(alta|elevada|cr[ií]tica|normal|baja)\b"),
        },
        "gpu_temperature": {
            "subject": re.compile(r"(?i)\b(gpu|gr[aá]fica|tarjeta\s+gr[aá]fica)\b"),
            "concept": re.compile(r"(?i)\btemperatura\b|°\s*c|celsius"),
            "number": re.compile(r"(?i)\b\d{1,3}(?:[.,]\d+)?\s*(?:°\s*c|celsius)\b"),
            "state": re.compile(r"(?i)\b(alta|elevada|cr[ií]tica|normal|baja)\b"),
        },
        "cpu_usage": {
            "subject": re.compile(r"(?i)\b(cpu|procesador)\b"),
            "concept": re.compile(r"(?i)\b(uso|carga|utilizaci[oó]n)\b|%"),
            "number": re.compile(r"\b\d{1,3}(?:[.,]\d+)?\s*%"),
            "state": re.compile(r"(?i)\b(alto|alta|elevad[oa]|normal|bajo|baja)\b"),
        },
        "gpu_usage": {
            "subject": re.compile(r"(?i)\b(gpu|gr[aá]fica|tarjeta\s+gr[aá]fica)\b"),
            "concept": re.compile(r"(?i)\b(uso|carga|utilizaci[oó]n)\b|%"),
            "number": re.compile(r"\b\d{1,3}(?:[.,]\d+)?\s*%"),
            "state": re.compile(r"(?i)\b(alto|alta|elevad[oa]|normal|bajo|baja)\b"),
        },
        "ram_usage": {
            "subject": re.compile(r"(?i)\b(ram|memoria)\b"),
            "concept": re.compile(r"(?i)\b(uso|carga|utilizaci[oó]n)\b|%"),
            "number": re.compile(r"\b\d{1,3}(?:[.,]\d+)?\s*%"),
            "state": re.compile(r"(?i)\b(alto|alta|elevad[oa]|normal|bajo|baja)\b"),
        },
        "network_latency_ms": {
            "subject": re.compile(r"(?i)\b(red|latencia|ping)\b"),
            "concept": re.compile(r"(?i)\b(latencia|ping)\b|\bms\b"),
            "number": re.compile(r"(?i)\b\d+(?:[.,]\d+)?\s*ms\b"),
            "state": re.compile(r"(?i)\b(alta|elevada|normal|baja)\b"),
        },
    }

    for field, spec in specs.items():
        if measured_data.get(field) != REAL_OR_NA:
            continue
        for sentence in _sentences(interpretation):
            if not spec["subject"].search(sentence) or not spec["concept"].search(sentence):
                continue
            if spec["number"].search(sentence):
                violations.append(
                    f"La interpretación inventa un valor concreto para {field}, que está N/A."
                )
                break
            if spec["state"].search(sentence) and not UNCERTAINTY_RE.search(sentence):
                violations.append(
                    f"La interpretación asigna un estado a {field} pese a estar N/A."
                )
                break
    return violations


def validate_response(
    response: dict[str, Any],
    measured_data: dict[str, str],
    chunks: list[KnowledgeChunk],
) -> ValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    missing = REQUIRED_KEYS - set(response)
    if missing:
        errors.append("Faltan claves obligatorias: " + ", ".join(sorted(missing)))

    # REAL_OR_NA: los datos medidos de salida deben ser exactamente los de la
    # capa de telemetría, nunca los propuestos por el LLM.
    if response.get("measured_data") != measured_data:
        errors.append("Los datos medidos de salida no coinciden con la telemetría verificada.")

    interpretation = response.get("interpretation", "")
    if not isinstance(interpretation, str):
        errors.append("interpretation debe ser texto.")
        interpretation = ""

    if len(chunks) > 4:
        errors.append("El pipeline excedió el máximo de cuatro fuentes RAG.")

    expected_ids = [f"S{i}" for i in range(1, len(chunks) + 1)]
    allowed_ids = set(expected_ids)

    sources = response.get("sources", [])
    if not isinstance(sources, list):
        errors.append("sources debe ser una lista.")
    else:
        actual_ids = [str(item.get("id")) for item in sources if isinstance(item, dict)]
        if actual_ids != expected_ids:
            errors.append("El manifiesto de fuentes no coincide con las fuentes RAG seleccionadas.")

    _validate_cited_list(
        response.get("retrieved_information", []),
        field_name="retrieved_information",
        allowed_ids=allowed_ids,
        require_citation=True,
        errors=errors,
    )
    _validate_cited_list(
        response.get("recommendations", []),
        field_name="recommendations",
        allowed_ids=allowed_ids,
        require_citation=True,
        errors=errors,
    )

    combined_text = json.dumps(
        {
            "interpretation": interpretation,
            "retrieved_information": response.get("retrieved_information", []),
            "recommendations": response.get("recommendations", []),
        },
        ensure_ascii=False,
    )
    used = _citations(combined_text)
    invalid = used - allowed_ids
    if invalid:
        errors.append("Se citaron fuentes inexistentes: " + ", ".join(sorted(invalid)))
    if chunks and not used:
        warnings.append("La respuesta no contiene referencias [S#] en el contenido técnico.")

    errors.extend(_na_interpretation_violations(interpretation, measured_data))

    return ValidationReport(valid=not errors, errors=errors, warnings=warnings)

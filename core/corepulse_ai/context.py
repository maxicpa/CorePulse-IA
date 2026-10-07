from __future__ import annotations

from typing import Any


REAL_OR_NA = "N/A"

# Campos mínimos del prototipo. Se pueden ampliar sin cambiar la regla REAL_OR_NA.
TELEMETRY_FIELDS: dict[str, str | None] = {
    "cpu_usage": "%",
    "cpu_temperature": "°C",
    "gpu_usage": "%",
    "gpu_temperature": "°C",
    "ram_usage": "%",
    "storage_usage": "%",
    "network_latency_ms": "ms",
    "system_status": None,
}


def _is_missing(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip().upper() in {"", "N/A", "NA", "NULL", "NONE"})


def normalize_telemetry(raw: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Normaliza telemetría sin inferir datos ausentes.

    Todo campo inexistente o inválido se expresa como N/A. Nunca se estima un
    sensor, temperatura, frecuencia ni estado que no venga en la entrada.
    """
    normalized: dict[str, dict[str, Any]] = {}
    for field, unit in TELEMETRY_FIELDS.items():
        value = raw.get(field)
        if _is_missing(value):
            normalized[field] = {
                "value": REAL_OR_NA,
                "unit": unit,
                "verified": False,
            }
            continue

        normalized[field] = {
            "value": value,
            "unit": unit,
            "verified": True,
        }
    return normalized


def compact_measured_data(normalized: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Devuelve una vista legible para el prompt y la respuesta."""
    result: dict[str, str] = {}
    for key, item in normalized.items():
        value = item["value"]
        unit = item.get("unit")
        if value == REAL_OR_NA:
            result[key] = REAL_OR_NA
        elif unit:
            result[key] = f"{value} {unit}"
        else:
            result[key] = str(value)
    return result



def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def infer_cpu_vendor(*values: Any) -> str:
    """Normaliza el fabricante CPU sin inventarlo.

    Sólo devuelve AMD/Intel cuando el fabricante o modelo recibido lo permite
    de forma explícita; de lo contrario conserva N/A.
    """
    text = " ".join(str(v) for v in values if v is not None).casefold()
    if any(token in text for token in ("advanced micro devices", "amd", "ryzen")):
        return "AMD"
    if any(token in text for token in ("genuineintel", "intel")):
        return "Intel"
    return REAL_OR_NA


def extract_hardware_context(raw: dict[str, Any]) -> dict[str, str]:
    """Extrae identidad de hardware verificable para orientar el RAG.

    Esta identidad no sustituye a VERIFIED_TELEMETRY ni crea sensores. Sirve
    únicamente para evitar, por ejemplo, recomendar documentación Intel a una
    CPU AMD cuando CorePulse conoce el modelo/fabricante real.
    """
    raw = raw if isinstance(raw, dict) else {}
    explicit_vendor = _clean_text(raw.get("cpu_vendor") or raw.get("cpu_manufacturer"))
    model = _clean_text(raw.get("cpu_model") or raw.get("cpu_name"))
    vendor = infer_cpu_vendor(explicit_vendor, model)
    return {
        "cpu_vendor": vendor,
        "cpu_model": model or REAL_OR_NA,
    }

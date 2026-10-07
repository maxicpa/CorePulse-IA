from __future__ import annotations

import math
from typing import Any

from .context import infer_cpu_vendor


def _finite(value: Any) -> float | int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if number.is_integer():
        return int(number)
    return round(number, 4)


def _max_real(values: list[Any]) -> float | int | None:
    normalized = [v for v in (_finite(x) for x in values) if v is not None]
    return max(normalized) if normalized else None


def adapt_corepulse_snapshot(
    snapshot: dict[str, Any],
    *,
    disks: list[dict[str, Any]] | None = None,
    network: dict[str, Any] | None = None,
    system: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Adapta telemetría REAL de CorePulse al contrato académico.

    No calcula, interpola ni estima métricas ausentes. Cualquier dato no
    disponible queda como ``None`` y luego ``normalize_telemetry`` lo convierte
    en ``N/A``. Esto mantiene a CorePulse como fuente de verdad.
    """
    snapshot = snapshot if isinstance(snapshot, dict) else {}
    disks = disks if isinstance(disks, list) else []
    network = network if isinstance(network, dict) else {}
    system = system if isinstance(system, dict) else {}

    storage_usage = _max_real([
        item.get("used_percent")
        for item in disks
        if isinstance(item, dict)
    ])

    network_latency = _finite(
        network.get("latency_ms")
        if network.get("latency_ms") is not None
        else network.get("latency_avg_ms")
    )

    system_status = system.get("status") or system.get("state")
    if system_status is not None:
        system_status = str(system_status).strip() or None

    cpu_model = str(snapshot.get("cpu_name") or "").strip() or None
    cpu_vendor = infer_cpu_vendor(snapshot.get("cpu_vendor"), snapshot.get("cpu_manufacturer"), cpu_model)

    return {
        "cpu_vendor": cpu_vendor,
        "cpu_model": cpu_model,
        "cpu_usage": _finite(snapshot.get("cpu_usage")),
        "cpu_temperature": _finite(snapshot.get("cpu_temp")),
        "gpu_usage": _finite(snapshot.get("gpu_usage")),
        "gpu_temperature": _finite(snapshot.get("gpu_temp")),
        "ram_usage": _finite(snapshot.get("ram_usage")),
        "storage_usage": storage_usage,
        "network_latency_ms": network_latency,
        "system_status": system_status,
        "_provenance": {
            "source": "core.telemetry.get_system_telemetry",
            "policy": snapshot.get("_policy") or snapshot.get("policy") or "REAL_OR_NA",
            "synthetic_values_allowed": False,
        },
    }


def collect_live_corepulse_telemetry() -> dict[str, Any]:
    """Obtiene una muestra real de CorePulse y la adapta al pipeline académico.

    La importación es diferida para que el módulo académico pueda probarse sin
    inicializar sensores Windows. Red y estado global no se fuerzan: si no hay
    una medición explícita en esta ruta, permanecen N/A.
    """
    try:
        from core.telemetry import get_all_disks_data, get_system_telemetry
    except ImportError as exc:
        raise RuntimeError(
            "El modo --live requiere ejecutar este módulo dentro del proyecto CorePulse completo. "
            "En el repositorio académico usa los JSON de examples/corepulse_ai/."
        ) from exc

    snapshot = get_system_telemetry(wait_for_first=True)
    try:
        disks = get_all_disks_data()
    except Exception:
        disks = []
    return adapt_corepulse_snapshot(snapshot, disks=disks)

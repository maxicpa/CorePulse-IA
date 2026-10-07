from __future__ import annotations

import unicodedata


ROUTES = ("cpu", "gpu", "memory", "storage", "network", "system", "general")


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def route_query(query: str) -> str:
    q = _normalize(query)
    rules: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("cpu", ("cpu", "procesador", "temperatura procesador", "uso procesador")),
        ("gpu", ("gpu", "grafica", "tarjeta grafica", "vram")),
        ("memory", ("ram", "memoria", "memory")),
        ("storage", ("ssd", "hdd", "disco", "almacenamiento", "storage")),
        ("network", ("red", "network", "latencia", "ping", "internet")),
        ("system", ("sistema", "windows", "salud del sistema", "system")),
    )
    for route, keywords in rules:
        if any(keyword in q for keyword in keywords):
            return route
    return "general"

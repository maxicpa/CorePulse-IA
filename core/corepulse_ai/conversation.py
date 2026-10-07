from __future__ import annotations

from typing import Any

from .sanitization import sanitize_context


MAX_MESSAGES = 6
MAX_CHARS_PER_MESSAGE = 1200


def normalize_history(history: Any) -> list[dict[str, str]]:
    """Control de contexto conversacional acotado y sanitizado."""
    clean: list[dict[str, str]] = []
    for item in list(history or [])[-MAX_MESSAGES:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role not in {"user", "assistant"}:
            continue
        content = sanitize_context(str(item.get("content") or ""), MAX_CHARS_PER_MESSAGE)
        if content:
            clean.append({"role": role, "content": content})
    return clean

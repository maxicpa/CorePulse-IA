from __future__ import annotations

import re


CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
PROMPT_INJECTION_RE = re.compile(
    r"(?i)(ignore|ignora|omite|olvida)\s+(?:all\s+|todas?\s+|las\s+)?(?:"
    r"(?:previous|anteriores?|previas?)\s+(?:instructions?|instrucciones?)|"
    r"(?:instructions?|instrucciones?)\s+(?:previous|anteriores?|previas?)"
    r")"
)


def sanitize_query(text: str, max_length: int = 1200) -> str:
    clean = CONTROL_CHARS_RE.sub(" ", text or "")
    clean = PROMPT_INJECTION_RE.sub("[INSTRUCCIÓN NO CONFIABLE BLOQUEADA]", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:max_length]


def sanitize_context(text: str, max_length: int = 5000) -> str:
    clean = CONTROL_CHARS_RE.sub(" ", text or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:max_length]

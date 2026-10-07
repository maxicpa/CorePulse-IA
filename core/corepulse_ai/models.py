from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


SourceType = Literal["internal", "external"]


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    topic: str
    source_type: SourceType
    title: str
    content: str
    source: str
    tags: tuple[str, ...] = ()


@dataclass
class ValidationReport:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

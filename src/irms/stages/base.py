"""环节统一接口。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from irms.context import RunContext


@dataclass
class StageResult:
    status: str  # success | failed | skipped
    artifact_path: str | None = None
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class Stage(Protocol):
    name: str
    artifact_name: str

    def run(self, ctx: RunContext) -> StageResult: ...

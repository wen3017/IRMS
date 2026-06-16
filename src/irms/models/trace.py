"""沙箱执行轨迹 schema（sandbox 环节产物）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    tick: int
    from_state: str
    to_state: str
    triggered_rule: str | None = None
    note: str = ""


class ExecutionTrace(BaseModel):
    steps: list[TraceStep] = Field(default_factory=list)
    reached_final: bool = False
    final_state: str | None = None
    unreached_states: list[str] = Field(default_factory=list)

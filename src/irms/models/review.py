"""审查报告 schema（review 环节产物）。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "warning", "error"]


class CheckResult(BaseModel):
    name: str = Field(description="检查项名，如 reachability / dead_states")
    passed: bool
    severity: Severity = "info"
    detail: str = ""


class ReviewReport(BaseModel):
    checks: list[CheckResult] = Field(default_factory=list)
    summary: str = Field(default="", description="自然语言审查总结（agent 生成）")
    passed: bool = True

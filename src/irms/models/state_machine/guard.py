"""状态机 Guard 模型。

本阶段仅保存 guard 表达式及变量，不解析、不执行。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Guard(BaseModel):
    expression: str = Field(description="守卫条件表达式，表达式语言待确认，本阶段不执行。")
    variables: dict[str, Any] = Field(default_factory=dict, description="表达式涉及变量，仅结构化保存。")
    description: str | None = Field(default=None, description="条件说明，待确认。")

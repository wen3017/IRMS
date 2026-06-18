"""状态机动作模型。

本阶段仅描述动作，不实现真实动作执行。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Action(BaseModel):
    action_type: str = Field(description="动作类型或动作编码，正式编码待确认。")
    parameters: dict[str, Any] = Field(default_factory=dict, description="动作参数，仅结构化保存，不执行。")
    description: str | None = Field(default=None, description="动作说明，待确认。")

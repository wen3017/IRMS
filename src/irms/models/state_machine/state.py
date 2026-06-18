"""任务状态模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, PositiveInt, model_validator

from irms.models.state_machine.action import Action
from irms.models.state_machine.enums import StateType, TERMINAL_STATE_TYPES


class State(BaseModel):
    id: str = Field(description="状态唯一标识。")
    name: str = Field(description="状态名称。")
    state_type: StateType = Field(description="状态类型。")
    description: str | None = Field(default=None, description="状态业务说明，待确认。")
    terminal: bool = Field(default=False, description="是否为终止状态。")
    timeout: PositiveInt | None = Field(default=None, description="进入该状态后允许停留的最大时长，单位：秒；未明确则为空。")
    entry_actions: list[Action] = Field(default_factory=list, description="进入状态时的动作描述，不执行。")
    exit_actions: list[Action] = Field(default_factory=list, description="离开状态时的动作描述，不执行。")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据，未明确内容写入此处前应标记待确认。")

    @model_validator(mode="after")
    def _check_terminal_flag(self) -> "State":
        if self.state_type in TERMINAL_STATE_TYPES and not self.terminal:
            raise ValueError("COMPLETED/FAILED/CANCELLED states must set terminal=true")
        if self.terminal and self.state_type not in TERMINAL_STATE_TYPES:
            raise ValueError("terminal=true is only allowed for COMPLETED/FAILED/CANCELLED states")
        return self

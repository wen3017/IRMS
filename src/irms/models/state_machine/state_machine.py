"""通用任务状态机模型。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from irms.models.state_machine.state import State
from irms.models.state_machine.transition import Transition
from irms.models.state_machine.validators import validate_state_machine_graph


class StateMachine(BaseModel):
    id: str = Field(description="状态机唯一标识。")
    name: str = Field(description="状态机名称。")
    description: str | None = Field(default=None, description="状态机说明，待确认。")
    states: list[State] = Field(description="状态列表。")
    transitions: list[Transition] = Field(description="流转列表。")
    initial_state_id: str = Field(description="初始状态 ID，必须引用唯一 INITIAL 状态。")
    version: str | None = Field(default=None, description="状态机版本，待确认。")
    metadata: dict[str, Any] = Field(default_factory=dict, description="扩展元数据，未明确内容应标记待确认。")
    task_type_id: str | None = Field(default=None, description="关联上一阶段 TaskType.task_type_id，待确认。")
    task_flow_id: str | None = Field(default=None, description="关联上一阶段 TaskFlow.flow_id，待确认。")

    @model_validator(mode="after")
    def _validate_graph(self) -> "StateMachine":
        validate_state_machine_graph(self.states, self.transitions, self.initial_state_id)
        return self


def state_machine_json_schema() -> dict[str, Any]:
    """导出 StateMachine JSON Schema。"""

    return StateMachine.model_json_schema()

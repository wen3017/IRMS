"""任务状态流转模型。"""

from __future__ import annotations

from pydantic import BaseModel, Field, NonNegativeInt, PositiveInt

from irms.models.state_machine.action import Action
from irms.models.state_machine.enums import TransitionType, TriggerType
from irms.models.state_machine.guard import Guard


class Transition(BaseModel):
    id: str = Field(description="流转唯一标识。")
    from_state: str = Field(description="来源状态 ID。")
    to_state: str = Field(description="目标状态 ID。")
    trigger: TriggerType = Field(description="触发类型。")
    guard: Guard | None = Field(default=None, description="流转守卫条件，表达式语言待确认，本阶段不执行。")
    actions: list[Action] = Field(default_factory=list, description="流转动作描述，不执行。")
    priority: NonNegativeInt = Field(default=0, description="流转优先级，非负整数。")
    timeout: PositiveInt | None = Field(default=None, description="触发流转前的等待或判定时限，单位：秒；未明确则为空。")
    description: str | None = Field(default=None, description="流转业务说明，待确认。")
    transition_type: TransitionType = Field(default=TransitionType.NORMAL, description="流转场景类型。")
    allow_self_loop: bool = Field(default=False, description="是否显式允许自循环。")
    allow_from_terminal: bool = Field(default=False, description="是否显式允许从终止状态恢复；默认不允许。")

"""规则配置 schema（generate 环节产物）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class StateMachine(BaseModel):
    states: list[str] = Field(description="所有任务状态")
    initial: str = Field(description="初始状态，如 created")
    finals: list[str] = Field(description="终态，如 completed / cancelled")


class Transition(BaseModel):
    from_state: str = Field(alias="from")
    to_state: str = Field(alias="to")
    trigger: str = Field(description="触发事件")
    guard: str | None = Field(default=None, description="流转条件/守卫")

    model_config = {"populate_by_name": True}


class Rule(BaseModel):
    id: str
    description: str = ""
    condition: str = Field(description="规则条件")
    action: str = Field(description="规则动作")


class RuleConfig(BaseModel):
    """任务状态机 + 流转 + 各类规则配置。"""

    state_machine: StateMachine
    transitions: list[Transition] = Field(default_factory=list)
    robot_dispatch_rules: list[Rule] = Field(default_factory=list)
    workstation_rules: list[Rule] = Field(default_factory=list)
    battery_rules: list[Rule] = Field(default_factory=list)
    exception_rules: list[Rule] = Field(default_factory=list)
    cancellation_rules: list[Rule] = Field(default_factory=list)
    priority_rules: list[Rule] = Field(default_factory=list)

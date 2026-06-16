"""场景模型 schema（ingest / model 环节产物）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class RobotSpec(BaseModel):
    type: str = Field(description="机器人类型，如 货架搬运 / 料箱搬运")
    capabilities: list[str] = Field(default_factory=list, description="能力，如 lift_shelf, carry_bin")
    low_battery_threshold: float = Field(default=20.0, description="低电量阈值(%)")
    full_battery_threshold: float = Field(default=90.0, description="充满阈值(%)")


class Workstation(BaseModel):
    id: str
    type: str = Field(description="工作站类型，如 拣选站 / 补货站")
    constraints: list[str] = Field(default_factory=list, description="约束，如 max_concurrent_tasks=1")


class Location(BaseModel):
    id: str
    area: str = Field(description="所属区域")
    constraints: list[str] = Field(default_factory=list)


class FlowStep(BaseModel):
    name: str = Field(description="流程步骤名，如 取货 / 搬运 / 拣选 / 归位")
    description: str = ""


class ExceptionBranch(BaseModel):
    name: str = Field(description="异常名，如 取货失败 / 机器人离线")
    trigger: str = Field(description="触发条件")
    handling: str = Field(description="处理动作")


class BatteryPolicy(BaseModel):
    low_threshold: float = 20.0
    charge_trigger: str = "low_battery"


class CancellationPolicy(BaseModel):
    allowed_states: list[str] = Field(default_factory=list, description="允许取消的状态")
    handling: str = "release_resources"


class PriorityPolicy(BaseModel):
    levels: list[str] = Field(default_factory=lambda: ["low", "normal", "high"])
    preemption: bool = False


class ScenarioModel(BaseModel):
    """标准化场景模型，是下游所有环节的输入契约。"""

    scenario_type: str = Field(description="场景类型，如 货架到人 / 料箱到人 / 分拣")
    robots: list[RobotSpec] = Field(default_factory=list)
    workstations: list[Workstation] = Field(default_factory=list)
    task_flow: list[FlowStep] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)
    battery: BatteryPolicy = Field(default_factory=BatteryPolicy)
    exceptions: list[ExceptionBranch] = Field(default_factory=list)
    cancellation: CancellationPolicy = Field(default_factory=CancellationPolicy)
    priority: PriorityPolicy = Field(default_factory=PriorityPolicy)

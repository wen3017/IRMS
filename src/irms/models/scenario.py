"""场景模型 schema（1.2 完善场景模型）。

本模块只定义数据模型与确定性校验，不实现数据库、接口、调度算法、
状态机执行器或规则引擎。字段来自 doc/1.1业务对象.md；需求未明确但
模型需要承载的内容保持可选，并通过 description 标记待确认。
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt, field_validator, model_validator


class _StrEnum(str, Enum):
    """让 JSON Schema 输出稳定的字符串枚举。"""


class SceneType(_StrEnum):
    SHELF_TO_PERSON = "货架到人"
    CONTAINER_TO_PERSON = "料箱到人"
    SORTING = "分拣"
    REPLENISHMENT = "补货"
    RETURN = "退货"
    PICKING_STATION = "工作站拣选"
    CHARGING = "机器人充电"
    EXCEPTION_RETURN = "异常回流"


class ConfigStatus(_StrEnum):
    DRAFT = "草稿"
    ENABLED = "启用"
    DISABLED = "停用"


class CapabilityCode(_StrEnum):
    CARRY_SHELF = "搬运货架"
    CARRY_CONTAINER = "搬运料箱"
    CARRY_PALLET = "搬运托盘"
    LIFT = "顶升"
    TOW = "牵引"
    CHARGE = "充电"


class BusinessCategory(_StrEnum):
    SHELF_TO_PERSON = "货架到人"
    CONTAINER_TO_PERSON = "料箱到人"
    SORTING = "分拣"
    REPLENISHMENT = "补货"
    RETURN = "退货"
    CHARGING = "充电"
    EXCEPTION_RETURN = "异常回流"


class ObjectType(_StrEnum):
    LOCATION = "点位"
    SHELF = "货架"
    WORKSTATION = "工作站"
    CONTAINER = "料箱"
    PALLET = "托盘"
    CHARGER = "充电桩"


class ResourceType(_StrEnum):
    SHELF = "货架"
    CONTAINER = "料箱"
    PALLET = "托盘"
    CHARGER = "充电桩"


class WorkstationType(_StrEnum):
    PICKING = "拣选"
    SORTING = "分拣"
    REPLENISHMENT = "补货"
    RETURN = "退货"
    HANDOVER = "交接"


class WorkstationStatus(_StrEnum):
    IDLE = "空闲"
    BUSY = "忙碌"
    FULL = "已满"
    PAUSED = "暂停"
    FAULT = "故障"
    OFFLINE = "离线"
    DISABLED = "停用"


class LocationKind(_StrEnum):
    POINT = "点位"
    AREA = "区域"


class PointType(_StrEnum):
    NORMAL = "普通"
    PICKUP = "取货"
    DROPOFF = "放货"
    WAITING = "等待"
    WORKSTATION = "工作站"
    SHELF = "货架"
    CHARGING = "充电"


class AreaType(_StrEnum):
    NORMAL = "普通"
    WORKSTATION = "工作站"
    STORAGE = "存储"
    CHARGING = "充电"
    WAITING = "等待"
    FORBIDDEN = "禁行"


class LocationStatus(_StrEnum):
    AVAILABLE = "可用"
    OCCUPIED = "被占用"
    RESERVED = "已预订"
    DISABLED = "禁用"
    BLOCKED = "阻塞"
    OPEN = "开放"
    RESTRICTED = "限制"
    FULL = "已满"
    CLOSED = "封闭"
    STOPPED = "停用"


class ResourceStatus(_StrEnum):
    AVAILABLE = "可用"
    RESERVED = "已预订"
    CARRYING = "搬运中"
    PROCESSING = "工作站处理中"
    OCCUPIED = "占用"
    CHARGING = "充电中"
    FAULT = "故障"
    OFFLINE = "离线"
    DISABLED = "停用"


class FlowType(_StrEnum):
    NORMAL = "正常流"
    EXCEPTION = "异常流"
    CANCELLATION = "取消流"


class TaskState(_StrEnum):
    CREATED = "已创建"
    VALIDATING = "待校验"
    WAITING_DISPATCH = "待分配"
    ASSIGNED = "已分配"
    RUNNING = "执行中"
    WAITING = "等待中"
    COMPLETED = "已完成"
    CANCELLING = "取消中"
    CANCELLED = "已取消"
    EXCEPTION = "异常"
    RETRYING = "重试中"
    MANUAL = "人工处理"
    FAILED = "失败"


class ConstraintType(_StrEnum):
    STATUS = "状态约束"
    CAPABILITY = "能力约束"
    TASK_TYPE = "任务类型约束"
    LOAD = "负载约束"
    BATTERY = "电量约束"
    LOCATION = "点位约束"
    AREA = "区域约束"
    WORKSTATION = "工作站约束"
    RESOURCE = "资源约束"
    CONCURRENCY = "并发约束"
    TIME = "时间约束"
    MUTEX = "任务互斥"
    PRECEDENCE = "前置任务约束"


class BatteryBand(_StrEnum):
    NORMAL = "正常电量"
    ATTENTION = "关注电量"
    LOW = "低电量"
    EMERGENCY = "紧急电量"
    PROTECTIVE = "保护电量"


class PrioritySource(_StrEnum):
    TASK_TYPE_DEFAULT = "任务类型默认优先级"
    UPSTREAM = "上游系统显式指定优先级"
    CREATED_TIME = "创建时间或等待时长"
    DEADLINE = "任务截止时间或超时风险"
    WORKSTATION_URGENCY = "工作站缺料、拥堵或业务紧急程度"
    SYSTEM_TASK = "充电、异常恢复等系统任务类别"
    MANUAL = "人工调整"
    DEPENDENCY = "任务依赖关系"


class CancellationStage(_StrEnum):
    CREATED_OR_VALIDATING = "已创建/待校验"
    WAITING_DISPATCH = "待分配"
    ASSIGNED_NOT_STARTED = "已分配未执行"
    MOVING_TO_SOURCE = "前往起点"
    CARRYING = "已取货/搬运中"
    WORKSTATION_PROCESSING = "工作站处理中"
    COMPLETED = "已完成"
    EXCEPTION_OR_RETRYING = "异常/重试中"


class ExceptionCategory(_StrEnum):
    INPUT = "输入异常"
    ROBOT = "机器人异常"
    BATTERY = "电量异常"
    LOCATION = "点位异常"
    AREA = "区域异常"
    WORKSTATION = "工作站异常"
    RESOURCE = "资源异常"
    TASK = "任务异常"
    RULE = "规则异常"
    COMMUNICATION = "通信异常"


class HandlingAction(_StrEnum):
    REJECT = "拒绝创建"
    WAIT = "等待"
    RETRY = "重试"
    REASSIGN = "重新分配"
    SWITCH_RESOURCE = "切换资源"
    SWITCH_WORKSTATION = "切换工作站"
    TRIGGER_CHARGING = "触发充电"
    CANCEL = "取消"
    FAIL = "失败"
    MANUAL = "转人工"
    RELEASE_RESOURCES = "释放资源"


class ConfirmationStatus(_StrEnum):
    PENDING = "待确认"
    CONFIRMED = "已确认"
    REJECTED = "已拒绝"


class BasicInfo(BaseModel):
    """场景基本信息。"""

    scene_id: str | None = Field(default=None, description="场景唯一标识，待确认。")
    scene_name: str = Field(description="场景名称。")
    scene_type: SceneType = Field(description="场景类型。")
    description: str = Field(description="场景业务说明。")
    version: str | None = Field(default=None, description="场景模型或规则版本，待确认。")
    enabled: bool | None = Field(default=None, description="场景是否启用，待确认。")
    status: ConfigStatus | None = Field(default=None, description="场景配置状态，是否持久化待确认。")


class RobotType(BaseModel):
    """机器人类型配置。"""

    robot_type_id: str = Field(description="机器人类型唯一标识，格式待确认。")
    type_name: str = Field(description="机器人类型名称。")
    capability_codes: list[CapabilityCode] = Field(default_factory=list, description="可执行能力集合。")
    supported_task_type_ids: list[str] = Field(default_factory=list, description="可执行的任务类型 ID 集合。")
    supported_resource_types: list[ResourceType] | None = Field(default=None, description="可搬运或操作的资源类型，待确认。")
    max_load: NonNegativeFloat | None = Field(default=None, description="最大负载，单位待确认。")
    size: dict[str, NonNegativeFloat] | None = Field(default=None, description="长、宽、高等尺寸，字段及单位待确认。")
    speed_limit: NonNegativeFloat | None = Field(default=None, description="最大运行速度，单位待确认。")
    battery_capacity: NonNegativeFloat | None = Field(default=None, description="电池容量，单位待确认。")
    charge_compatibility: list[str] | None = Field(default=None, description="可使用的充电桩类型，待确认。")
    allowed_area_types: list[AreaType] | None = Field(default=None, description="可进入的区域类型，待确认。")
    docking_modes: list[str] | None = Field(default=None, description="支持的对接方式，待确认。")
    status: ConfigStatus | None = Field(default=None, description="启用/停用状态，待确认。")


class TaskFlowStep(BaseModel):
    """任务流程步骤。"""

    step_id: str = Field(description="步骤唯一标识，格式待确认。")
    step_name: str = Field(description="步骤名称。")
    from_state: TaskState | None = Field(default=None, description="进入前任务状态，正式状态码待确认。")
    to_state: TaskState | None = Field(default=None, description="完成后任务状态，正式状态码待确认。")
    flow_type: FlowType = Field(description="正常流、异常流或取消流。")
    entry_condition: str | None = Field(default=None, description="进入条件，具体表达式格式待确认。")
    action: str | None = Field(default=None, description="执行动作，具体动作编码待确认。")
    success_condition: str | None = Field(default=None, description="成功条件，具体表达式格式待确认。")
    failure_branch_ids: list[str] = Field(default_factory=list, description="失败后进入的异常分支 ID。")
    workstation_ids: list[str] = Field(default_factory=list, description="步骤引用的工作站 ID。")
    location_ids: list[str] = Field(default_factory=list, description="步骤引用的点位或区域 ID。")


class TaskFlow(BaseModel):
    """任务标准流程。"""

    flow_id: str = Field(description="任务流程唯一标识，格式待确认。")
    task_type_id: str = Field(description="所属任务类型 ID。")
    steps: list[TaskFlowStep] = Field(description="标准流程步骤。")

    @field_validator("steps")
    @classmethod
    def _steps_not_empty(cls, value: list[TaskFlowStep]) -> list[TaskFlowStep]:
        if not value:
            raise ValueError("task flow steps must not be empty")
        return value


class TaskType(BaseModel):
    """任务类型配置。"""

    task_type_id: str = Field(description="任务类型唯一标识，格式待确认。")
    task_type_name: str = Field(description="任务类型名称。")
    business_category: BusinessCategory = Field(description="业务类别。")
    required_capabilities: list[CapabilityCode] = Field(default_factory=list, description="执行该任务需要的机器人能力。")
    allowed_robot_type_ids: list[str] = Field(default_factory=list, description="允许执行该任务的机器人类型 ID。")
    source_object_type: ObjectType | None = Field(default=None, description="起点可接受的对象类型，待确认。")
    target_object_type: ObjectType | None = Field(default=None, description="终点可接受的对象类型，待确认。")
    resource_type: ResourceType | None = Field(default=None, description="任务操作的资源类型，待确认。")
    standard_flow_id: str = Field(description="标准任务流程 ID。")
    source_location_ids: list[str] = Field(default_factory=list, description="可用起始点位/区域 ID。")
    target_location_ids: list[str] = Field(default_factory=list, description="可用目标点位/区域 ID。")
    workstation_ids: list[str] = Field(default_factory=list, description="任务涉及的工作站 ID。")
    cancel_policy_id: str | None = Field(default=None, description="任务取消策略 ID，具体内容待确认。")
    exception_branch_ids: list[str] = Field(default_factory=list, description="异常处理分支 ID。")
    default_priority: int | None = Field(default=None, ge=0, le=100, description="默认优先级，范围和比较方式待确认。")
    timeout_seconds: NonNegativeInt | None = Field(default=None, description="默认超时时间，单位和阈值待确认。")
    status: ConfigStatus | None = Field(default=None, description="任务类型配置状态，待确认。")


class Workstation(BaseModel):
    """工作站对象。"""

    station_id: str = Field(description="工作站唯一标识，格式待确认。")
    station_name: str | None = Field(default=None, description="工作站名称，待确认。")
    station_type: WorkstationType = Field(description="工作站类型。")
    capability_codes: list[CapabilityCode] = Field(default_factory=list, description="工作站支持的业务能力。")
    point_ids: list[str] = Field(description="工作站关联的到达、等待、操作或离开点位 ID。")
    capacity: int = Field(description="最大同时处理数量，单位待确认。", ge=1)
    queue_capacity: NonNegativeInt | None = Field(default=None, description="等待队列容量，待确认。")
    supported_task_type_ids: list[str] = Field(default_factory=list, description="支持处理的任务类型 ID。")
    supported_resource_types: list[ResourceType] | None = Field(default=None, description="支持处理的资源类型，待确认。")
    operating_status: WorkstationStatus = Field(description="当前运行状态。")
    opening_hours: str | None = Field(default=None, description="可用时间范围，格式待确认。")
    processing_time_seconds: NonNegativeInt | None = Field(default=None, description="标准处理时间，待确认。")
    current_load: NonNegativeInt | None = Field(default=None, description="当前占用或排队数量，待确认。")


class Coordinate(BaseModel):
    x: float
    y: float
    z: float | None = Field(default=None, description="高度或楼层坐标，是否需要待确认。")


class Location(BaseModel):
    """点位或区域对象。"""

    location_id: str = Field(description="点位或区域唯一标识。")
    location_name: str | None = Field(default=None, description="点位或区域名称，待确认。")
    location_kind: LocationKind = Field(description="点位或区域。")
    point_type: PointType | None = Field(default=None, description="点位类型，仅 location_kind=点位 时使用。")
    area_type: AreaType | None = Field(default=None, description="区域类型，仅 location_kind=区域 时使用。")
    coordinate: Coordinate | None = Field(default=None, description="地图坐标，待确认。")
    area_id: str | None = Field(default=None, description="点位所属区域 ID，仅点位使用。")
    point_ids: list[str] = Field(default_factory=list, description="区域包含的点位 ID，仅区域使用。")
    enabled: bool | None = Field(default=None, description="是否启用，待确认。")
    occupancy_status: LocationStatus | None = Field(default=None, description="点位占用或区域开放状态，待确认。")
    max_occupancy: int | None = Field(default=None, ge=1, description="最大占用数量，待确认。")
    allowed_robot_type_ids: list[str] = Field(default_factory=list, description="可进入的机器人类型 ID。")
    allowed_task_type_ids: list[str] = Field(default_factory=list, description="可在区域内执行的任务类型 ID，待确认。")
    bound_resource_id: str | None = Field(default=None, description="固定关联资源 ID，如货架位或充电桩，待确认。")
    direction_constraint: str | None = Field(default=None, description="进入、离开或对接方向限制，待确认。")
    capacity: int | None = Field(default=None, ge=1, description="区域最大机器人或资源容量，待确认。")
    speed_limit: NonNegativeFloat | None = Field(default=None, description="区域速度限制，待确认。")
    access_policy: str | None = Field(default=None, description="进入和离开规则，具体规则待确认。")


class Resource(BaseModel):
    """货架、料箱、托盘或充电桩资源。"""

    resource_id: str = Field(description="资源唯一标识。")
    resource_type: ResourceType = Field(description="资源类型。")
    resource_subtype: str | None = Field(default=None, description="货架/料箱/托盘/充电桩类型，待确认。")
    current_location_type: ObjectType | None = Field(default=None, description="当前所在对象类型，待确认。")
    current_location_id: str = Field(description="当前所在点位、工作站或机器人等对象 ID。")
    storage_capacity: NonNegativeFloat | None = Field(default=None, description="存储容量，待确认。")
    load_weight: NonNegativeFloat | None = Field(default=None, description="当前负载重量，待确认。")
    movable: bool | None = Field(default=None, description="是否允许机器人搬运，待确认。")
    compatible_robot_type_ids: list[str] = Field(default_factory=list, description="可搬运或适配该资源的机器人类型 ID。")
    occupancy_status: ResourceStatus | None = Field(default=None, description="占用或锁定状态，待确认。")
    carried_by_robot_id: str | None = Field(default=None, description="当前搬运机器人 ID，待确认。")
    bound_task_id: str | None = Field(default=None, description="当前关联任务 ID，待确认。")
    charging_power: NonNegativeFloat | None = Field(default=None, description="充电功率，仅充电桩使用，待确认。")
    occupied_robot_id: str | None = Field(default=None, description="当前占用充电桩的机器人 ID，待确认。")
    reservation_task_id: str | None = Field(default=None, description="当前预约充电任务 ID，待确认。")
    queue_capacity: NonNegativeInt | None = Field(default=None, description="等待队列容量，待确认。")


class DispatchConstraint(BaseModel):
    """调度约束说明。"""

    constraint_id: str = Field(description="约束唯一标识，格式待确认。")
    constraint_type: ConstraintType = Field(description="约束类别。")
    description: str = Field(description="规则说明。")
    applies_to_task_type_ids: list[str] = Field(default_factory=list, description="适用任务类型 ID。")
    applies_to_robot_type_ids: list[str] = Field(default_factory=list, description="适用机器人类型 ID。")
    condition: str | None = Field(default=None, description="约束条件表达式，格式待确认。")
    enabled: bool | None = Field(default=None, description="是否启用，待确认。")


class BatteryPolicy(BaseModel):
    """电量策略框架。"""

    policy_id: str = Field(description="电量策略唯一标识，格式待确认。")
    task_accept_min_percent: float | None = Field(default=None, ge=0, le=100, description="最低接单电量阈值，具体值待确认。")
    low_battery_percent: float | None = Field(default=None, ge=0, le=100, description="低电量阈值，具体值待确认。")
    emergency_battery_percent: float | None = Field(default=None, ge=0, le=100, description="紧急电量阈值，具体值待确认。")
    protective_battery_percent: float | None = Field(default=None, ge=0, le=100, description="保护电量阈值，具体值待确认。")
    stop_charging_percent: float | None = Field(default=None, ge=0, le=100, description="停止充电阈值，具体值待确认。")
    require_enough_power_to_charge: bool | None = Field(default=None, description="是否检查完成任务并到达充电桩的预计电量，待确认。")
    low_battery_action: HandlingAction | None = Field(default=None, description="低电量处理动作，待确认。")
    battery_bands: list[BatteryBand] = Field(default_factory=list, description="业务使用的电量区间。")


class PriorityPolicy(BaseModel):
    """优先级策略框架。"""

    policy_id: str = Field(description="优先级策略唯一标识，格式待确认。")
    priority_min: int | None = Field(default=None, ge=0, le=100, description="优先级最小值，范围待确认。")
    priority_max: int | None = Field(default=None, ge=0, le=100, description="优先级最大值，范围待确认。")
    sources: list[PrioritySource] = Field(default_factory=list, description="优先级来源。")
    allow_preemption: bool | None = Field(default=None, description="是否允许抢占，待确认。")
    aging_enabled: bool | None = Field(default=None, description="是否启用等待时间提升优先级，待确认。")
    same_priority_order: str | None = Field(default=None, description="相同优先级排序规则，待确认。")

    @model_validator(mode="after")
    def _check_range(self) -> "PriorityPolicy":
        if self.priority_min is not None and self.priority_max is not None:
            if self.priority_min > self.priority_max:
                raise ValueError("priority_min must be <= priority_max")
        return self


class CancellationRule(BaseModel):
    stage: CancellationStage = Field(description="任务阶段。")
    handling_principle: str = Field(description="取消处理原则。")
    confirmation_required: bool = Field(default=True, description="是否需要业务确认。")


class CancellationPolicy(BaseModel):
    """任务取消策略框架。"""

    policy_id: str = Field(description="取消策略唯一标识，格式待确认。")
    cancellable_states: list[TaskState] = Field(default_factory=list, description="允许取消的任务状态。")
    rules: list[CancellationRule] = Field(default_factory=list, description="按任务阶段的取消处理原则。")
    require_source_reason_time: bool | None = Field(default=None, description="是否强制记录取消来源、原因和时间，待确认。")
    final_state: TaskState | None = Field(default=None, description="取消后进入的明确终态，状态码待确认。")


class ExceptionBranch(BaseModel):
    """异常分支。"""

    exception_id: str = Field(description="异常分支唯一标识，格式待确认。")
    exception_category: ExceptionCategory = Field(description="异常类别。")
    typical_exception: str = Field(description="典型异常。")
    trigger: str = Field(description="触发条件。")
    default_handling: list[HandlingAction] = Field(description="默认处理方向。")
    terminal_condition: str | None = Field(default=None, description="终止条件，具体表达式待确认。")
    max_retry_count: NonNegativeInt | None = Field(default=None, description="最大重试次数，具体值待确认。")
    manual_required: bool | None = Field(default=None, description="是否必须转人工，待确认。")


class Assumption(BaseModel):
    """建模假设。"""

    assumption_id: str = Field(description="假设唯一标识。")
    content: str = Field(description="假设内容。")
    source: str | None = Field(default=None, description="假设来源。")
    risk: str | None = Field(default=None, description="假设风险说明。")


class ManualConfirmation(BaseModel):
    """待人工确认的业务参数。"""

    confirmation_id: str = Field(description="待确认项唯一标识。")
    field_path: str = Field(description="涉及的模型字段路径。")
    question: str = Field(description="需要业务确认的问题。")
    reason: str = Field(description="为什么不能自行填写默认业务值。")
    status: ConfirmationStatus = Field(default=ConfirmationStatus.PENDING, description="确认状态。")


class ScenarioModel(BaseModel):
    """标准化场景模型，是下游状态机、规则配置、审查和沙箱的输入契约。"""

    basic_info: BasicInfo
    robot_types: list[RobotType] = Field(default_factory=list)
    task_types: list[TaskType] = Field(default_factory=list)
    workstations: list[Workstation] = Field(default_factory=list)
    locations: list[Location] = Field(default_factory=list)
    resources: list[Resource] = Field(default_factory=list)
    task_flows: list[TaskFlow] = Field(default_factory=list)
    dispatch_constraints: list[DispatchConstraint] = Field(default_factory=list)
    battery_policy: BatteryPolicy | None = Field(default=None)
    priority_policy: PriorityPolicy | None = Field(default=None)
    cancellation_policy: CancellationPolicy | None = Field(default=None)
    exception_branches: list[ExceptionBranch] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    manual_confirmations: list[ManualConfirmation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_ids_and_refs(self) -> "ScenarioModel":
        robot_type_ids = _unique_ids("robot_types", self.robot_types, "robot_type_id")
        task_type_ids = _unique_ids("task_types", self.task_types, "task_type_id")
        workstation_ids = _unique_ids("workstations", self.workstations, "station_id")
        location_ids = _unique_ids("locations", self.locations, "location_id")
        resource_ids = _unique_ids("resources", self.resources, "resource_id")
        task_flow_ids = _unique_ids("task_flows", self.task_flows, "flow_id")
        exception_ids = _unique_ids("exception_branches", self.exception_branches, "exception_id")
        _unique_ids("dispatch_constraints", self.dispatch_constraints, "constraint_id")
        _unique_ids("assumptions", self.assumptions, "assumption_id")
        _unique_ids("manual_confirmations", self.manual_confirmations, "confirmation_id")

        for robot_type in self.robot_types:
            _require_subset(
                f"robot_types.{robot_type.robot_type_id}.supported_task_type_ids",
                robot_type.supported_task_type_ids,
                task_type_ids,
            )

        for task_type in self.task_types:
            _require_subset(
                f"task_types.{task_type.task_type_id}.allowed_robot_type_ids",
                task_type.allowed_robot_type_ids,
                robot_type_ids,
            )
            _require_subset(
                f"task_types.{task_type.task_type_id}.source_location_ids",
                task_type.source_location_ids,
                location_ids,
            )
            _require_subset(
                f"task_types.{task_type.task_type_id}.target_location_ids",
                task_type.target_location_ids,
                location_ids,
            )
            _require_subset(
                f"task_types.{task_type.task_type_id}.workstation_ids",
                task_type.workstation_ids,
                workstation_ids,
            )
            _require_subset(
                f"task_types.{task_type.task_type_id}.exception_branch_ids",
                task_type.exception_branch_ids,
                exception_ids,
            )
            if task_type.standard_flow_id not in task_flow_ids:
                raise ValueError(
                    f"task_types.{task_type.task_type_id}.standard_flow_id references unknown task flow "
                    f"{task_type.standard_flow_id!r}"
                )
            if task_type.cancel_policy_id:
                if not self.cancellation_policy:
                    raise ValueError(
                        f"task_types.{task_type.task_type_id}.cancel_policy_id references unknown "
                        f"cancellation policy {task_type.cancel_policy_id!r}"
                    )
                if task_type.cancel_policy_id != self.cancellation_policy.policy_id:
                    raise ValueError(
                        f"task_types.{task_type.task_type_id}.cancel_policy_id references unknown "
                        f"cancellation policy {task_type.cancel_policy_id!r}"
                    )

        for workstation in self.workstations:
            _require_subset(f"workstations.{workstation.station_id}.point_ids", workstation.point_ids, location_ids)
            _require_subset(
                f"workstations.{workstation.station_id}.supported_task_type_ids",
                workstation.supported_task_type_ids,
                task_type_ids,
            )

        for location in self.locations:
            if location.location_kind == LocationKind.POINT and location.area_id:
                if location.area_id not in location_ids:
                    raise ValueError(
                        f"locations.{location.location_id}.area_id references unknown area {location.area_id!r}"
                    )
            _require_subset(
                f"locations.{location.location_id}.point_ids",
                location.point_ids,
                location_ids,
            )
            _require_subset(
                f"locations.{location.location_id}.allowed_robot_type_ids",
                location.allowed_robot_type_ids,
                robot_type_ids,
            )
            _require_subset(
                f"locations.{location.location_id}.allowed_task_type_ids",
                location.allowed_task_type_ids,
                task_type_ids,
            )
            if location.bound_resource_id and location.bound_resource_id not in resource_ids:
                raise ValueError(
                    f"locations.{location.location_id}.bound_resource_id references unknown resource "
                    f"{location.bound_resource_id!r}"
                )

        for resource in self.resources:
            if resource.current_location_type in {None, ObjectType.LOCATION}:
                if resource.current_location_id not in location_ids:
                    raise ValueError(
                        f"resources.{resource.resource_id}.current_location_id references unknown location "
                        f"{resource.current_location_id!r}"
                    )
            elif resource.current_location_type == ObjectType.WORKSTATION:
                if resource.current_location_id not in workstation_ids:
                    raise ValueError(
                        f"resources.{resource.resource_id}.current_location_id references unknown workstation "
                        f"{resource.current_location_id!r}"
                    )
            _require_subset(
                f"resources.{resource.resource_id}.compatible_robot_type_ids",
                resource.compatible_robot_type_ids,
                robot_type_ids,
            )

        for flow in self.task_flows:
            if flow.task_type_id not in task_type_ids:
                raise ValueError(f"task_flows.{flow.flow_id}.task_type_id references unknown task type")
            step_ids = [step.step_id for step in flow.steps]
            if len(step_ids) != len(set(step_ids)):
                raise ValueError(f"task_flows.{flow.flow_id}.steps contains duplicate step_id")
            for step in flow.steps:
                _require_subset(f"task_flows.{flow.flow_id}.steps.{step.step_id}.workstation_ids", step.workstation_ids, workstation_ids)
                _require_subset(f"task_flows.{flow.flow_id}.steps.{step.step_id}.location_ids", step.location_ids, location_ids)
                _require_subset(f"task_flows.{flow.flow_id}.steps.{step.step_id}.failure_branch_ids", step.failure_branch_ids, exception_ids)

        for constraint in self.dispatch_constraints:
            _require_subset(
                f"dispatch_constraints.{constraint.constraint_id}.applies_to_task_type_ids",
                constraint.applies_to_task_type_ids,
                task_type_ids,
            )
            _require_subset(
                f"dispatch_constraints.{constraint.constraint_id}.applies_to_robot_type_ids",
                constraint.applies_to_robot_type_ids,
                robot_type_ids,
            )

        return self

    @property
    def scenario_type(self) -> str:
        """兼容旧 pipeline 的场景类型读取。"""
        return self.basic_info.scene_type.value


def _unique_ids(collection_name: str, items: list[BaseModel], attr: str) -> set[str]:
    ids = [getattr(item, attr) for item in items]
    duplicated = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    if duplicated:
        raise ValueError(f"{collection_name} contains duplicate ids: {duplicated}")
    return set(ids)


def _require_subset(field_path: str, values: list[str], allowed: set[str]) -> None:
    missing = sorted(set(values) - allowed)
    if missing:
        raise ValueError(f"{field_path} references unknown ids: {missing}")


def scenario_json_schema() -> dict[str, Any]:
    """导出 ScenarioModel JSON Schema。"""

    return ScenarioModel.model_json_schema()

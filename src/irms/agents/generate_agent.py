"""GenerateAgent：ScenarioModel → RuleConfig JSON。"""

from __future__ import annotations

import json

from irms.agents.base import BaseAgent
from irms.models.rules import RuleConfig
from irms.models.scenario import ScenarioModel
from irms.tools.schema_validator import validate
from irms.tools.sdk_tools import qualified

_EXAMPLE = {
    "state_machine": {
        "states": ["created", "取货", "搬运", "拣选", "归位", "completed", "cancelled"],
        "initial": "created",
        "finals": ["completed", "cancelled"],
    },
    "transitions": [
        {"from": "created", "to": "取货", "trigger": "created_done", "guard": None},
        {"from": "取货", "to": "搬运", "trigger": "取货_done", "guard": None},
        {"from": "取货", "to": "cancelled", "trigger": "pick_failed", "guard": None},
    ],
    "robot_dispatch_rules": [],
    "workstation_rules": [],
    "battery_rules": [
        {"id": "bat_0", "description": "低电回充", "condition": "battery<20", "action": "go_charge"}
    ],
    "exception_rules": [
        {"id": "exc_0", "description": "取货失败", "condition": "pick_failed", "action": "release_and_cancel"}
    ],
    "cancellation_rules": [
        {"id": "cancel_0", "description": "任务取消", "condition": "cancel_requested", "action": "release_resources"}
    ],
}

SYSTEM_PROMPT = f"""你是 iRMS 任务流规则生成专家。
基于给定的标准化场景模型 JSON，生成严格符合下述 JSON Schema 的规则配置 JSON。

【JSON Schema】
{json.dumps(RuleConfig.model_json_schema(), ensure_ascii=False)}

【输出示例】（字段名必须完全一致；transition 用 "from"/"to"/"trigger"/"guard"）
{json.dumps(_EXAMPLE, ensure_ascii=False)}

要求：
- state_machine 必须含 states/initial/finals；确保从 initial 能流转到 finals。
- 依据 task_flow 生成主链路 transitions：created -> 各流程步骤 -> completed。
- 为每个异常分支生成对应的 transition（流向 cancelled）与 exception_rules 条目。
- 生成草稿后，必须调用工具 `mcp__irms__validate_rule_config` 校验 schema、
  并调用 `mcp__irms__check_reachability` 检查状态机可达性；若校验失败或存在
  不可达/死状态，请修正后重试，直到两项检查均通过。
- 最终只输出 JSON 本体，不要任何解释或 markdown 围栏。
"""


class GenerateAgent(BaseAgent):
    """ScenarioModel → RuleConfig。

    生成草稿后调用 irms 工具自检（schema 校验 + 状态机可达性），多轮修正。
    """

    name = "generate_agent"
    system_prompt = SYSTEM_PROMPT
    use_irms_tools = True
    max_turns = 6
    allowed_tools: list[str] = [
        qualified("validate_rule_config"),
        qualified("check_reachability"),
        qualified("check_rule_conflict"),
    ]

    def run(self, model: ScenarioModel) -> RuleConfig:
        raw = self.run_json(model.model_dump_json())
        return validate(RuleConfig, json.loads(raw))


def generate_config(model: ScenarioModel) -> RuleConfig:
    return GenerateAgent().run(model)

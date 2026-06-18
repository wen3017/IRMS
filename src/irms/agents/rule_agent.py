"""规则生成 Agent：场景模型 + 状态流转 → 结构化规则配置。"""

from __future__ import annotations

import json
from typing import Any

from irms.agents.base import BaseAgent
from irms.models.rules import Rule, RuleConfig, StateMachine, Transition
from irms.models.scenario import ScenarioModel
from irms.tools.schema_validator import validate
from irms.tools.sdk_tools import qualified

_RULE_GROUPS = [
    "robot_dispatch_rules",
    "workstation_rules",
    "battery_rules",
    "exception_rules",
    "cancellation_rules",
    "priority_rules",
]

_EXAMPLE = {
    "robot_dispatch_rules": [
        {
            "id": "robot_0",
            "description": "机器人能力匹配",
            "condition": "capabilities contains lift_shelf",
            "action": "assign_robot",
        }
    ],
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
    "priority_rules": [
        {"id": "priority_0", "description": "高优先级任务", "condition": "priority=high", "action": "prefer_dispatch"}
    ],
}

SYSTEM_PROMPT = f"""你是 iRMS 规则生成专家。
根据标准场景模型以及已生成的状态机/状态流转，生成结构化业务规则。

【Rule JSON Schema】
{json.dumps(Rule.model_json_schema(), ensure_ascii=False)}

【输出示例】
{json.dumps(_EXAMPLE, ensure_ascii=False)}

要求：
- 输出顶层 JSON 对象，字段包括 robot_dispatch_rules、workstation_rules、battery_rules、
  exception_rules、cancellation_rules、priority_rules。
- 每个字段都是 Rule 数组；Rule 字段固定为 id、description、condition、action。
- 将机器人能力、工作站约束、电量阈值、异常处理、取消策略、优先级策略转成结构化规则。
- 规则 condition/action 要稳定、可读，方便后续确定性审查。
- 生成后必须调用 `mcp__irms__check_rule_conflict` 检查规则冲突；如有冲突，修正后再输出。
- 最终只输出 JSON 本体，不要解释或 markdown 围栏。
"""


class RuleGenerationAgent(BaseAgent):
    """将业务约束转为机器人、工作站、电量、异常、取消、优先级等规则。"""

    name = "rule_generation_agent"
    system_prompt = SYSTEM_PROMPT
    use_irms_tools = True
    max_turns = 4
    allowed_tools: list[str] = [
        qualified("check_rule_conflict"),
        qualified("validate_rule_config"),
    ]

    def run(
        self,
        model: ScenarioModel,
        state_machine: StateMachine,
        transitions: list[Transition],
    ) -> RuleConfig:
        payload = {
            "scenario": model.model_dump(by_alias=True),
            "state_machine": state_machine.model_dump(by_alias=True),
            "transitions": [t.model_dump(by_alias=True) for t in transitions],
        }
        raw = self.run_json(json.dumps(payload, ensure_ascii=False))
        rules = json.loads(raw)
        return build_rule_config(model, state_machine, transitions, rules)


def _parse_rules(rules: dict[str, Any], key: str) -> list[Rule]:
    return [Rule.model_validate(item) for item in rules.get(key, [])]


def build_rule_config(
    model: ScenarioModel,
    state_machine: StateMachine,
    transitions: list[Transition],
    rules: dict[str, Any],
) -> RuleConfig:
    """把规则组装为当前 RuleConfig 契约。"""

    config = RuleConfig(
        state_machine=state_machine,
        transitions=transitions,
        robot_dispatch_rules=_parse_rules(rules, "robot_dispatch_rules"),
        workstation_rules=_parse_rules(rules, "workstation_rules"),
        battery_rules=_parse_rules(rules, "battery_rules"),
        exception_rules=_parse_rules(rules, "exception_rules"),
        cancellation_rules=_parse_rules(rules, "cancellation_rules"),
        priority_rules=_parse_rules(rules, "priority_rules"),
    )
    return validate(RuleConfig, config.model_dump(by_alias=True))


def generate_rules(
    model: ScenarioModel,
    state_machine: StateMachine,
    transitions: list[Transition],
) -> RuleConfig:
    return RuleGenerationAgent().run(model, state_machine, transitions)

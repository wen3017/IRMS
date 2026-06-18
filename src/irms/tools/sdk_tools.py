"""把确定性工具封装为 claude-agent-sdk 可调用的 in-process MCP tool。

工具在主进程内运行（无 IPC 开销），agent 通过工具名
`mcp__irms__<tool>` 调用。这些工具复用 irms.tools 下的纯确定性逻辑，
保证 agent 自检结果与离线审查一致。
"""

from __future__ import annotations

import json
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool

from irms.models.rules import RuleConfig
from irms.models.scenario import ScenarioModel
from irms.tools.conflict import find_conflicts
from irms.tools.reachability import (
    can_reach_any_final,
    dead_states,
    unreachable_states,
)

# MCP server 名称；agent 侧工具全名为 mcp__irms__<tool_name>
SERVER_NAME = "irms"


def _text(payload: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}


def _parse_config(raw: str) -> RuleConfig:
    return RuleConfig.model_validate(json.loads(raw))


@tool(
    "check_reachability",
    "校验规则配置的状态机：能否从初始状态到达终态，以及有哪些不可达/死状态。"
    "输入 config_json 为 RuleConfig 的 JSON 字符串。",
    {"config_json": str},
)
async def check_reachability(args: dict[str, Any]) -> dict[str, Any]:
    try:
        config = _parse_config(args["config_json"])
    except Exception as e:  # noqa: BLE001
        return {"content": [{"type": "text", "text": f"解析失败: {e}"}], "is_error": True}
    return _text({
        "can_reach_final": can_reach_any_final(config),
        "unreachable_states": unreachable_states(config),
        "dead_states": dead_states(config),
    })


@tool(
    "check_rule_conflict",
    "检测规则配置中条件相同但动作不同的潜在互斥规则对。"
    "输入 config_json 为 RuleConfig 的 JSON 字符串。",
    {"config_json": str},
)
async def check_rule_conflict(args: dict[str, Any]) -> dict[str, Any]:
    try:
        config = _parse_config(args["config_json"])
    except Exception as e:  # noqa: BLE001
        return {"content": [{"type": "text", "text": f"解析失败: {e}"}], "is_error": True}
    all_rules = (
        config.robot_dispatch_rules + config.workstation_rules + config.battery_rules
        + config.exception_rules + config.cancellation_rules + config.priority_rules
    )
    return _text({"conflicts": find_conflicts(all_rules)})


@tool(
    "validate_rule_config",
    "校验给定 JSON 是否符合 RuleConfig schema，返回是否通过及错误信息。",
    {"config_json": str},
)
async def validate_rule_config(args: dict[str, Any]) -> dict[str, Any]:
    try:
        RuleConfig.model_validate(json.loads(args["config_json"]))
        return _text({"valid": True})
    except Exception as e:  # noqa: BLE001
        return _text({"valid": False, "error": str(e)})


@tool(
    "validate_scenario_model",
    "校验给定 JSON 是否符合 ScenarioModel schema，返回是否通过及错误信息。",
    {"scenario_json": str},
)
async def validate_scenario_model(args: dict[str, Any]) -> dict[str, Any]:
    try:
        ScenarioModel.model_validate(json.loads(args["scenario_json"]))
        return _text({"valid": True})
    except Exception as e:  # noqa: BLE001
        return _text({"valid": False, "error": str(e)})


# 所有自定义工具
ALL_TOOLS = [
    check_reachability,
    check_rule_conflict,
    validate_rule_config,
    validate_scenario_model,
]


def qualified(tool_name: str) -> str:
    """返回 agent 侧使用的工具全名 mcp__irms__<tool_name>。"""
    return f"mcp__{SERVER_NAME}__{tool_name}"


def build_server():
    """构建 in-process MCP server config，供 ClaudeAgentOptions.mcp_servers 使用。"""
    return create_sdk_mcp_server(name=SERVER_NAME, version="0.1.0", tools=ALL_TOOLS)

"""IngestAgent：自然语言文档 → ScenarioModel JSON。"""

from __future__ import annotations

import json

from irms.agents.base import BaseAgent
from irms.models.scenario import ScenarioModel
from irms.tools.schema_validator import validate

# 提供一个最小完整示例，约束模型输出结构（字段名必须严格一致）。
_EXAMPLE = {
    "scenario_type": "货架到人",
    "robots": [
        {
            "type": "货架搬运机器人",
            "capabilities": ["lift_shelf"],
            "low_battery_threshold": 20.0,
            "full_battery_threshold": 90.0,
        }
    ],
    "workstations": [{"id": "WS-01", "type": "拣选站", "constraints": ["max_concurrent_tasks=1"]}],
    "task_flow": [{"name": "取货", "description": "顶起货架"}],
    "locations": [{"id": "LOC-A1", "area": "存储区", "constraints": []}],
    "battery": {"low_threshold": 20.0, "charge_trigger": "low_battery"},
    "exceptions": [{"name": "取货失败", "trigger": "pick_failed", "handling": "release_and_cancel"}],
    "cancellation": {"allowed_states": ["created"], "handling": "release_resources"},
    "priority": {"levels": ["low", "normal", "high"], "preemption": False},
}

SYSTEM_PROMPT = f"""你是 iRMS 仓储场景抽取专家。
将用户提供的自然语言仓储场景描述抽取为严格符合下述 JSON Schema 的 JSON 对象。

【JSON Schema】
{json.dumps(ScenarioModel.model_json_schema(), ensure_ascii=False)}

【输出示例】（字段名必须与此完全一致，不得自创字段）
{json.dumps(_EXAMPLE, ensure_ascii=False)}

要求：
- 顶层字段固定为：scenario_type, robots, workstations, task_flow, locations, battery, exceptions, cancellation, priority。
- robots/workstations/task_flow/locations/exceptions 必须是数组。
- 只输出 JSON 本体，不要任何解释或 markdown 围栏。
"""


class IngestAgent(BaseAgent):
    """自然语言文档 → ScenarioModel。"""

    name = "ingest_agent"
    system_prompt = SYSTEM_PROMPT
    allowed_tools: list[str] = []

    def run(self, doc_text: str) -> ScenarioModel:
        raw = self.run_json(doc_text)
        return validate(ScenarioModel, json.loads(raw))


def ingest_document(doc_text: str) -> ScenarioModel:
    return IngestAgent().run(doc_text)

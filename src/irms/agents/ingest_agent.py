"""场景解析 Agent：业务输入 → ScenarioModel JSON。"""

from __future__ import annotations

import json

from irms.agents.base import BaseAgent
from irms.models.scenario import ScenarioModel
from irms.tools.schema_validator import validate

_EXAMPLE = {
    "basic_info": {
        "scene_name": "货架到人最小场景",
        "scene_type": "货架到人",
        "description": "机器人搬运货架到拣选站。",
    },
    "robot_types": [
        {
            "robot_type_id": "RT-SHELF-AMR",
            "type_name": "货架搬运机器人",
            "capability_codes": ["搬运货架", "顶升"],
            "supported_task_type_ids": ["TT-SHELF-TO-PERSON"],
        }
    ],
    "task_types": [
        {
            "task_type_id": "TT-SHELF-TO-PERSON",
            "task_type_name": "货架到人任务",
            "business_category": "货架到人",
            "required_capabilities": ["搬运货架", "顶升"],
            "allowed_robot_type_ids": ["RT-SHELF-AMR"],
            "standard_flow_id": "FLOW-SHELF-TO-PERSON",
        }
    ],
    "workstations": [],
    "locations": [],
    "resources": [],
    "task_flows": [
        {
            "flow_id": "FLOW-SHELF-TO-PERSON",
            "task_type_id": "TT-SHELF-TO-PERSON",
            "steps": [
                {"step_id": "STEP-1", "step_name": "取货", "flow_type": "正常流"}
            ],
        }
    ],
    "manual_confirmations": [
        {
            "confirmation_id": "MC-001",
            "field_path": "battery_policy.low_battery_percent",
            "question": "低电量阈值是多少？",
            "reason": "需求文档标记为待确认，不能自行填写默认业务值。",
        }
    ],
}

SYSTEM_PROMPT = f"""你是 iRMS 仓储场景抽取专家。
将用户提供的自然语言仓储场景描述抽取为严格符合下述 JSON Schema 的 JSON 对象。

【JSON Schema】
{json.dumps(ScenarioModel.model_json_schema(), ensure_ascii=False)}

【输出示例】（字段名必须与新版 ScenarioModel 一致，不得自创字段）
{json.dumps(_EXAMPLE, ensure_ascii=False)}

要求：
- 顶层字段使用新版 ScenarioModel：basic_info, robot_types, task_types, workstations,
  locations, resources, task_flows, dispatch_constraints, battery_policy,
  priority_policy, cancellation_policy, exception_branches, assumptions,
  manual_confirmations。
- 需求未明确但模型需要承载的字段填 null 或省略；待确认业务参数写入 manual_confirmations。
- 只输出 JSON 本体，不要任何解释或 markdown 围栏。
"""


class ScenarioParsingAgent(BaseAgent):
    """读取业务输入，识别场景对象、任务步骤、业务规则和异常分支。"""

    name = "scenario_parsing_agent"
    system_prompt = SYSTEM_PROMPT
    allowed_tools: list[str] = []

    def run(self, doc_text: str) -> ScenarioModel:
        raw = self.run_json(doc_text)
        return validate(ScenarioModel, json.loads(raw))


def ingest_document(doc_text: str) -> ScenarioModel:
    return ScenarioParsingAgent().run(doc_text)

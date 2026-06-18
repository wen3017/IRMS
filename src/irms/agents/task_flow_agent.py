"""任务流生成 Agent：ScenarioModel → 状态机与状态流转。"""

from __future__ import annotations

import json

from irms.agents.base import BaseAgent
from irms.models.rules import StateMachine, Transition
from irms.models.scenario import ScenarioModel
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
        {"from": "搬运", "to": "拣选", "trigger": "搬运_done", "guard": None},
        {"from": "取货", "to": "cancelled", "trigger": "pick_failed", "guard": "exception"},
        {"from": "created", "to": "cancelled", "trigger": "cancel_requested", "guard": "cancellation"},
    ],
}

SYSTEM_PROMPT = f"""你是 iRMS 任务流生成专家。
根据标准场景模型生成任务状态机与状态流转关系。

【StateMachine JSON Schema】
{json.dumps(StateMachine.model_json_schema(), ensure_ascii=False)}

【Transition JSON Schema】
{json.dumps(Transition.model_json_schema(), ensure_ascii=False)}

【输出示例】
{json.dumps(_EXAMPLE, ensure_ascii=False)}

要求：
- 输出顶层 JSON 对象，只包含 state_machine 和 transitions。
- state_machine 必须包含 states、initial、finals。
- 建立正常流：created -> task_flow 中每个步骤 -> completed。
- 建立异常流：根据 exceptions 为相关业务状态补充流向 cancelled 的 transition。
- 建立取消流：根据 cancellation.allowed_states 为允许取消状态补充流向 cancelled 的 transition。
- 用 guard 标记流转类型：正常流 guard 可为 null；异常流使用 "exception"；取消流使用 "cancellation"。
- 最终只输出 JSON 本体，不要解释或 markdown 围栏。
"""


class TaskFlowGenerationAgent(BaseAgent):
    """根据场景模型生成任务状态机，标记正常流、异常流和取消流。"""

    name = "task_flow_generation_agent"
    system_prompt = SYSTEM_PROMPT
    use_irms_tools = True
    max_turns = 4
    allowed_tools: list[str] = [
        qualified("check_reachability"),
    ]

    def run(self, model: ScenarioModel) -> tuple[StateMachine, list[Transition]]:
        raw = self.run_json(model.model_dump_json())
        data = json.loads(raw)
        state_machine = StateMachine.model_validate(data["state_machine"])
        transitions = [Transition.model_validate(item) for item in data.get("transitions", [])]
        return state_machine, transitions


def generate_task_flow(model: ScenarioModel) -> tuple[StateMachine, list[Transition]]:
    return TaskFlowGenerationAgent().run(model)

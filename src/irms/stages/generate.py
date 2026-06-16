"""generate 环节：场景模型 → 规则配置。

优先走 GenerateAgent；agent 不可用时回退到确定性基线生成器，
以保证 `--from-json` 全确定性路径端到端可跑通。
"""

from __future__ import annotations

from irms.context import RunContext
from irms.models.rules import Rule, RuleConfig, StateMachine, Transition
from irms.models.scenario import ScenarioModel
from irms.stages.base import StageResult
from irms.tools.schema_validator import validate


def _baseline_config(scenario: ScenarioModel) -> RuleConfig:
    """从场景模型确定性地推导一个基线状态机与规则配置。"""
    # 由任务流程步骤推导状态：created -> <每个流程步骤> -> completed
    flow_states = [step.name for step in scenario.task_flow]
    states = ["created", *flow_states, "completed", "cancelled"]
    # 去重保序
    seen: set[str] = set()
    states = [s for s in states if not (s in seen or seen.add(s))]

    sm = StateMachine(states=states, initial="created", finals=["completed", "cancelled"])

    transitions: list[Transition] = []
    # 主链路：created -> flow[0] -> ... -> completed
    main_chain = ["created", *flow_states, "completed"]
    seen2: set[str] = set()
    main_chain = [s for s in main_chain if not (s in seen2 or seen2.add(s))]
    for src, dst in zip(main_chain, main_chain[1:]):
        transitions.append(
            Transition.model_validate(
                {"from": src, "to": dst, "trigger": f"{src}_done", "guard": None}
            )
        )

    # 异常分支：每个异常从其触发状态（默认主链路首个流程态）流向 cancelled
    exception_rules: list[Rule] = []
    for i, exc in enumerate(scenario.exceptions):
        transitions.append(
            Transition.model_validate(
                {"from": main_chain[min(1, len(main_chain) - 1)], "to": "cancelled",
                 "trigger": exc.trigger or exc.name, "guard": None}
            )
        )
        exception_rules.append(
            Rule(id=f"exc_{i}", description=exc.name,
                 condition=exc.trigger or exc.name, action=exc.handling or "cancel_task")
        )

    cancellation_rules = [
        Rule(id="cancel_0", description="任务取消",
             condition="cancel_requested", action=scenario.cancellation.handling)
    ]
    battery_rules = [
        Rule(id="bat_0", description="低电回充",
             condition=f"battery<{scenario.battery.low_threshold}", action="go_charge")
    ]

    return RuleConfig(
        state_machine=sm,
        transitions=transitions,
        robot_dispatch_rules=[],
        workstation_rules=[],
        battery_rules=battery_rules,
        exception_rules=exception_rules,
        cancellation_rules=cancellation_rules,
    )


class GenerateStage:
    name = "generate"
    artifact_name = "03_config.json"
    input_artifact = "02_model.json"

    def run(self, ctx: RunContext) -> StageResult:
        try:
            data = ctx.read_json(ctx.artifact(self.input_artifact))
            scenario = validate(ScenarioModel, data)
            try:
                from irms.agents.generate_agent import generate_config

                config = generate_config(scenario)
                meta = {"source": "agent"}
            except Exception:
                # agent 不可用：确定性基线生成
                config = _baseline_config(scenario)
                meta = {"source": "baseline"}
            path = ctx.write_artifact(self.artifact_name, config)
            return StageResult(status="success", artifact_path=str(path), meta=meta)
        except Exception as e:
            return StageResult(status="failed", error=str(e))

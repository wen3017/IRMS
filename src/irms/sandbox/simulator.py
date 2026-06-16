"""单任务状态机离散事件模拟器（确定性、纯内存、独立工作目录隔离）。"""

from __future__ import annotations

from irms.models.rules import RuleConfig
from irms.models.trace import ExecutionTrace, TraceStep
from irms.tools.reachability import reachable_states


class Simulator:
    """从 initial 状态出发，沿 transitions 逐 tick 推进到终态。

    雏形阶段：单任务、单机器人，确定性地选择每个状态的第一条可用出边，
    记录状态流转轨迹、被触发的规则（trigger），并报告不可达状态。
    """

    MAX_TICKS = 100

    def __init__(self, config: RuleConfig):
        self.config = config
        self._adjacency: dict[str, list] = {}
        for t in config.transitions:
            self._adjacency.setdefault(t.from_state, []).append(t)

    def run(self) -> ExecutionTrace:
        sm = self.config.state_machine
        finals = set(sm.finals)
        current = sm.initial
        visited_states = {current}
        steps: list[TraceStep] = []

        tick = 0
        while current not in finals and tick < self.MAX_TICKS:
            outgoing = self._adjacency.get(current, [])
            if not outgoing:
                # 死状态：无法继续推进
                break
            # 确定性：取第一条出边（后续可按 guard/优先级扩展）
            t = outgoing[0]
            steps.append(
                TraceStep(
                    tick=tick,
                    from_state=t.from_state,
                    to_state=t.to_state,
                    triggered_rule=t.trigger,
                    note=t.guard or "",
                )
            )
            current = t.to_state
            visited_states.add(current)
            tick += 1

        reachable = reachable_states(self.config)
        unreached = [s for s in sm.states if s not in reachable]

        return ExecutionTrace(
            steps=steps,
            reached_final=current in finals,
            final_state=current,
            unreached_states=unreached,
        )

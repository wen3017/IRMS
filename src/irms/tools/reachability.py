"""确定性审查工具：状态机可达性分析。"""

from __future__ import annotations

from irms.models.rules import RuleConfig


def reachable_states(config: RuleConfig) -> set[str]:
    """从 initial 出发，沿 transitions 做 BFS，返回可达状态集合。"""
    adjacency: dict[str, list[str]] = {}
    for t in config.transitions:
        adjacency.setdefault(t.from_state, []).append(t.to_state)

    visited: set[str] = set()
    queue = [config.state_machine.initial]
    while queue:
        cur = queue.pop(0)
        if cur in visited:
            continue
        visited.add(cur)
        queue.extend(adjacency.get(cur, []))
    return visited


def unreachable_states(config: RuleConfig) -> list[str]:
    """返回声明了但从 initial 不可达的状态。"""
    reachable = reachable_states(config)
    return [s for s in config.state_machine.states if s not in reachable]


def can_reach_any_final(config: RuleConfig) -> bool:
    """是否能从 initial 到达任一终态。"""
    reachable = reachable_states(config)
    return any(f in reachable for f in config.state_machine.finals)


def dead_states(config: RuleConfig) -> list[str]:
    """无出边的非终态（死状态）。"""
    has_out = {t.from_state for t in config.transitions}
    finals = set(config.state_machine.finals)
    return [s for s in config.state_machine.states if s not in has_out and s not in finals]

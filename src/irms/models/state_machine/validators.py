"""状态机图结构与引用校验。"""

from __future__ import annotations

from collections import defaultdict, deque

from irms.models.state_machine.enums import StateType, TransitionType
from irms.models.state_machine.state import State
from irms.models.state_machine.transition import Transition


def validate_state_machine_graph(
    states: list[State],
    transitions: list[Transition],
    initial_state_id: str,
) -> None:
    state_by_id = _unique_by_id("states", states)
    _unique_by_id("transitions", transitions)

    if initial_state_id not in state_by_id:
        raise ValueError(f"initial_state_id references unknown state {initial_state_id!r}")

    initial_states = [state for state in states if state.state_type == StateType.INITIAL]
    if len(initial_states) != 1:
        raise ValueError("state machine must contain exactly one INITIAL state")
    if initial_states[0].id != initial_state_id:
        raise ValueError("initial_state_id must point to the single INITIAL state")

    terminal_state_ids = {state.id for state in states if state.terminal}
    if not terminal_state_ids:
        raise ValueError("state machine must contain at least one terminal state")

    incoming: dict[str, list[Transition]] = defaultdict(list)
    outgoing: dict[str, list[Transition]] = defaultdict(list)
    transition_conflicts: dict[tuple[str, str, int, str | None], Transition] = {}

    for transition in transitions:
        if transition.from_state not in state_by_id:
            raise ValueError(f"transition {transition.id!r}.from_state references unknown state {transition.from_state!r}")
        if transition.to_state not in state_by_id:
            raise ValueError(f"transition {transition.id!r}.to_state references unknown state {transition.to_state!r}")
        if transition.from_state == transition.to_state and not transition.allow_self_loop:
            raise ValueError(f"transition {transition.id!r} is a self-loop but allow_self_loop=false")

        source_state = state_by_id[transition.from_state]
        if source_state.terminal:
            is_explicit_recovery = (
                transition.allow_from_terminal
                and transition.transition_type == TransitionType.RECOVERY
            )
            if not is_explicit_recovery:
                raise ValueError(f"terminal state {source_state.id!r} cannot have ordinary outgoing transitions")

        guard_expression = transition.guard.expression if transition.guard else None
        conflict_key = (
            transition.from_state,
            transition.trigger.value,
            int(transition.priority),
            guard_expression,
        )
        previous = transition_conflicts.get(conflict_key)
        if previous and previous.to_state != transition.to_state:
            raise ValueError(
                "conflicting transitions from same state with same trigger, priority and guard: "
                f"{previous.id!r} -> {transition.id!r}"
            )
        transition_conflicts[conflict_key] = transition

        incoming[transition.to_state].append(transition)
        outgoing[transition.from_state].append(transition)

    for state in states:
        if state.id != initial_state_id and not incoming[state.id]:
            raise ValueError(f"non-initial state {state.id!r} has no incoming transition")
        if not state.terminal and not outgoing[state.id]:
            raise ValueError(f"non-terminal state {state.id!r} has no outgoing transition")
        if not incoming[state.id] and not outgoing[state.id] and state.id != initial_state_id:
            raise ValueError(f"state {state.id!r} is isolated")

    reachable = _reachable_from(initial_state_id, outgoing)
    unreachable = sorted(set(state_by_id) - reachable)
    if unreachable:
        raise ValueError(f"unreachable states from initial state: {unreachable}")

    normal_state_ids = {
        state.id for state in states
        if state.state_type not in {StateType.FAILED, StateType.CANCELLED}
    }
    not_reachable_normal = sorted(normal_state_ids - reachable)
    if not_reachable_normal:
        raise ValueError(f"normal business states are not reachable: {not_reachable_normal}")

    can_reach_terminal = _states_that_can_reach_terminal(terminal_state_ids, incoming)
    no_terminal_path = sorted(
        state_id for state_id, state in state_by_id.items()
        if not state.terminal and state_id not in can_reach_terminal
    )
    if no_terminal_path:
        raise ValueError(f"states without path to any terminal state: {no_terminal_path}")


def _unique_by_id(collection_name: str, items):
    seen = {}
    duplicates = []
    for item in items:
        if item.id in seen:
            duplicates.append(item.id)
        seen[item.id] = item
    if duplicates:
        raise ValueError(f"{collection_name} contains duplicate ids: {sorted(set(duplicates))}")
    return seen


def _reachable_from(initial_state_id: str, outgoing: dict[str, list[Transition]]) -> set[str]:
    reachable: set[str] = set()
    queue: deque[str] = deque([initial_state_id])
    while queue:
        state_id = queue.popleft()
        if state_id in reachable:
            continue
        reachable.add(state_id)
        for transition in outgoing.get(state_id, []):
            queue.append(transition.to_state)
    return reachable


def _states_that_can_reach_terminal(
    terminal_state_ids: set[str],
    incoming: dict[str, list[Transition]],
) -> set[str]:
    reachable: set[str] = set()
    queue: deque[str] = deque(terminal_state_ids)
    while queue:
        state_id = queue.popleft()
        if state_id in reachable:
            continue
        reachable.add(state_id)
        for transition in incoming.get(state_id, []):
            queue.append(transition.from_state)
    return reachable

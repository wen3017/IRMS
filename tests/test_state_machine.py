"""1.3 状态机模型基础校验测试。"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from irms.models.state_machine import StateMachine, state_machine_json_schema

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "basic_task_state_machine.json"


@pytest.fixture()
def valid_data() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_valid_state_machine(valid_data: dict) -> None:
    state_machine = StateMachine.model_validate(valid_data)
    assert state_machine.initial_state_id == "S_INITIAL"
    assert any(state.terminal for state in state_machine.states)


def test_export_state_machine_json_schema() -> None:
    schema = state_machine_json_schema()
    assert schema["title"] == "StateMachine"
    assert "states" in schema["properties"]
    assert "transitions" in schema["properties"]


def test_multiple_initial_states(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    another_initial = deepcopy(data["states"][1])
    another_initial["id"] = "S_INITIAL_2"
    another_initial["state_type"] = "INITIAL"
    data["states"].append(another_initial)
    data["transitions"].append({
        "id": "T_INITIAL_2_FAILED",
        "from_state": "S_INITIAL_2",
        "to_state": "S_FAILED",
        "trigger": "EXCEPTION_EVENT",
        "priority": 0,
        "transition_type": "EXCEPTION",
    })

    with pytest.raises(ValidationError, match="exactly one INITIAL"):
        StateMachine.model_validate(data)


def test_initial_state_missing(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["initial_state_id"] = "UNKNOWN"

    with pytest.raises(ValidationError, match="initial_state_id references unknown state"):
        StateMachine.model_validate(data)


def test_duplicate_state_id(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["states"].append(deepcopy(data["states"][1]))

    with pytest.raises(ValidationError, match="states contains duplicate ids"):
        StateMachine.model_validate(data)


def test_duplicate_transition_id(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["transitions"].append(deepcopy(data["transitions"][0]))

    with pytest.raises(ValidationError, match="transitions contains duplicate ids"):
        StateMachine.model_validate(data)


def test_transition_references_unknown_state(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["transitions"][0]["to_state"] = "UNKNOWN"

    with pytest.raises(ValidationError, match="to_state references unknown state"):
        StateMachine.model_validate(data)


def test_no_terminal_state(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    for state in data["states"]:
        if state["terminal"]:
            state["terminal"] = False
            state["state_type"] = "EXECUTING"

    with pytest.raises(ValidationError, match="at least one terminal state"):
        StateMachine.model_validate(data)


def test_unreachable_state(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["states"].extend([
        {
            "id": "S_UNREACHABLE_A",
            "name": "不可达 A",
            "state_type": "WAITING",
            "description": "测试不可达状态。",
            "terminal": False,
            "timeout": None,
            "entry_actions": [],
            "exit_actions": [],
            "metadata": {},
        },
        {
            "id": "S_UNREACHABLE_B",
            "name": "不可达 B",
            "state_type": "WAITING",
            "description": "测试不可达状态。",
            "terminal": False,
            "timeout": None,
            "entry_actions": [],
            "exit_actions": [],
            "metadata": {},
        },
    ])
    data["transitions"].extend([
        {
            "id": "T_UNREACHABLE_A_B",
            "from_state": "S_UNREACHABLE_A",
            "to_state": "S_UNREACHABLE_B",
            "trigger": "BUSINESS_EVENT",
            "priority": 0,
            "transition_type": "NORMAL",
        },
        {
            "id": "T_UNREACHABLE_B_A",
            "from_state": "S_UNREACHABLE_B",
            "to_state": "S_UNREACHABLE_A",
            "trigger": "BUSINESS_EVENT",
            "priority": 0,
            "transition_type": "NORMAL",
        },
    ])

    with pytest.raises(ValidationError, match="unreachable states"):
        StateMachine.model_validate(data)


def test_terminal_state_illegal_outgoing(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["transitions"].append({
        "id": "T_COMPLETED_EXECUTING",
        "from_state": "S_COMPLETED",
        "to_state": "S_EXECUTING",
        "trigger": "BUSINESS_EVENT",
        "priority": 0,
        "transition_type": "NORMAL",
    })

    with pytest.raises(ValidationError, match="cannot have ordinary outgoing transitions"):
        StateMachine.model_validate(data)


def test_invalid_timeout(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["states"][1]["timeout"] = 0

    with pytest.raises(ValidationError):
        StateMachine.model_validate(data)


def test_transition_conflict(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["transitions"].append({
        "id": "T_WAITING_FAILED_CONFLICT",
        "from_state": "S_WAITING",
        "to_state": "S_FAILED",
        "trigger": "DISPATCH_EVENT",
        "guard": None,
        "actions": [],
        "priority": 0,
        "timeout": None,
        "description": "同来源、同触发、同优先级且同 guard，但目标不同。",
        "transition_type": "EXCEPTION",
        "allow_self_loop": False,
        "allow_from_terminal": False,
    })

    with pytest.raises(ValidationError, match="conflicting transitions"):
        StateMachine.model_validate(data)

"""1.2 场景模型基础校验测试。"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from irms.models.scenario import ScenarioModel, scenario_json_schema

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "shelf_to_person.json"


@pytest.fixture()
def valid_data() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_valid_scenario_model(valid_data: dict) -> None:
    scenario = ScenarioModel.model_validate(valid_data)
    assert scenario.basic_info.scene_type == "货架到人"
    assert scenario.robot_types[0].robot_type_id == "RT-SHELF-AMR"
    assert scenario.manual_confirmations


def test_export_scenario_json_schema() -> None:
    schema = scenario_json_schema()
    assert schema["title"] == "ScenarioModel"
    assert "basic_info" in schema["properties"]
    assert "manual_confirmations" in schema["properties"]


def test_enum_error(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["basic_info"]["scene_type"] = "不存在的场景"

    with pytest.raises(ValidationError):
        ScenarioModel.model_validate(data)


def test_numeric_out_of_range(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["battery_policy"]["low_battery_percent"] = 101

    with pytest.raises(ValidationError):
        ScenarioModel.model_validate(data)


def test_duplicate_id(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["robot_types"].append(deepcopy(data["robot_types"][0]))

    with pytest.raises(ValidationError, match="duplicate ids"):
        ScenarioModel.model_validate(data)


def test_invalid_reference(valid_data: dict) -> None:
    data = deepcopy(valid_data)
    data["task_types"][0]["allowed_robot_type_ids"] = ["UNKNOWN-ROBOT-TYPE"]

    with pytest.raises(ValidationError, match="references unknown ids"):
        ScenarioModel.model_validate(data)

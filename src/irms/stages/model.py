"""model 环节：校验并标准化场景模型（确定性）。"""

from __future__ import annotations

from irms.context import RunContext
from irms.models.scenario import ScenarioModel
from irms.stages.base import StageResult
from irms.tools.schema_validator import SchemaValidationError, validate


class ModelStage:
    name = "model"
    artifact_name = "02_model.json"
    input_artifact = "01_scenario.json"

    def run(self, ctx: RunContext) -> StageResult:
        try:
            data = ctx.read_json(ctx.artifact(self.input_artifact))
            # 二次校验 + 标准化（pydantic 补默认值）
            scenario = validate(ScenarioModel, data)
            path = ctx.write_artifact(self.artifact_name, scenario)
            return StageResult(status="success", artifact_path=str(path))
        except SchemaValidationError as e:
            return StageResult(status="failed", error=f"模型标准化失败: {e}")
        except Exception as e:
            return StageResult(status="failed", error=str(e))

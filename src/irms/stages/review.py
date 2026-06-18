"""review 环节：规则审查 Agent 调用确定性工具并汇总报告。"""

from __future__ import annotations

from irms.context import RunContext
from irms.models.rules import RuleConfig
from irms.stages.base import StageResult
from irms.tools.schema_validator import validate


class ReviewStage:
    name = "review"
    artifact_name = "04_review.json"
    input_artifact = "03_config.json"

    def run(self, ctx: RunContext) -> StageResult:
        try:
            data = ctx.read_json(ctx.artifact(self.input_artifact))
            config = validate(RuleConfig, data)
            from irms.agents.review_agent import review_config

            report = review_config(config)
            path = ctx.write_artifact(self.artifact_name, report)
            return StageResult(status="success", artifact_path=str(path),
                               meta={"passed": report.passed})
        except Exception as e:
            return StageResult(status="failed", error=str(e))

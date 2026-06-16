"""sandbox 环节：状态机离散事件模拟（确定性）。"""

from __future__ import annotations

from irms.context import RunContext
from irms.models.rules import RuleConfig
from irms.sandbox.simulator import Simulator
from irms.stages.base import StageResult
from irms.tools.schema_validator import validate


class SandboxStage:
    name = "sandbox"
    artifact_name = "05_trace.json"
    input_artifact = "03_config.json"

    def run(self, ctx: RunContext) -> StageResult:
        try:
            data = ctx.read_json(ctx.artifact(self.input_artifact))
            config = validate(RuleConfig, data)
            trace = Simulator(config).run()
            path = ctx.write_artifact(self.artifact_name, trace)
            return StageResult(status="success", artifact_path=str(path),
                               meta={"reached_final": trace.reached_final})
        except Exception as e:
            return StageResult(status="failed", error=str(e))

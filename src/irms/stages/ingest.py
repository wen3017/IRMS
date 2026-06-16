"""ingest 环节：文档 → 场景 JSON（agent 抽取 / 或直读 JSON）。"""

from __future__ import annotations

import json

from irms.context import RunContext
from irms.models.scenario import ScenarioModel
from irms.stages.base import StageResult
from irms.tools.schema_validator import SchemaValidationError, validate


class IngestStage:
    name = "ingest"
    artifact_name = "01_scenario.json"

    def run(self, ctx: RunContext) -> StageResult:
        try:
            if ctx.input_type == "json":
                data = ctx.read_json(ctx.input_path)
                scenario = validate(ScenarioModel, data)
            else:
                # 自然语言文档 → 走 agent 抽取
                from irms.agents.ingest_agent import ingest_document

                doc_text = ctx.input_path.read_text(encoding="utf-8")
                scenario = ingest_document(doc_text)
            path = ctx.write_artifact(self.artifact_name, scenario)
            return StageResult(status="success", artifact_path=str(path))
        except (SchemaValidationError, json.JSONDecodeError) as e:
            return StageResult(status="failed", error=f"场景校验失败: {e}")
        except Exception as e:  # agent 不可用等
            return StageResult(status="failed", error=str(e))

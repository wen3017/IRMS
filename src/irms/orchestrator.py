"""确定性 pipeline 编排：顺序驱动 5 环节，管理进度、断点续跑、fail-fast。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from irms.context import RunContext
from irms.stages import PIPELINE, STAGE_BY_NAME
from irms.stages.base import Stage, StageResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Orchestrator:
    def __init__(self, ctx: RunContext):
        self.ctx = ctx

    def run_all(self) -> bool:
        """顺序执行全部环节。返回是否全部成功（fail-fast）。"""
        for stage in PIPELINE:
            ok = self._run_stage(stage)
            if not ok:
                self.ctx.save_progress()
                return False
        self.ctx.save_progress()
        return True

    def run_single(self, name: str) -> bool:
        stage = STAGE_BY_NAME[name]
        ok = self._run_stage(stage, allow_skip=False)
        self.ctx.save_progress()
        return ok

    def _run_stage(self, stage: Stage, allow_skip: bool = True) -> bool:
        prog = self.ctx.progress.stages.get(stage.name)
        if allow_skip and not self.ctx.force and prog and prog.status == "success":
            print(f"[skip] {stage.name} (已成功，断点续跑跳过)")
            return True

        self.ctx.progress.mark(stage.name, status="running", started_at=_now(), error=None)
        self.ctx.save_progress()

        result: StageResult = stage.run(self.ctx)

        if result.status == "success":
            self.ctx.progress.mark(
                stage.name, status="success",
                artifact_path=result.artifact_path, finished_at=_now(),
            )
            extra = f" [{result.meta}]" if result.meta else ""
            print(f"[ok]   {stage.name} -> {result.artifact_path}{extra}")
            return True

        self.ctx.progress.mark(
            stage.name, status="failed", finished_at=_now(), error=result.error,
        )
        print(f"[fail] {stage.name}: {result.error}")
        return False


def build_context(input_path: Path, out_dir: Path, from_json: bool, force: bool) -> RunContext:
    suffix = input_path.suffix.lower()
    if from_json or suffix == ".json":
        input_type = "json"
    else:
        input_type = "md"
    return RunContext(input_path=input_path, input_type=input_type, out_dir=out_dir, force=force)

"""运行上下文与进度记录。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

StageStatus = Literal["pending", "running", "success", "failed", "skipped"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StageProgress(BaseModel):
    status: StageStatus = "pending"
    artifact_path: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None


class RunProgress(BaseModel):
    """全流程进度记录，落盘为 progress.json，支持断点续跑。"""

    run_id: str
    input_path: str
    input_type: str  # "md" | "json"
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)
    stages: dict[str, StageProgress] = Field(default_factory=dict)

    def mark(self, name: str, **kwargs: Any) -> None:
        sp = self.stages.setdefault(name, StageProgress())
        for k, v in kwargs.items():
            setattr(sp, k, v)
        self.updated_at = _now()


class RunContext:
    """持有 run 工作目录、进度、上游产物访问与 agent 句柄。"""

    PROGRESS_FILE = "progress.json"

    def __init__(self, input_path: Path, input_type: str, out_dir: Path, force: bool = False):
        self.input_path = input_path
        self.input_type = input_type
        self.out_dir = out_dir
        self.force = force
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.progress = self._load_or_init_progress()

    def _load_or_init_progress(self) -> RunProgress:
        p = self.out_dir / self.PROGRESS_FILE
        if p.exists() and not self.force:
            return RunProgress.model_validate_json(p.read_text(encoding="utf-8"))
        return RunProgress(
            run_id=datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            input_path=str(self.input_path),
            input_type=self.input_type,
        )

    def save_progress(self) -> None:
        p = self.out_dir / self.PROGRESS_FILE
        p.write_text(self.progress.model_dump_json(indent=2), encoding="utf-8")

    def artifact(self, filename: str) -> Path:
        return self.out_dir / filename

    def write_artifact(self, filename: str, model: BaseModel) -> Path:
        path = self.artifact(filename)
        path.write_text(model.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
        return path

    def read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

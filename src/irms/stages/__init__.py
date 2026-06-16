"""管线 5 环节。"""

from irms.stages.base import Stage, StageResult
from irms.stages.generate import GenerateStage
from irms.stages.ingest import IngestStage
from irms.stages.model import ModelStage
from irms.stages.review import ReviewStage
from irms.stages.sandbox import SandboxStage

# 顺序即管线执行顺序
PIPELINE: list[Stage] = [
    IngestStage(),
    ModelStage(),
    GenerateStage(),
    ReviewStage(),
    SandboxStage(),
]

STAGE_BY_NAME = {s.name: s for s in PIPELINE}

__all__ = [
    "Stage",
    "StageResult",
    "IngestStage",
    "ModelStage",
    "GenerateStage",
    "ReviewStage",
    "SandboxStage",
    "PIPELINE",
    "STAGE_BY_NAME",
]

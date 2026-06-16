"""端到端薄切片冒烟测试（--from-json 全确定性路径，无需 API key）。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from irms.context import RunContext
from irms.orchestrator import Orchestrator

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "shelf_to_person.json"


@pytest.fixture(autouse=True)
def _no_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """强制走全确定性路径（generate 用基线生成器），保证测试快速可复现。

    直接 patch 凭证判定，避免受 .env 自动加载影响。
    """
    import irms.agents.base as agent_base

    monkeypatch.setattr(agent_base, "has_credentials", lambda: False)


def test_pipeline_end_to_end(tmp_path: Path) -> None:
    ctx = RunContext(input_path=EXAMPLE, input_type="json", out_dir=tmp_path, force=True)
    ok = Orchestrator(ctx).run_all()
    assert ok is True

    # 五份产物 + 进度文件均存在
    for name in [
        "01_scenario.json", "02_model.json", "03_config.json",
        "04_review.json", "05_trace.json", "progress.json",
    ]:
        assert (tmp_path / name).exists(), f"缺少产物 {name}"

    # 沙箱轨迹应到达终态
    trace = json.loads((tmp_path / "05_trace.json").read_text(encoding="utf-8"))
    assert trace["reached_final"] is True
    assert trace["final_state"] == "completed"
    assert len(trace["steps"]) > 0


def test_resume_skips_completed(tmp_path: Path) -> None:
    ctx = RunContext(input_path=EXAMPLE, input_type="json", out_dir=tmp_path, force=True)
    assert Orchestrator(ctx).run_all() is True

    # 第二次运行（不 force）应全部跳过且仍成功
    ctx2 = RunContext(input_path=EXAMPLE, input_type="json", out_dir=tmp_path, force=False)
    assert Orchestrator(ctx2).run_all() is True
    for sp in ctx2.progress.stages.values():
        assert sp.status == "success"

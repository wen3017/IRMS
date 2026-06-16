"""Typer CLI 入口。"""

from __future__ import annotations

from pathlib import Path

import typer

from irms import __version__
from irms.config import resolve_output_dir
from irms.orchestrator import Orchestrator, build_context

app = typer.Typer(
    name="irms",
    help="iRMS Rule Agent: AMR 仓储任务流规则生成与沙箱验证工具",
    no_args_is_help=True,
)


@app.command()
def run(
    scenario: Path = typer.Argument(..., help="场景输入：自然语言文档(.md) 或结构化 JSON"),
    out: str = typer.Option(None, "--out", help="产物输出目录，默认 ./output"),
    from_json: bool = typer.Option(False, "--from-json", help="直接读取 JSON，跳过 agent 抽取"),
    force: bool = typer.Option(False, "--force", help="忽略进度，强制重跑所有环节"),
    stage: str = typer.Option(None, "--stage", help="只运行指定环节"),
) -> None:
    """运行完整 5 环节管线（或指定单环节）。"""
    out_dir = resolve_output_dir(out)
    ctx = build_context(scenario, out_dir, from_json, force)
    orch = Orchestrator(ctx)

    ok = orch.run_single(stage) if stage else orch.run_all()
    if ok:
        typer.echo(f"\n完成。产物目录: {out_dir}")
    else:
        typer.echo("\n管线中断（fail-fast）。详见 progress.json")
        raise typer.Exit(code=1)


def _single(scenario: Path, stage_name: str, out: str | None, from_json: bool, force: bool) -> None:
    out_dir = resolve_output_dir(out)
    ctx = build_context(scenario, out_dir, from_json, force)
    ok = Orchestrator(ctx).run_single(stage_name)
    if not ok:
        raise typer.Exit(code=1)


@app.command()
def ingest(scenario: Path, out: str = typer.Option(None, "--out"),
           from_json: bool = typer.Option(False, "--from-json")) -> None:
    """仅运行 ingest 环节。"""
    _single(scenario, "ingest", out, from_json, force=True)


@app.command()
def model(scenario: Path, out: str = typer.Option(None, "--out")) -> None:
    """仅运行 model 环节（需已有 01_scenario.json）。"""
    _single(scenario, "model", out, from_json=True, force=True)


@app.command()
def generate(scenario: Path, out: str = typer.Option(None, "--out")) -> None:
    """仅运行 generate 环节（需已有 02_model.json）。"""
    _single(scenario, "generate", out, from_json=True, force=True)


@app.command()
def review(scenario: Path, out: str = typer.Option(None, "--out")) -> None:
    """仅运行 review 环节（需已有 03_config.json）。"""
    _single(scenario, "review", out, from_json=True, force=True)


@app.command()
def sandbox(scenario: Path, out: str = typer.Option(None, "--out")) -> None:
    """仅运行 sandbox 环节（需已有 03_config.json）。"""
    _single(scenario, "sandbox", out, from_json=True, force=True)


@app.command()
def version() -> None:
    """打印版本号。"""
    typer.echo(f"irms {__version__}")


if __name__ == "__main__":
    app()

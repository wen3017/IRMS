"""review 环节：确定性审查 + agent 总结。"""

from __future__ import annotations

from irms.context import RunContext
from irms.models.review import CheckResult, ReviewReport
from irms.models.rules import RuleConfig
from irms.stages.base import StageResult
from irms.tools.conflict import find_conflicts
from irms.tools.reachability import can_reach_any_final, dead_states, unreachable_states
from irms.tools.schema_validator import validate


def _run_checks(config: RuleConfig) -> list[CheckResult]:
    checks: list[CheckResult] = []

    reach_final = can_reach_any_final(config)
    checks.append(CheckResult(
        name="reachability", passed=reach_final,
        severity="error" if not reach_final else "info",
        detail="可从初始状态到达终态" if reach_final else "无法从初始状态到达任何终态",
    ))

    unreached = unreachable_states(config)
    checks.append(CheckResult(
        name="unreachable_states", passed=not unreached,
        severity="warning" if unreached else "info",
        detail=f"不可达状态: {unreached}" if unreached else "无不可达状态",
    ))

    dead = dead_states(config)
    checks.append(CheckResult(
        name="dead_states", passed=not dead,
        severity="warning" if dead else "info",
        detail=f"死状态(无出边非终态): {dead}" if dead else "无死状态",
    ))

    all_rules = (
        config.robot_dispatch_rules + config.workstation_rules + config.battery_rules
        + config.exception_rules + config.cancellation_rules
    )
    conflicts = find_conflicts(all_rules)
    checks.append(CheckResult(
        name="rule_conflict", passed=not conflicts,
        severity="warning" if conflicts else "info",
        detail=f"规则冲突对: {conflicts}" if conflicts else "无规则冲突",
    ))

    missing_exc = len(config.exception_rules) == 0
    checks.append(CheckResult(
        name="missing_exception_branch", passed=not missing_exc,
        severity="warning" if missing_exc else "info",
        detail="缺少异常处理规则" if missing_exc else "存在异常处理规则",
    ))

    return checks


class ReviewStage:
    name = "review"
    artifact_name = "04_review.json"
    input_artifact = "03_config.json"

    def run(self, ctx: RunContext) -> StageResult:
        try:
            data = ctx.read_json(ctx.artifact(self.input_artifact))
            config = validate(RuleConfig, data)
            checks = _run_checks(config)
            passed = all(c.passed or c.severity != "error" for c in checks)

            from irms.agents.review_agent import summarize

            summary = summarize(checks)

            report = ReviewReport(checks=checks, summary=summary, passed=passed)
            path = ctx.write_artifact(self.artifact_name, report)
            return StageResult(status="success", artifact_path=str(path),
                               meta={"passed": passed})
        except Exception as e:
            return StageResult(status="failed", error=str(e))

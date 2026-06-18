"""规则审查 Agent：调用确定性审查工具并汇总风险与建议。"""

from __future__ import annotations

from irms.agents.base import AgentUnavailableError, BaseAgent
from irms.models.review import CheckResult
from irms.models.review import ReviewReport
from irms.models.rules import RuleConfig
from irms.tools.conflict import find_conflicts
from irms.tools.reachability import can_reach_any_final, dead_states, unreachable_states

SYSTEM_PROMPT = """你是 iRMS 规则审查报告撰写专家。
基于给定的确定性检查结果列表，用简洁中文总结：整体是否通过、存在哪些风险
（如状态不可达、异常分支缺失、规则互斥），给出修复建议；
对需要人工确认的规则，明确说明需要确认的原因。只输出总结文本。
"""


class RuleReviewAgent(BaseAgent):
    """调用确定性审查工具，汇总错误、风险、建议和人工确认点。"""

    name = "rule_review_agent"
    system_prompt = SYSTEM_PROMPT
    allowed_tools: list[str] = []

    def run(self, config: RuleConfig) -> ReviewReport:
        checks = run_deterministic_checks(config)
        passed = all(c.passed or c.severity != "error" for c in checks)
        summary = self._summarize(checks)
        return ReviewReport(checks=checks, summary=summary, passed=passed)

    def _summarize(self, checks: list[CheckResult]) -> str:
        payload = "\n".join(
            f"- [{c.severity}] {c.name}: {'PASS' if c.passed else 'FAIL'} {c.detail}"
            for c in checks
        )
        try:
            return self.run_text(payload)
        except AgentUnavailableError:
            return self._fallback(checks)

    @staticmethod
    def _fallback(checks: list[CheckResult]) -> str:
        failed = [c for c in checks if not c.passed]
        if not failed:
            return "全部检查通过：状态机可从创建流转到终态，无不可达状态与规则冲突。"
        lines = ["审查发现以下问题："]
        lines += [f"- {c.name}: {c.detail}" for c in failed]
        return "\n".join(lines)


def run_deterministic_checks(config: RuleConfig) -> list[CheckResult]:
    """调用确定性审查工具，生成结构化检查结果。"""

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
        + config.exception_rules + config.cancellation_rules + config.priority_rules
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
        detail="缺少异常处理规则，需要人工确认是否允许无异常分支上线"
        if missing_exc else "存在异常处理规则",
    ))

    manual = _manual_confirmation_checks(config)
    checks.extend(manual)
    return checks


def _manual_confirmation_checks(config: RuleConfig) -> list[CheckResult]:
    checks: list[CheckResult] = []
    guarded = [t for t in config.transitions if t.guard]
    if guarded:
        checks.append(CheckResult(
            name="manual_confirmation",
            passed=True,
            severity="info",
            detail=f"存在需业务确认的带条件流转: {[t.trigger for t in guarded]}",
        ))
    return checks


def review_config(config: RuleConfig) -> ReviewReport:
    return RuleReviewAgent().run(config)

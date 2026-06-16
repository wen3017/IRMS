"""ReviewSummaryAgent：确定性检查结果 → 自然语言审查总结。"""

from __future__ import annotations

from irms.agents.base import AgentUnavailableError, BaseAgent
from irms.models.review import CheckResult

SYSTEM_PROMPT = """你是 iRMS 规则审查报告撰写专家。
基于给定的确定性检查结果列表，用简洁中文总结：整体是否通过、存在哪些风险
（如状态不可达、异常分支缺失、规则互斥），并给出修复建议。只输出总结文本。
"""


class ReviewSummaryAgent(BaseAgent):
    """检查结果 → 自然语言审查总结；agent 不可用时回退确定性拼接。"""

    name = "review_summary_agent"
    system_prompt = SYSTEM_PROMPT
    allowed_tools: list[str] = []

    def run(self, checks: list[CheckResult]) -> str:
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


def summarize(checks: list[CheckResult]) -> str:
    return ReviewSummaryAgent().run(checks)

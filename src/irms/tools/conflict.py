"""确定性审查工具：规则互斥/重叠检测。"""

from __future__ import annotations

from irms.models.rules import Rule


def find_conflicts(rules: list[Rule]) -> list[tuple[str, str]]:
    """检测条件相同但动作不同的规则对（潜在互斥）。

    雏形阶段用简单的字符串归一化比较，后续可替换为条件表达式语义比较。
    """
    conflicts: list[tuple[str, str]] = []
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            a, b = rules[i], rules[j]
            same_condition = a.condition.strip() == b.condition.strip()
            diff_action = a.action.strip() != b.action.strip()
            if same_condition and diff_action:
                conflicts.append((a.id, b.id))
    return conflicts

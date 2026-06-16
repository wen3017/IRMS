# iRMS Rule Agent —— Python 版详细设计方案

> 本文档是 `feat/python-impl` 分支的实现依据。目标：搭建端到端薄切片的 CLI 工具雏形，覆盖
> 「场景描述 → 场景模型 → 状态机/流转 → 规则配置 → 审查 → 沙箱轨迹」完整管线，每环节最小实现。

## 1. 设计目标与边界

### 1.1 雏形目标
- 跑通端到端薄切片：输入一个场景（自然语言文档或 JSON），输出可审查的规则配置 + 沙箱执行轨迹。
- 验证整体架构可行性：确定性 pipeline 串联 + 每环节可插 agent 或确定性节点。
- 沉淀稳定的数据 schema，为后续 TS 版移植（`feat/ts-impl`）和环节加深提供基础。

### 1.2 本期边界（明确不做）
- 不做多任务/多机器人并发调度、资源竞争、电量动态仿真（沙箱仅单任务单机器人）。
- 不做进程级/容器级隔离（仅独立工作目录 + 纯内存模拟）。
- 不做 Web 可视化、不做 TS 版（TS 在独立分支后续移植）。
- 不做规则的图形化编辑器、不接真实 iRMS 系统 API。

## 2. 总体架构

```
                          ┌──────────────────────────────────────────┐
   场景输入                │            Orchestrator (确定性)            │
  (md / json)  ──────────▶│  读进度 JSON → 顺序驱动 5 环节 → 落盘产物     │
                          └──────────────────────────────────────────┘
                                │      │       │        │        │
                              ingest  model  generate  review  sandbox
                                │      │       │        │        │
                            ┌───┴──────┴───────┴────────┴────────┴────┐
                            │ 每环节 = 单/多 agent  或  纯确定性节点      │
                            │ agent 可调用 tools/ 下的确定性工具          │
                            └─────────────────────────────────────────┘
                                              │
                                       output/ (落盘)
                          01_model.json … 05_trace.json + progress.json
```

- **Orchestrator**：纯确定性控制流。负责环节顺序、进度记录、断点续跑、fail-fast、产物落盘。
- **Stage（环节）**：统一接口，内部可调用 agent 或纯确定性逻辑。
- **Agent**：基于 `claude-agent-sdk`，每环节有独立 system prompt + 允许的 tools。
- **Tools**：确定性工具（可达性分析、沙箱模拟等），既被 agent 调用，也可被确定性环节直接调用。

## 3. 管线环节（5 环节）

| # | 环节 | 类型 | 输入 | 输出产物 | 说明 |
|---|------|------|------|----------|------|
| 1 | `ingest` | agent / 直读 | 文档(md) 或 scenario.json | `01_scenario.json` | 文档由 LLM agent 抽取为场景 JSON；`--from-json` 直接读取跳过 agent |
| 2 | `model` | 确定性 | `01_scenario.json` | `02_model.json` | 校验 + 标准化为统一场景模型（pydantic 校验、补默认值） |
| 3 | `generate` | agent | `02_model.json` | `03_config.json` | 生成任务状态机 + 状态流转 + 各类规则配置 |
| 4 | `review` | 确定性 tool + agent 总结 | `03_config.json` | `04_review.json` | 确定性审查（可达性/异常分支缺失/规则互斥）+ agent 生成自然语言报告 |
| 5 | `sandbox` | 确定性 | `03_config.json` | `05_trace.json` | 单任务状态机离散事件模拟，输出创建→完成轨迹 + 规则触发记录 |

### 3.1 环节统一接口
```python
class Stage(Protocol):
    name: str
    def run(self, ctx: RunContext) -> StageResult: ...
```
- `RunContext`：持有 run 工作目录、配置、上游产物访问、agent runner 句柄。
- `StageResult`：`status`(success/failed/skipped)、`artifact_path`、`error`、`meta`。

## 4. 数据模型（schema）

所有 schema 用 pydantic v2 定义于 `models/`，是 Python 与 TS 两版的共同契约。

### 4.1 场景模型 ScenarioModel（`01/02`）
```
ScenarioModel
├── scenario_type: str            # 货架到人 / 料箱到人 / 分拣 / 补货 / 充电 ...
├── robots: list[RobotSpec]       # type, capabilities, battery_thresholds
├── workstations: list[Workstation]  # id, type, constraints
├── task_flow: list[FlowStep]     # 标准任务流程步骤
├── locations: list[Location]     # 点位/区域约束
├── battery: BatteryPolicy        # 低电阈值、充电触发
├── exceptions: list[ExceptionBranch]  # 异常分支
├── cancellation: CancellationPolicy   # 任务取消规则
└── priority: PriorityPolicy      # 优先级规则
```

### 4.2 配置模型 RuleConfig（`03`）
```
RuleConfig
├── state_machine: StateMachine   # states[], initial, finals[]
├── transitions: list[Transition] # from, to, trigger, guard(条件)
├── robot_dispatch_rules: list[Rule]   # 机器人接单规则
├── workstation_rules: list[Rule]      # 工作站约束规则
├── battery_rules: list[Rule]          # 电量规则
├── exception_rules: list[Rule]        # 异常处理规则
└── cancellation_rules: list[Rule]     # 任务取消规则
```

### 4.3 审查报告 ReviewReport（`04`）
```
ReviewReport
├── checks: list[CheckResult]     # 每项确定性检查: name, passed, severity, detail
│     ├── reachability            # 从 initial 是否可达所有 final
│     ├── dead_states             # 不可达 / 无出边的状态
│     ├── missing_exception_branch
│     └── rule_conflict           # 规则互斥/重叠
├── summary: str                  # agent 生成的自然语言总结
└── passed: bool
```

### 4.4 沙箱轨迹 ExecutionTrace（`05`）
```
ExecutionTrace
├── steps: list[TraceStep]        # tick, from_state, to_state, triggered_rule, note
├── reached_final: bool
├── final_state: str
└── unreached_states: list[str]
```

### 4.5 进度记录 progress.json
```
RunProgress
├── run_id: str
├── input: {path, type}          # md / json
├── created_at, updated_at
└── stages: dict[name -> {status, artifact_path, started_at, finished_at, error}]
```
- Orchestrator 每环节开始/结束都更新该文件，支持断点续跑（跳过 status==success 的环节），`--force` 忽略并重跑。

## 5. Agent 设计（claude-agent-sdk）

- 凭证：从环境变量 `ANTHROPIC_API_KEY` 读取；缺失时需 agent 的环节直接 fail 并给出明确提示（不静默 mock）。
- 每环节 agent 定义于 `agents/`，包含：独立 system prompt、输出 JSON schema 约束、允许调用的 tools 白名单。
- agent 输出统一要求为符合对应 pydantic schema 的 JSON，由确定性代码二次校验，校验失败即该环节 failed。

| Agent | 职责 | 允许的 tools |
|-------|------|--------------|
| `IngestAgent` | 自然语言文档 → ScenarioModel JSON | （仅文本理解，无外部 tool） |
| `GenerateAgent` | ScenarioModel → RuleConfig JSON | `validate_schema` |
| `ReviewSummaryAgent` | 确定性检查结果 → 自然语言审查总结 | （读检查结果，输出文本） |

确定性环节（model、review 检查、sandbox）不依赖 agent。

## 6. 确定性工具（tools/）

| Tool | 功能 | 被谁用 |
|------|------|--------|
| `reachability` | 基于状态机+流转做 BFS/DFS 可达性分析 | review 环节 / agent |
| `dead_state_detector` | 检测不可达状态、无出边状态 | review 环节 |
| `rule_conflict_checker` | 检测规则条件互斥/重叠 | review 环节 |
| `schema_validator` | 校验任意产物是否符合 pydantic schema | 各环节 / agent |

沙箱模拟器（`sandbox/simulator.py`）：状态机离散事件模拟，确定性逐 tick 推进，单任务单机器人。

## 7. CLI 设计（Typer，命令名 irms）

```
irms run <scenario.(md|json)> [--out ./output] [--from-json] [--force] [--stage NAME]
        # 跑完整 5 环节；--from-json 跳过 ingest 抽取；--force 重跑；--stage 只跑某环节
irms ingest   <doc.md> [--out]      # 单独跑抽取
irms model    <scenario.json> [--out]
irms generate <model.json> [--out]
irms review   <config.json> [--out]
irms sandbox  <config.json> [--out]
irms version
```

退出码：0 成功；非 0 表示某环节 failed（fail-fast）。

## 8. 项目结构

```
irms/
├── pyproject.toml            # uv 管理，定义依赖与 [project.scripts] irms 入口
├── README.md
├── DESIGN.md                 # 本文档
├── .gitignore                # 忽略 output/ .venv/ 等
├── examples/
│   ├── shelf_to_person.md    # 自然语言场景示例
│   └── shelf_to_person.json  # 结构化场景示例
├── src/irms/
│   ├── __init__.py
│   ├── cli.py                # Typer 入口
│   ├── orchestrator.py       # 确定性 pipeline + 进度管理
│   ├── context.py            # RunContext / RunProgress
│   ├── config.py             # 全局配置（env、路径）
│   ├── models/
│   │   ├── __init__.py
│   │   ├── scenario.py       # ScenarioModel 及子模型
│   │   ├── rules.py          # RuleConfig / StateMachine / Transition / Rule
│   │   ├── review.py         # ReviewReport / CheckResult
│   │   └── trace.py          # ExecutionTrace / TraceStep
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py           # AgentRunner 封装 claude-agent-sdk
│   │   ├── ingest_agent.py
│   │   ├── generate_agent.py
│   │   └── review_agent.py
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── base.py           # Stage 协议 + StageResult
│   │   ├── ingest.py
│   │   ├── model.py
│   │   ├── generate.py
│   │   ├── review.py
│   │   └── sandbox.py
│   ├── sandbox/
│   │   ├── __init__.py
│   │   └── simulator.py      # 状态机离散事件模拟器
│   └── tools/
│       ├── __init__.py
│       ├── reachability.py
│       ├── conflict.py
│       └── schema_validator.py
└── tests/
    └── test_smoke.py         # 端到端薄切片冒烟测试（--from-json 路径）
```

## 9. 依赖

- `typer` —— CLI 框架
- `pydantic>=2` —— 数据模型与校验
- `claude-agent-sdk` —— agent / sub-agent 机制
- `rich`（typer 自带可选）—— 终端输出
- dev: `pytest`

## 10. 实现里程碑（本期骨架）

1. uv 初始化项目 + pyproject.toml + 包结构占位。
2. 定义全部 pydantic schema（models/）。
3. 实现 orchestrator + 进度 JSON + 5 个 stage 占位（确定性环节给出最小可运行实现，agent 环节先接口齐全）。
4. 实现确定性核心：model 校验、reachability/conflict 审查、sandbox 模拟器（保证 `--from-json` 全确定性路径端到端跑通）。
5. agents/ 接入 claude-agent-sdk 接口（缺 key 明确报错）。
6. examples + 冒烟测试，验证 `irms run examples/shelf_to_person.json --from-json` 可跑出 5 份产物 + progress.json。

> 注：本期重点保证 **`--from-json` 的全确定性路径**端到端可运行（不依赖网络/key）；
> agent 抽取与生成路径接口齐备，待有 `ANTHROPIC_API_KEY` 时即可启用。

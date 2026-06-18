# iRMS Rule Agent (Python)

面向 AMR 仓储项目的任务流规则生成与沙箱验证 CLI 工具雏形。

详细设计见 [DESIGN.md](./DESIGN.md)。

## 安装

```bash
uv sync
```

## 配置凭证（仅 agent 环节需要）

`ingest` / `generate` / `review` 环节调用 LLM，需要凭证；纯确定性路径（`--from-json`）无需凭证。

复制模板并填入凭证（`.env` 不纳入 git 管理）：

```bash
cp .env.example .env
```

支持两种鉴权方式：

- 官方 API key：`ANTHROPIC_API_KEY=...`
- 自定义网关：`ANTHROPIC_BASE_URL=...` + `ANTHROPIC_AUTH_TOKEN=...`
- 可选：`IRMS_MODEL=...` 指定模型

## 使用

```bash
# 全确定性路径（无需凭证）：直接传入结构化场景 JSON
uv run irms run examples/shelf_to_person.json --from-json

# 从自然语言文档抽取（需要凭证）
uv run irms run examples/shelf_to_person.md

# 忽略进度，强制完整重跑所有环节
uv run irms run examples/shelf_to_person.md --force

# 只运行指定环节
uv run irms run examples/shelf_to_person.md --stage generate

# 指定产物输出目录（默认 ./output）
uv run irms run examples/shelf_to_person.json --from-json --out output

# 查看版本
uv run irms version
```

### 单环节命令

每个命令读取上一环节的产物，独立运行（始终强制重跑）：

```bash
uv run irms ingest   examples/shelf_to_person.md   # 文档 -> 01_scenario.json
uv run irms model    examples/shelf_to_person.json # 校验标准化 -> 02_model.json
uv run irms generate examples/shelf_to_person.json # 生成规则 -> 03_config.json
uv run irms review   examples/shelf_to_person.json # 审查 -> 04_review.json
uv run irms sandbox  examples/shelf_to_person.json # 沙箱模拟 -> 05_trace.json
```

产物落盘到 `output/`：`01_scenario.json … 05_trace.json` 以及记录进度的 `progress.json`。

## 管线

`ingest → model → generate → review → sandbox`，由确定性 orchestrator 串联：

| 环节 | 类型 | 说明 |
|---|---|---|
| ingest | agent | 自然语言文档 → 结构化场景模型（`--from-json` 时跳过） |
| model | 确定性 | 二次校验并标准化场景模型 |
| generate | 双 agent + 工具 | 任务流生成 Agent 生成状态机/流转；规则生成 Agent 生成机器人、工作站、电量、异常、取消、优先级等规则 |
| review | 规则审查 agent + 工具 | 调用确定性审查工具，汇总错误、风险、建议和人工确认点（无凭证时回退确定性拼接） |
| sandbox | 确定性 | 状态机离散事件模拟，输出执行 trace |

支持断点续跑：成功的环节会记录在 `progress.json`，再次 `run` 时自动跳过；
加 `--force` 或删除 `output/` 可强制完整重跑。失败时 fail-fast 中断。

### Agent 工具能力

确定性校验逻辑通过 in-process MCP server 注册为 agent 可调用工具
（工具名 `mcp__irms__*`），目前任务流生成、规则生成和规则审查会使用：

- `mcp__irms__validate_rule_config`：校验 RuleConfig schema
- `mcp__irms__check_reachability`：检查状态机可达性（终态可达、不可达/死状态）
- `mcp__irms__check_rule_conflict`：检测规则互斥

当前设计包含 4 个业务 Agent：

- `ScenarioParsingAgent`：场景解析，输出标准场景模型
- `TaskFlowGenerationAgent`：生成任务状态机和正常/异常/取消流
- `RuleGenerationAgent`：生成结构化规则配置
- `RuleReviewAgent`：审查规则并输出风险、建议和人工确认说明

## 测试

```bash
uv run pytest -q
```

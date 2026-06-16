"""BaseAgent：所有 agent 的基类，封装 claude-agent-sdk 调用与凭证校验。

通过 `query()` 驱动底层 claude CLI。凭证支持官方 ANTHROPIC_API_KEY，
或自定义网关 ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN（经 options.env 传入）。
缺少凭证时明确报错（不静默 mock）。

子类约定：
- 覆盖类属性 `name` / `system_prompt` / `allowed_tools`；
- 实现 `run(...)` 高层方法（调用 `self.run_json` 或 `self.run_text`）。
"""

from __future__ import annotations

import asyncio
import json
import os

from irms.config import (
    ANTHROPIC_AUTH_TOKEN_ENV,
    ANTHROPIC_BASE_URL_ENV,
    get_auth_token,
    get_base_url,
    get_model,
    has_credentials,
)


class AgentUnavailableError(RuntimeError):
    """需要 agent 的环节在缺少凭证/SDK 时抛出。"""


class BaseAgent:
    """agent 基类。子类通过类属性声明 prompt 与工具，并实现 run()。

    工具能力：
    - `use_irms_tools`：是否挂载 irms in-process MCP 工具（确定性可达性/冲突/校验）。
    - `allowed_tools`：允许调用的工具白名单，可包含：
        * 自定义工具全名，如 "mcp__irms__check_reachability"；
        * 内置 agent 工具名，如 "Read" / "Glob" / "Grep"。
    - `max_turns`：>1 时 agent 可进行「调用工具→读结果→继续」的多轮循环。
    """

    name: str = "agent"
    system_prompt: str = ""
    allowed_tools: list[str] = []
    use_irms_tools: bool = False
    max_turns: int = 1
    permission_mode: str = "bypassPermissions"

    def _ensure_available(self) -> None:
        if not has_credentials():
            raise AgentUnavailableError(
                "未检测到凭证，无法运行 agent 环节。\n"
                "请在 .env 中配置 ANTHROPIC_API_KEY，或 "
                f"{ANTHROPIC_BASE_URL_ENV} + {ANTHROPIC_AUTH_TOKEN_ENV}；\n"
                "或对结构化场景使用 `--from-json` 走全确定性路径。"
            )

    def _build_env(self) -> dict[str, str]:
        """为底层 CLI 准备环境变量，注入网关 base_url / token。"""
        env = dict(os.environ)
        base_url = get_base_url()
        token = get_auth_token()
        if base_url:
            env[ANTHROPIC_BASE_URL_ENV] = base_url
        if token:
            env[ANTHROPIC_AUTH_TOKEN_ENV] = token
        return env

    async def _arun(self, user_prompt: str) -> str:
        from claude_agent_sdk import (
            AssistantMessage,
            ClaudeAgentOptions,
            ResultMessage,
            TextBlock,
            query,
        )

        options_kwargs: dict = {
            "system_prompt": self.system_prompt,
            "env": self._build_env(),
            "allowed_tools": self.allowed_tools,
            "max_turns": self.max_turns,
            "permission_mode": self.permission_mode,
        }
        if self.use_irms_tools:
            from irms.tools.sdk_tools import SERVER_NAME, build_server

            options_kwargs["mcp_servers"] = {SERVER_NAME: build_server()}
        model = get_model()
        if model:
            options_kwargs["model"] = model
        options = ClaudeAgentOptions(**options_kwargs)

        last_text: str = ""
        result_text: str = ""
        async for message in query(prompt=user_prompt, options=options):
            if isinstance(message, AssistantMessage):
                parts = [b.text for b in message.content if isinstance(b, TextBlock)]
                if parts:
                    # 多轮工具调用时，仅保留最后一条助手文本（最终答案），
                    # 避免中间解释文本污染 JSON 提取。
                    last_text = "".join(parts)
            elif isinstance(message, ResultMessage):
                result_text = str(getattr(message, "result", "") or "")
        return last_text or result_text

    def run_text(self, user_prompt: str) -> str:
        """运行一次 agent 调用，返回模型输出的纯文本。"""
        self._ensure_available()
        try:
            import claude_agent_sdk  # noqa: F401
        except ImportError as e:  # pragma: no cover
            raise AgentUnavailableError("claude-agent-sdk 未安装，请先 `uv sync`。") from e

        try:
            return asyncio.run(self._arun(user_prompt))
        except AgentUnavailableError:
            raise
        except Exception as e:
            raise AgentUnavailableError(f"agent 调用失败: {e}") from e

    def run_json(self, user_prompt: str) -> str:
        """运行一次 agent 调用，返回模型输出中的 JSON 文本。"""
        return _extract_json(self.run_text(user_prompt))

    def run(self, *args, **kwargs):  # noqa: D401
        """高层入口，由子类实现。"""
        raise NotImplementedError


def _extract_json(text: str) -> str:
    """从模型输出中提取 JSON：去除 ```json 围栏或截取首个 {...} 块。"""
    s = text.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()
        if s.startswith("json"):
            s = s[4:].strip()
    if not s.startswith("{"):
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            s = s[start : end + 1]
    json.loads(s)  # 校验可解析
    return s

"""全局配置：环境变量与路径。

启动时自动从项目根目录 .env 加载凭证（.env 不纳入 git 管理）。
支持两种鉴权：官方 ANTHROPIC_API_KEY，或自定义网关 ANTHROPIC_BASE_URL + ANTHROPIC_AUTH_TOKEN。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 从项目根目录加载 .env（若存在）。override=False：不覆盖已存在的真实环境变量。
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env", override=False)

ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
ANTHROPIC_AUTH_TOKEN_ENV = "ANTHROPIC_AUTH_TOKEN"
ANTHROPIC_BASE_URL_ENV = "ANTHROPIC_BASE_URL"
MODEL_ENV = "IRMS_MODEL"
DEFAULT_OUTPUT_DIR = "output"


def get_api_key() -> str | None:
    """读取官方 API key；未设置返回 None。"""
    return os.environ.get(ANTHROPIC_API_KEY_ENV) or None


def get_auth_token() -> str | None:
    """读取网关鉴权 token；未设置返回 None。"""
    return os.environ.get(ANTHROPIC_AUTH_TOKEN_ENV) or None


def get_base_url() -> str | None:
    return os.environ.get(ANTHROPIC_BASE_URL_ENV) or None


def get_model() -> str | None:
    return os.environ.get(MODEL_ENV) or None


def has_credentials() -> bool:
    """是否具备可用凭证（官方 key 或网关 token）。"""
    return bool(get_api_key() or get_auth_token())


def resolve_output_dir(out: str | None) -> Path:
    return Path(out or DEFAULT_OUTPUT_DIR)

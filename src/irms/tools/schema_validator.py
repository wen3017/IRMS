"""确定性工具：通用 schema 校验。"""

from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class SchemaValidationError(Exception):
    pass


def validate(model_cls: type[T], data: dict[str, Any]) -> T:
    """将 dict 校验为指定 pydantic 模型，失败抛 SchemaValidationError。"""
    try:
        return model_cls.model_validate(data)
    except ValidationError as e:
        raise SchemaValidationError(str(e)) from e

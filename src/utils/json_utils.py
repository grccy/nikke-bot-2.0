"""
JSON 序列化工具

提供安全的 JSON 序列化/反序列化，失败时返回默认值而非抛异常。
"""

import json
from typing import Any


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """安全序列化为 JSON 字符串。

    Args:
        obj: 待序列化对象
        default: 序列化失败时的默认返回值

    Returns:
        JSON 字符串
    """
    try:
        return json.dumps(obj, ensure_ascii=False)
    except (TypeError, ValueError):
        return default


def safe_json_loads(text: str, default: Any = None) -> Any:
    """安全解析 JSON 字符串。

    Args:
        text: JSON 字符串
        default: 解析失败时的默认返回值

    Returns:
        解析后的 Python 对象
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default

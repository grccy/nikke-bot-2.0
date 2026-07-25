"""
UTC 时间工具

所有时间字段统一使用 ISO 8601 UTC 格式：2026-07-25T00:30:00Z
"""

from datetime import datetime, timezone


def utc_now() -> str:
    """返回当前 ISO 8601 UTC 时间戳字符串。

    Returns:
        格式化时间字符串，如 "2026-07-25T00:30:00Z"
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_now_datetime() -> datetime:
    """返回当前 UTC datetime 对象"""
    return datetime.now(timezone.utc)


def parse_utc(ts: str) -> datetime:
    """解析 ISO 8601 UTC 时间戳字符串为 datetime 对象。

    Args:
        ts: ISO 8601 格式时间戳，支持 "2026-07-25T00:30:00Z" 或 "2026-07-25T00:30:00+00:00"

    Returns:
        datetime 对象
    """
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def format_utc(dt: datetime) -> str:
    """将 datetime 对象格式化为 ISO 8601 UTC 字符串。

    Args:
        dt: datetime 对象

    Returns:
        格式化时间字符串
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

"""
数据校验工具

提供通用字段校验函数，供 Model 层和 Service 层使用。
"""

from typing import Any


def validate_level(level: int) -> bool:
    """验证装备等级在 0-5 范围内"""
    return 0 <= level <= 5


def validate_tier(tier: int) -> bool:
    """验证词条阶级在 1-15 范围内"""
    return 1 <= tier <= 15


def validate_affix_count(count: int) -> bool:
    """验证词条数量在 0-3 范围内"""
    return 0 <= count <= 3


def validate_scope_group(scope: str, group_id: str | None) -> bool:
    """验证 scope 与 group_id 的一致性。

    规则：
    - scope == 'group' 时，group_id 必须非空
    - scope != 'group' 时，group_id 必须为空
    """
    if scope == "group":
        return group_id is not None and group_id != ""
    else:
        return group_id is None


def require_not_empty(value: Any, field_name: str) -> None:
    """断言字段非空，否则抛出 ValueError。

    Args:
        value: 待校验值
        field_name: 字段名（用于错误信息）

    Raises:
        ValueError: 字段为空时
    """
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise ValueError(f"{field_name} 不能为空")


def require_range(
    value: int | float,
    min_val: int | float,
    max_val: int | float,
    field_name: str,
) -> None:
    """断言数值在指定范围内，否则抛出 ValueError。

    Args:
        value: 待校验数值
        min_val: 最小值（含）
        max_val: 最大值（含）
        field_name: 字段名（用于错误信息）

    Raises:
        ValueError: 数值超出范围时
    """
    if not (min_val <= value <= max_val):
        raise ValueError(
            f"{field_name} 必须在 {min_val}-{max_val} 之间，当前值: {value}"
        )

"""
装备词条模型

一条装备最多 3 条词条。
tier 持久化存储，通过 tier_config_version 追踪配置版本。
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from .enums import AffixQuality


class Affix(BaseModel):
    """装备词条。

    约束：
        - value >= 0
        - 同一装备的所有 affix 的 quality 必须一致（由 Equipment 模型校验）
        - sort_order 在同一装备内不重复（由数据库 UNIQUE 约束保证）
        - 1 <= tier <= 15
    """

    name: str = Field(..., description="词条规范名称，如'优越代码伤害加成'")
    value: float = Field(..., ge=0, description="词条数值，如 26.36")
    quality: AffixQuality = Field(..., description="品质：蓝/紫/金")
    tier: int = Field(..., ge=1, le=15, description="词条阶级，由 tier.json 查表计算")
    sort_order: int = Field(default=0, ge=0, le=3, description="排序序号 1/2/3，0=未排序")

    # ---- 数据库分配字段 ----
    id: Optional[int] = Field(default=None, description="数据库主键")
    equipment_id: Optional[int] = Field(default=None, description="所属装备 ID")

    # ---- 溯源字段 ----
    raw_name: Optional[str] = Field(default=None, description="OCR 原始识别文本")
    tier_config_version: Optional[str] = Field(
        default=None, description="计算 tier 时的 tier.json 版本号"
    )

    # ---- 未来扩展 ----
    max_value: Optional[float] = Field(default=None, description="该品质下的理论最大值")
    score_contribution: Optional[float] = Field(default=None, description="对装备总评分的贡献")
    stat_type: Optional[str] = Field(default=None, description="统计类型: percent / flat / crit")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "优越代码伤害加成",
                "value": 26.36,
                "quality": "blue",
                "tier": 13,
                "sort_order": 1,
                "tier_config_version": "2.1.0",
            }
        }
    }

"""数据库行 → 词条模型"""

from typing import Optional
from pydantic import BaseModel, Field


class DbAffix(BaseModel):
    """affixes 表的行对象。"""

    id: int = Field(..., description="词条 ID")
    equipment_id: int = Field(..., description="所属装备 ID")
    name: str = Field(..., description="词条规范名称")
    value: float = Field(..., description="词条数值")
    quality: str = Field(..., description="品质: blue/purple/gold")
    tier: int = Field(..., description="阶级 1-15")
    raw_name: Optional[str] = Field(default=None, description="OCR 原始文本")
    sort_order: int = Field(default=0, description="排序 0-3")
    tier_config_version: Optional[str] = Field(default=None, description="tier.json 版本号")

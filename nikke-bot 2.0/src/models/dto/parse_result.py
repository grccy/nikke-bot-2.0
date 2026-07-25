"""Parser 解析结果 DTO"""

from typing import Optional
from pydantic import BaseModel, Field


class ParseResultAffixDTO(BaseModel):
    """解析结果中的词条条目"""
    name: str = Field(..., description="词条规范名称")
    value: float = Field(..., description="词条数值")
    quality: str = Field(default="blue", description="品质: blue/purple/gold")
    raw_name: Optional[str] = Field(default=None, description="OCR 原始文本")


class ParseResultDTO(BaseModel):
    """Parser 解析结果 —— OCR 文本 → 结构化装备数据"""

    manufacturer: str = Field(default="", description="制造商值: elysion/missilis/tetra/pilgrim/abnormal")
    type: str = Field(default="", description="装备类型: attack/defense/support")
    slot: str = Field(default="", description="装备部位: head/body/arm/leg")
    level: int = Field(default=0, ge=0, le=5, description="装备等级")
    affixes: list[ParseResultAffixDTO] = Field(default_factory=list, max_length=3, description="词条列表")
    raw_text: str = Field(default="", description="OCR 原始文本")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="解析置信度")

"""创建词条 DTO"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CreateAffixDTO(BaseModel):
    """创建词条的输入参数。"""

    name: str = Field(..., min_length=1, description="词条规范名称")
    value: float = Field(..., gt=0, description="词条数值")
    quality: str = Field(..., description="品质: blue/purple/gold")
    raw_name: Optional[str] = Field(default=None, description="OCR 原始文本")

    @field_validator("quality")
    @classmethod
    def quality_must_be_valid(cls, v: str) -> str:
        if v not in ("blue", "purple", "gold"):
            raise ValueError(f"无效品质: {v}, 必须为 blue/purple/gold")
        return v

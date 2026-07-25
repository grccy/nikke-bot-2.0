"""创建装备 DTO"""

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


class CreateEquipmentDTO(BaseModel):
    """创建装备的输入参数。

    由 Handler 层构建，传入 EquipmentService.create_equipment()。
    """

    owner_id: str = Field(..., min_length=1, description="用户 QQ 号")
    template_id: int = Field(..., gt=0, description="装备模板 ID")
    character_id: Optional[int] = Field(default=None, description="所属角色 ID")
    level: int = Field(default=0, ge=0, le=5, description="装备等级")
    affixes: list[CreateAffixDTO] = Field(
        default_factory=list, max_length=3, description="词条列表"
    )
    screenshot_path: Optional[str] = Field(default=None, description="截图路径")

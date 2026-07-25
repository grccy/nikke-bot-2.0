"""更新装备 DTO"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UpdateEquipmentDTO(BaseModel):
    """更新装备的输入参数。

    所有字段均为 Optional，只更新提供的字段。
    """

    character_id: Optional[int] = Field(default=None, description="所属角色 ID")
    level: Optional[int] = Field(default=None, ge=0, le=5, description="装备等级")
    scope: Optional[str] = Field(default=None, description="可见范围")
    group_id: Optional[str] = Field(default=None, description="群号")

    @field_validator("scope")
    @classmethod
    def scope_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("private", "group", "public"):
            raise ValueError(f"无效 scope: {v}")
        return v

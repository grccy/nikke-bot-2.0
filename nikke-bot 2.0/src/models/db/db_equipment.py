"""数据库行 → 装备模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DbEquipment(BaseModel):
    """equipments 表的行对象。"""

    id: int = Field(..., description="装备 ID")
    owner_id: str = Field(..., description="用户 QQ 号")
    template_id: int = Field(..., description="装备模板 ID")
    character_id: Optional[int] = Field(default=None, description="所属角色 ID")
    name: str = Field(..., description="装备规范名称")
    type: str = Field(..., description="装备类型: attack/defense/support")
    slot: str = Field(..., description="装备部位: head/body/arm/leg")
    manufacturer: str = Field(..., description="制造商")
    level: int = Field(default=0, description="装备等级 0-5")
    screenshot_path: Optional[str] = Field(default=None, description="截图路径")
    scope: str = Field(default="private", description="可见范围")
    group_id: Optional[str] = Field(default=None, description="群号")
    is_locked: bool = Field(default=False, description="是否锁定")
    score: Optional[float] = Field(default=None, description="装备评分")
    is_bis: Optional[bool] = Field(default=None, description="是否毕业装备")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")

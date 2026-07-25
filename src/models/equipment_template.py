"""
装备模板模型

游戏中装备类型的静态定义。
由 (manufacturer, type, slot) 三元组唯一确定。
数据从 data/equipment_templates.json 加载，总数约 60 个。
"""

from typing import Optional
from pydantic import BaseModel, Field

from .enums import EquipmentType, EquipmentSlot, Manufacturer


class EquipmentTemplate(BaseModel):
    """装备模板 —— 游戏中存在的装备类型定义。

    约束：
        - (manufacturer, type, slot) 三元组全局唯一
    """

    name: str = Field(..., description="模板规范名称，如'朝圣者火力头盔'")
    type: EquipmentType = Field(..., description="装备类型")
    slot: EquipmentSlot = Field(..., description="装备部位")
    manufacturer: Manufacturer = Field(..., description="制造商")

    id: Optional[int] = Field(default=None, description="数据库主键")
    rarity: Optional[str] = Field(default=None, description="稀有度（预留）")
    icon_name: Optional[str] = Field(default=None, description="图标文件名，渲染用（预留）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "朝圣者火力头盔",
                "type": "attack",
                "slot": "head",
                "manufacturer": "pilgrim",
            }
        }
    }

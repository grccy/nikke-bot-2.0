"""
角色模型

NIKKE 游戏角色。数据从 data/characters.json 加载。
"""

from typing import Optional
from pydantic import BaseModel, Field

from .enums import EquipmentType, EquipmentSlot, Manufacturer


class BISEntry(BaseModel):
    """毕业装备推荐条目。

    描述一个部位的最佳装备配置，用于判断装备是否为毕业装备。
    """

    type: EquipmentType = Field(..., description="推荐装备类型")
    slot: EquipmentSlot = Field(..., description="推荐装备部位")
    manufacturer: Optional[Manufacturer] = Field(default=None, description="推荐制造商（None=不限）")
    target_affixes: list[str] = Field(default_factory=list, description="目标词条名称列表")
    min_tier: int = Field(default=10, ge=1, le=15, description="最低阶级要求")
    priority: int = Field(default=0, description="推荐优先级（越小越优先）")


class Character(BaseModel):
    """NIKKE 游戏角色。

    角色是装备的归属目标。数据从 data/characters.json 导入。
    """

    name: str = Field(..., description="角色规范名称，如'红莲'")
    aliases: list[str] = Field(default_factory=list, description="别名列表，如['红莲·暗影', 'Scarlet']")

    # ---- 游戏属性 ----
    rarity: Optional[str] = Field(default=None, description="稀有度: SSR / SR / R")
    element: Optional[str] = Field(default=None, description="属性: 火 / 水 / 风 / 雷 / 铁甲")
    weapon_type: Optional[str] = Field(default=None, description="武器类型: AR / SR / SMG / SG / RL / MG")
    burst_level: Optional[str] = Field(default=None, description="爆裂阶段: I / II / III")
    manufacturer: Optional[Manufacturer] = Field(default=None, description="所属制造商")

    # ---- 数据库分配 ----
    id: Optional[int] = Field(default=None, description="数据库主键")

    # ---- 未来扩展 ----
    bis_equipment: list[BISEntry] = Field(
        default_factory=list, description="毕业装备推荐列表"
    )
    recommended_affixes: list[str] = Field(
        default_factory=list, description="推荐词条名称列表"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "红莲",
                "aliases": ["红莲·暗影", "Scarlet"],
                "rarity": "SSR",
                "element": "火",
                "weapon_type": "AR",
                "burst_level": "III",
                "manufacturer": "pilgrim",
            }
        }
    }

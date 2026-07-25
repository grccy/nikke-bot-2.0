"""
数据模型层

提供：
- enums: 枚举与基础类型定义
- user: 用户模型
- character: 角色模型（含 BISEntry）
- equipment_template: 装备模板模型
- equipment: 装备实例模型
- affix: 词条模型
- ocr_record: OCR 识别记录模型
"""

from .enums import (
    EquipmentType,
    EquipmentSlot,
    Manufacturer,
    AffixQuality,
    ScopeType,
)
from .affix import Affix
from .equipment import Equipment
from .equipment_template import EquipmentTemplate
from .user import User, UserPreferences
from .character import Character, BISEntry
from .ocr_record import OCRRecord

__all__ = [
    # Enums
    "EquipmentType",
    "EquipmentSlot",
    "Manufacturer",
    "AffixQuality",
    "ScopeType",
    # Models
    "Affix",
    "Equipment",
    "EquipmentTemplate",
    "User",
    "UserPreferences",
    "Character",
    "BISEntry",
    "OCRRecord",
]

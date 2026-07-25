"""
枚举与基础类型定义

系统中使用的所有枚举类型，作为模型的类型约束基础。
"""

from enum import Enum


class EquipmentType(str, Enum):
    """装备类型"""
    ATTACK = "attack"      # 火力型
    DEFENSE = "defense"    # 防御型
    SUPPORT = "support"    # 支援型


class EquipmentSlot(str, Enum):
    """装备部位"""
    HEAD = "head"          # 头部
    BODY = "body"          # 身躯
    ARM = "arm"            # 臂部
    LEG = "leg"            # 腿部


class Manufacturer(str, Enum):
    """制造商"""
    ELYSION = "elysion"        # 极乐净土
    MISSILIS = "missilis"      # 米西利斯
    TETRA = "tetra"            # 泰特拉
    PILGRIM = "pilgrim"        # 朝圣者
    ABNORMAL = "abnormal"      # 反常


class AffixQuality(str, Enum):
    """词条品质"""
    BLUE = "blue"          # 蓝
    PURPLE = "purple"      # 紫
    GOLD = "gold"          # 金


class ScopeType(str, Enum):
    """装备可见范围"""
    PRIVATE = "private"    # 仅自己可见
    GROUP = "group"        # 指定群内可见
    PUBLIC = "public"      # 完全公开

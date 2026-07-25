"""
Parser 层

提供 OCR 文本 → 结构化装备数据的解析能力。

模块:
- normalizer:    文本预处理（全角半角、错字修正）
- equipment_parser: 制造商/类型/部位/等级解析
- affix_parser:  词条名称/数值/品质解析
"""

from src.parser.normalizer import normalize_text, correct_ocr_errors
from src.parser.equipment_parser import EquipmentParser
from src.parser.affix_parser import AffixParser

__all__ = [
    "normalize_text",
    "correct_ocr_errors",
    "EquipmentParser",
    "AffixParser",
]

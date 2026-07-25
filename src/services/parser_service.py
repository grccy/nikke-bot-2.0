"""
OCR 文本解析服务

桥接层 —— 组合 Parser 层各模块，将 OCRResult.text → ParseResultDTO。

Handler 只调用此 Service，不直接调用 parser/ 下的模块。
"""

import logging
from typing import Optional

from src.parser.equipment_parser import EquipmentParser
from src.parser.affix_parser import AffixParser
from src.parser.normalizer import normalize_text, correct_ocr_errors
from src.models.dto.parse_result import ParseResultDTO, ParseResultAffixDTO

logger = logging.getLogger(__name__)


class ParserService:
    """OCR 文本 → 结构化装备数据。

    Handler 只调用 parse() 一个方法。
    """

    def __init__(self):
        self.equip_parser = EquipmentParser()
        self.affix_parser = AffixParser()

    async def parse(self, raw_text: str) -> ParseResultDTO:
        """解析 OCR 原始文本为结构化装备数据。

        Args:
            raw_text: OCR 原始识别文本

        Returns:
            ParseResultDTO
        """
        # 预处理
        text = normalize_text(raw_text)

        # 解析
        manufacturer = self.equip_parser.parse_manufacturer(text) or ""
        equip_type = self.equip_parser.parse_type(text) or ""
        slot = self.equip_parser.parse_slot(text) or ""
        level = self.equip_parser.parse_level(text)

        raw_affixes = self.affix_parser.parse_affixes(text)
        affix_dtos = [
            ParseResultAffixDTO(
                name=a["name"],
                value=a["value"],
                quality=a["quality"],
                raw_name=a.get("raw_name"),
            )
            for a in raw_affixes
        ]

        # 置信度
        found_count = sum([
            bool(manufacturer),
            bool(equip_type),
            bool(slot),
            len(affix_dtos) >= 2,
        ])
        confidence = found_count / 4.0

        logger.info(
            f"解析完成: mfr={manufacturer}, type={equip_type}, "
            f"slot={slot}, level={level}, affixes={len(affix_dtos)}, "
            f"confidence={confidence:.0%}"
        )

        return ParseResultDTO(
            manufacturer=manufacturer,
            type=equip_type,
            slot=slot,
            level=level,
            affixes=affix_dtos,
            raw_text=raw_text,
            confidence=confidence,
        )

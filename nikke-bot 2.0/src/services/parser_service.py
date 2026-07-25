"""
OCR 文本解析服务

负责：
- OCR 原始文本 → 结构化装备数据
- 别名模糊匹配
- 词条提取
"""

import re
import json
import logging
from typing import Optional
from pathlib import Path

from src.config import get_config
from src.utils.json_utils import safe_json_loads

logger = logging.getLogger(__name__)

# 数值正则
PERCENT_PATTERN = re.compile(r"\+?\s*(\d+\.?\d*)\s*%")

# 等级正则
LEVEL_PATTERN = re.compile(r"[Ll][Vv][.]?\s*(\d+)")


class ParserService:
    """OCR 文本解析器"""

    def __init__(self):
        self._alias_config: Optional[dict] = None
        self._affix_names: list[str] = []

    # ================================================================
    # 主解析方法
    # ================================================================

    async def parse(self, raw_text: str) -> dict:
        """解析 OCR 原始文本为结构化装备数据。

        Args:
            raw_text: OCR 原始识别文本

        Returns:
            {
                "name": "",           # 装备规范名称 (暂用 type+slot)
                "type": "",           # attack / defense / support
                "slot": "",           # head / body / arm / leg
                "manufacturer": "",   # elysion / missilis / tetra / pilgrim / abnormal
                "level": 0,           # 装备等级
                "affixes": [          # 词条列表
                    {"name": "", "value": 0.0, "quality": "blue", "raw_name": ""},
                    ...
                ],
                "raw_text": "",       # 原始文本（回传）
                "confidence": 0.0,    # 解析置信度
            }
        """
        self._ensure_config()

        result = {
            "name": "",
            "type": "",
            "slot": "",
            "manufacturer": "",
            "level": 0,
            "affixes": [],
            "raw_text": raw_text,
            "confidence": 0.0,
        }

        lines = raw_text.split("\n")

        # 1. 识别制造商
        mfr = self._match_manufacturer(raw_text)
        if mfr:
            result["manufacturer"] = mfr

        # 2. 识别装备类型
        etype = self._match_equipment_type(raw_text)
        if etype:
            result["type"] = etype

        # 3. 识别装备部位
        slot = self._match_equipment_slot(raw_text)
        if slot:
            result["slot"] = slot

        # 4. 识别等级
        for line in lines:
            m = LEVEL_PATTERN.search(line)
            if m:
                result["level"] = int(m.group(1))
                break

        # 5. 提取词条
        affixes = self._extract_affixes(raw_text)
        result["affixes"] = affixes

        # 6. 计算置信度
        found_count = sum([
            bool(result["manufacturer"]),
            bool(result["type"]),
            bool(result["slot"]),
            len(affixes) >= 2,
        ])
        result["confidence"] = found_count / 4.0

        return result

    # ================================================================
    # 匹配方法
    # ================================================================

    def _match_manufacturer(self, text: str) -> Optional[str]:
        """匹配制造商"""
        if not self._alias_config:
            return None
        mfr_map = self._alias_config.get("manufacturer_names", {})
        return self._fuzzy_match(text, mfr_map)

    def _match_equipment_type(self, text: str) -> Optional[str]:
        """匹配装备类型"""
        if not self._alias_config:
            return None
        type_map = self._alias_config.get("equipment_type_names", {})
        return self._fuzzy_match(text, type_map)

    def _match_equipment_slot(self, text: str) -> Optional[str]:
        """匹配装备部位"""
        if not self._alias_config:
            return None
        slot_map = self._alias_config.get("equipment_slot_names", {})
        return self._fuzzy_match(text, slot_map)

    def _fuzzy_match(self, text: str, mapping: dict) -> Optional[str]:
        """在文本中模糊匹配别名映射。

        Args:
            text: 要搜索的文本
            mapping: {规范名: [别名列表]}

        Returns:
            匹配到的规范名，或 None
        """
        text_lower = text.lower()
        for standard_name, aliases in mapping.items():
            for alias in aliases:
                if alias.lower() in text_lower:
                    return standard_name
        return None

    def _extract_affixes(self, text: str) -> list[dict]:
        """从文本中提取词条信息。

        策略：
        1. 扫描每一行，匹配词条名称
        2. 在同一行或下一行找百分比数值
        3. 根据数值范围推测品质

        Args:
            text: OCR 原始文本

        Returns:
            词条列表
        """
        if not self._alias_config:
            return []

        affix_map = self._alias_config.get("affix_names", {})
        lines = text.split("\n")
        affixes: list[dict] = []
        seen_names: set[str] = set()

        for i, line in enumerate(lines):
            # 匹配词条名称
            affix_name = self._fuzzy_match(line, affix_map)
            if not affix_name or affix_name in seen_names:
                continue

            # 找数值
            value = None
            m = PERCENT_PATTERN.search(line)
            if m:
                value = float(m.group(1))
            elif i + 1 < len(lines):
                m = PERCENT_PATTERN.search(lines[i + 1])
                if m:
                    value = float(m.group(1))

            if value is not None and 0.5 < value < 50:
                # 根据数值推测品质
                quality = self._guess_quality(value)

                seen_names.add(affix_name)
                affixes.append({
                    "name": affix_name,
                    "value": value,
                    "quality": quality,
                    "raw_name": line.strip(),
                })

        return affixes[:3]

    @staticmethod
    def _guess_quality(value: float) -> str:
        """根据数值范围推测词条品质"""
        if value >= 10:
            return "gold"
        elif value >= 7:
            return "purple"
        else:
            return "blue"

    # ================================================================
    # 配置加载
    # ================================================================

    def _ensure_config(self):
        """确保配置已加载"""
        if self._alias_config is not None:
            return

        try:
            alias_path = get_config().data_dir / "alias.json"
            with open(alias_path, "r", encoding="utf-8") as f:
                self._alias_config = json.load(f)
        except Exception as e:
            logger.warning(f"alias.json 加载失败: {e}")
            self._alias_config = {}

        try:
            names_path = get_config().data_dir / "affix_names.json"
            with open(names_path, "r", encoding="utf-8") as f:
                self._affix_names = json.load(f)
        except Exception:
            self._affix_names = []

"""
词条解析器

从 OCR 文本中提取词条属性名、数值、品质。
"""

import re
import json
import logging
from pathlib import Path
from typing import Optional

from src.config import get_config
from src.parser.normalizer import normalize_text, correct_ocr_errors

logger = logging.getLogger(__name__)

# 百分比数值: +15.6% / +11% / 26.36% / 15.6
_PERCENT_PATTERN = re.compile(r"\+?\s*(\d+\.?\d*)\s*%?")

# 品质关键词
_QUALITY_KEYWORDS = {
    "gold": ["金", "🟡", "金色", "黃", "金"],
    "purple": ["紫", "🟣", "紫色", "紫⾊"],
    "blue": ["蓝", "🔵", "蓝色", "藍", "藍色", "蓝⾊"],
}

# 别名配置缓存
_alias_config: Optional[dict] = None
_affix_map: Optional[dict] = None


class AffixParser:
    """词条解析器"""

    def __init__(self):
        self._ensure_config()

    # ---- 解析 ----

    def parse_affixes(self, text: str) -> list[dict]:
        """从 OCR 文本中提取全部词条。

        策略:
        1. 逐行扫描
        2. 匹配词条名称（通过 alias.json 中的 affix_names）
        3. 在同一行或下一行找百分比数值
        4. 根据数值范围推测品质

        Args:
            text: OCR 原始文本

        Returns:
            词条列表 [{"name": "", "value": 0.0, "quality": "blue", "raw_name": ""}, ...]
            最多 3 条
        """
        if not _affix_map:
            return []

        text = correct_ocr_errors(normalize_text(text))
        lines = text.split("\n")

        affixes: list[dict] = []
        seen_names: set[str] = set()

        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue

            # 匹配词条名称
            affix_name = self._fuzzy_match_affix(line_clean)
            if not affix_name or affix_name in seen_names:
                continue

            # 找数值
            value = None
            m = _PERCENT_PATTERN.search(line_clean)
            if m:
                value = float(m.group(1))

            # 当前行没有数值，尝试下一行
            if value is None and i + 1 < len(lines):
                m = _PERCENT_PATTERN.search(lines[i + 1].strip())
                if m:
                    value = float(m.group(1))

            if value is None or not (0.5 < value < 50):
                continue

            # 推测品质
            quality = self._detect_quality(line_clean, value)

            seen_names.add(affix_name)
            affixes.append({
                "name": affix_name,
                "value": value,
                "quality": quality,
                "raw_name": line_clean,
            })

        return affixes[:3]

    def parse_quality(self, text: str) -> Optional[str]:
        """从文本中检测词条品质关键词。

        Returns:
            gold / purple / blue 或 None
        """
        text = correct_ocr_errors(normalize_text(text))
        text_lower = text.lower()

        for quality, keywords in _QUALITY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower or kw in text:
                    return quality

        return None

    # ---- 内部 ----

    def _fuzzy_match_affix(self, text: str) -> Optional[str]:
        """在文本中匹配词条名称"""
        if not _affix_map:
            return None

        text_lower = text.lower()
        for standard_name, aliases in _affix_map.items():
            for alias in aliases:
                if alias.lower() in text_lower:
                    return standard_name
        return None

    @staticmethod
    def _detect_quality(text: str, value: float) -> str:
        """根据文本关键词 + 数值范围推测品质。

        优先文本关键词，其次数值范围。
        """
        # 文本关键词检测
        for quality, keywords in _QUALITY_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return quality

        # 数值范围推测
        if value >= 10:
            return "gold"
        elif value >= 7:
            return "purple"
        else:
            return "blue"

    @staticmethod
    def _ensure_config():
        """加载 alias.json"""
        global _alias_config, _affix_map
        if _alias_config is not None:
            return

        try:
            alias_path = get_config().data_dir / "alias.json"
            with open(alias_path, "r", encoding="utf-8") as f:
                _alias_config = json.load(f)
            _affix_map = _alias_config.get("affix_names", {})
        except Exception as e:
            logger.warning(f"alias.json 加载失败: {e}")
            _alias_config = {}
            _affix_map = {}

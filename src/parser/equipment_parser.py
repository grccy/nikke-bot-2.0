"""
装备属性解析器

从 OCR 文本中提取：
- 制造商
- 装备类型
- 装备部位
- 等级
"""

import re
import json
import logging
from pathlib import Path
from typing import Optional

from src.config import get_config
from src.parser.normalizer import normalize_text, correct_ocr_errors

logger = logging.getLogger(__name__)

# 等级正则: Lv5, Lv. 5, LV5, 等级5, Lv 5
_LEVEL_PATTERN = re.compile(r"[LlLl][Vv]\.?\s*(\d+)|等级\s*(\d+)")

# 别名配置缓存
_alias_config: Optional[dict] = None


class EquipmentParser:
    """装备属性解析器"""

    def __init__(self):
        self._ensure_alias_config()

    # ---- 解析 ----

    def parse_manufacturer(self, text: str) -> Optional[str]:
        """解析制造商。

        Returns:
            制造商枚举值: elysion / missilis / tetra / pilgrim / abnormal
            或 None
        """
        text = correct_ocr_errors(normalize_text(text))
        return self._fuzzy_match(text, "manufacturer_names")

    def parse_type(self, text: str) -> Optional[str]:
        """解析装备类型。

        Returns:
            attack / defense / support 或 None
        """
        text = correct_ocr_errors(normalize_text(text))
        return self._fuzzy_match(text, "equipment_type_names")

    def parse_slot(self, text: str) -> Optional[str]:
        """解析装备部位。

        Returns:
            head / body / arm / leg 或 None
        """
        text = correct_ocr_errors(normalize_text(text))
        return self._fuzzy_match(text, "equipment_slot_names")

    def parse_level(self, text: str) -> int:
        """解析装备等级。

        从文本中查找 LvX 或 等级X 模式。

        Returns:
            等级数值 0-5
        """
        for line in text.split("\n"):
            m = _LEVEL_PATTERN.search(line)
            if m:
                value = m.group(1) or m.group(2)
                if value:
                    level = int(value)
                    return max(0, min(5, level))
        return 0  # 默认

    # ---- 内部 ----

    def _fuzzy_match(self, text: str, category: str) -> Optional[str]:
        """在文本中模糊匹配别名。

        Args:
            text: OCR 文本
            category: alias.json 中的分类 key

        Returns:
            规范值（enum value）或 None
        """
        if not _alias_config:
            return None

        mapping = _alias_config.get(category, {})
        text_lower = text.lower()

        for standard_name, aliases in mapping.items():
            for alias in aliases:
                if alias.lower() in text_lower:
                    return standard_name

        return None

    @staticmethod
    def _ensure_alias_config():
        """加载 alias.json"""
        global _alias_config
        if _alias_config is not None:
            return

        try:
            alias_path = get_config().data_dir / "alias.json"
            with open(alias_path, "r", encoding="utf-8") as f:
                _alias_config = json.load(f)
        except Exception as e:
            logger.warning(f"alias.json 加载失败: {e}")
            _alias_config = {}

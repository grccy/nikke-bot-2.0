"""
测试 AffixParser —— 词条解析
"""

import pytest
from unittest.mock import patch, MagicMock
from src.parser.affix_parser import AffixParser


# ---- Mock alias.json 内容 ----
MOCK_ALIAS = {
    "affix_names": {
        "攻击力": ["攻击力", "攻击", "攻击力增加", "ATK"],
        "防御力": ["防御力", "防御", "防御力增加", "DEF"],
        "暴击伤害": ["暴击伤害", "暴伤", "暴击伤"],
        "蓄力速度": ["蓄力速度", "蓄速", "蓄力"],
        "最大装弹数": ["最大装弹数", "装弹数", "弹夹"],
    },
    "manufacturer_names": {},
    "equipment_type_names": {},
    "equipment_slot_names": {},
}


@pytest.fixture(autouse=True)
def mock_alias_config(monkeypatch):
    """注入 mock alias.json 避免文件依赖"""
    import json
    from pathlib import Path
    import tempfile

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(MOCK_ALIAS, tmp)
    tmp.close()

    # Mock get_config().data_dir 指向临时目录
    from src.config import AppConfig, DatabaseConfig
    test_cfg = AppConfig(database=DatabaseConfig(path=Path(tmp.name).parent / "test.db"))
    test_cfg.data_dir = Path(tmp.name).parent
    monkeypatch.setattr("src.config.get_config", lambda: test_cfg)

    # 清除 parser 缓存
    import src.parser.equipment_parser as ep
    import src.parser.affix_parser as ap
    ep._alias_config = None
    ap._alias_config = None
    ap._affix_map = None

    yield

    # 清理
    import os
    os.unlink(tmp.name)
    ep._alias_config = None
    ap._alias_config = None
    ap._affix_map = None


class TestAffixParserBasic:
    """基础词条解析"""

    def test_parse_single_affix(self):
        """解析单条词条"""
        parser = AffixParser()
        text = "攻击力 +15.6%"
        result = parser.parse_affixes(text)
        assert len(result) == 1
        assert result[0]["name"] == "攻击力"
        assert result[0]["value"] == 15.6

    def test_parse_multiple_affixes(self):
        """解析多条词条"""
        parser = AffixParser()
        text = "攻击力 +11.5%\n暴击伤害 +24.3%\n蓄力速度 +8.1%"
        result = parser.parse_affixes(text)
        assert len(result) == 3
        assert result[0]["name"] == "攻击力"
        assert result[1]["name"] == "暴击伤害"
        assert result[2]["name"] == "蓄力速度"

    def test_parse_with_alias(self):
        """通过别名匹配词条"""
        parser = AffixParser()
        # "攻击"是"攻击力"的别名
        text = "攻击 +11.5%"
        result = parser.parse_affixes(text)
        assert len(result) == 1
        assert result[0]["name"] == "攻击力"

    def test_parse_english_alias(self):
        """英文别名匹配"""
        parser = AffixParser()
        text = "ATK +15.6%"
        result = parser.parse_affixes(text)
        assert len(result) == 1
        assert result[0]["name"] == "攻击力"

    def test_deduplicate_same_affix(self):
        """重复词条应去重"""
        parser = AffixParser()
        text = "攻击力 +11%\n攻击力 +15%"
        result = parser.parse_affixes(text)
        assert len(result) == 1  # 只取第一个

    def test_max_three_affixes(self):
        """最多返回 3 条"""
        parser = AffixParser()
        text = "攻击力 +11%\n防御力 +12%\n暴击伤害 +13%\n蓄力速度 +14%"
        result = parser.parse_affixes(text)
        assert len(result) == 3

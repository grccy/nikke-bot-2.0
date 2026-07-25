"""
测试 Affix 词条模型
"""

import pytest
from src.models.enums import AffixQuality
from src.models.affix import Affix


class TestAffixModel:
    """词条模型单元测试"""

    def test_create_valid_affix(self):
        """创建有效词条"""
        affix = Affix(
            name="攻击力",
            value=15.6,
            quality=AffixQuality.GOLD,
            tier=9,
            sort_order=1,
        )
        assert affix.name == "攻击力"
        assert affix.value == 15.6
        assert affix.quality == AffixQuality.GOLD
        assert affix.tier == 9

    def test_negative_value_raises_error(self):
        """负数数值应抛出验证错误"""
        with pytest.raises(Exception):
            Affix(name="攻击力", value=-1.0, quality=AffixQuality.BLUE, tier=1)

    def test_invalid_sort_order_raises_error(self):
        """sort_order 超出 0-3 应抛出验证错误"""
        with pytest.raises(Exception):
            Affix(name="攻击力", value=10.0, quality=AffixQuality.BLUE, tier=1, sort_order=5)

    def test_tier_out_of_range_raises_error(self):
        """tier 超出 1-15 应抛出验证错误"""
        with pytest.raises(Exception):
            Affix(name="攻击力", value=10.0, quality=AffixQuality.BLUE, tier=0)

    def test_default_values(self):
        """测试默认值"""
        affix = Affix(name="暴击伤害", value=20.0, quality=AffixQuality.PURPLE, tier=10)
        assert affix.sort_order == 0
        assert affix.id is None
        assert affix.equipment_id is None
        assert affix.raw_name is None

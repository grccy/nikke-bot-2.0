"""
测试 EquipmentParser —— 装备属性解析
"""

import pytest
from src.parser.equipment_parser import EquipmentParser


class TestEquipmentParser:
    """装备属性解析"""

    def test_parse_manufacturer_pilgrim(self):
        """解析朝圣者"""
        parser = EquipmentParser()
        result = parser.parse_manufacturer("朝圣者 火力型 头部")
        assert result == "pilgrim"

    def test_parse_manufacturer_missilis(self):
        """解析米西利斯"""
        parser = EquipmentParser()
        result = parser.parse_manufacturer("米西利斯防御型")
        assert result == "missilis"

    def test_parse_manufacturer_english(self):
        """英文制造商"""
        parser = EquipmentParser()
        result = parser.parse_manufacturer("PILGRIM Attack Head")
        assert result == "pilgrim"

    def test_parse_manufacturer_abnormal(self):
        """解析反常"""
        parser = EquipmentParser()
        result = parser.parse_manufacturer("反常火力型")
        assert result == "abnormal"

    def test_parse_manufacturer_not_found(self):
        """无匹配制造商返回 None"""
        parser = EquipmentParser()
        result = parser.parse_manufacturer("未知文字")
        assert result is None

    def test_parse_type_attack(self):
        """解析火力型"""
        parser = EquipmentParser()
        assert parser.parse_type("火力型头盔") == "attack"
        assert parser.parse_type("攻击型头盔") == "attack"  # alias

    def test_parse_type_defense(self):
        """解析防御型"""
        parser = EquipmentParser()
        assert parser.parse_type("防御型防弹衣") == "defense"

    def test_parse_type_support(self):
        """解析支援型"""
        parser = EquipmentParser()
        assert parser.parse_type("支援型臂章") == "support"
        assert parser.parse_type("辅助臂章") == "support"  # alias

    def test_parse_slot_head(self):
        """解析头部"""
        parser = EquipmentParser()
        assert parser.parse_slot("头盔") == "head"
        assert parser.parse_slot("头部装备") == "head"

    def test_parse_slot_all(self):
        """解析全部部位"""
        parser = EquipmentParser()
        assert parser.parse_slot("防弹衣") == "body"
        assert parser.parse_slot("躯干") == "body"
        assert parser.parse_slot("臂章") == "arm"
        assert parser.parse_slot("手臂") == "arm"
        assert parser.parse_slot("战靴") == "leg"
        assert parser.parse_slot("腿") == "leg"

    def test_parse_level_lv5(self):
        """解析 Lv5"""
        parser = EquipmentParser()
        assert parser.parse_level("朝圣者 Lv5 头盔") == 5

    def test_parse_level_lv_dot(self):
        """解析 Lv. 3"""
        parser = EquipmentParser()
        assert parser.parse_level("Lv. 3") == 3

    def test_parse_level_cn(self):
        """解析中文"等级"标记"""
        parser = EquipmentParser()
        assert parser.parse_level("等级5") == 5

    def test_parse_level_not_found(self):
        """无等级标记返回 0"""
        parser = EquipmentParser()
        assert parser.parse_level("朝圣者火力头盔") == 0

    def test_parse_level_out_of_range_clamped(self):
        """超出 0-5 的范围应被钳制"""
        parser = EquipmentParser()
        # 如果 OCR 误识别 Lv 7 → clamp to 5
        result = parser.parse_level("Lv 9")
        assert result == 5

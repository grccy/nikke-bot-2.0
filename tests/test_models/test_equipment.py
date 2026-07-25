"""
测试 Equipment 装备模型
"""

import pytest
from src.models.enums import (
    EquipmentType, EquipmentSlot, Manufacturer, AffixQuality, ScopeType
)
from src.models.equipment import Equipment
from src.models.affix import Affix


class TestEquipmentModel:
    """装备模型单元测试"""

    def test_create_valid_equipment(self):
        """创建有效装备"""
        equip = Equipment(
            owner_id="123456789",
            template_id=1,
            name="朝圣者火力头盔",
            type=EquipmentType.ATTACK,
            slot=EquipmentSlot.HEAD,
            manufacturer=Manufacturer.PILGRIM,
            level=3,
        )
        assert equip.owner_id == "123456789"
        assert equip.level == 3
        assert equip.affixes == []
        assert equip.scope == ScopeType.PRIVATE
        assert equip.is_locked is False

    def test_level_out_of_range_raises_error(self):
        """等级超出 0-5 应报错"""
        with pytest.raises(Exception):
            Equipment(
                owner_id="123",
                template_id=1,
                name="测试",
                type=EquipmentType.ATTACK,
                slot=EquipmentSlot.HEAD,
                manufacturer=Manufacturer.PILGRIM,
                level=6,
            )

    def test_scope_group_requires_group_id(self):
        """scope=group 时 group_id 必填"""
        with pytest.raises(Exception):
            Equipment(
                owner_id="123",
                template_id=1,
                name="测试",
                type=EquipmentType.ATTACK,
                slot=EquipmentSlot.HEAD,
                manufacturer=Manufacturer.PILGRIM,
                scope=ScopeType.GROUP,
                group_id=None,
            )

    def test_affixes_quality_consistency(self):
        """词条品质必须一致"""
        affix1 = Affix(name="攻击力", value=10.0, quality=AffixQuality.BLUE, tier=5)
        affix2 = Affix(name="暴击伤害", value=15.0, quality=AffixQuality.GOLD, tier=8)

        with pytest.raises(Exception):
            Equipment(
                owner_id="123",
                template_id=1,
                name="测试",
                type=EquipmentType.ATTACK,
                slot=EquipmentSlot.HEAD,
                manufacturer=Manufacturer.PILGRIM,
                affixes=[affix1, affix2],
            )

    def test_max_three_affixes(self):
        """词条数量不能超过 3"""
        affixes = [
            Affix(name=f"词条{i}", value=10.0, quality=AffixQuality.BLUE, tier=5)
            for i in range(4)
        ]
        with pytest.raises(Exception):
            Equipment(
                owner_id="123",
                template_id=1,
                name="测试",
                type=EquipmentType.ATTACK,
                slot=EquipmentSlot.HEAD,
                manufacturer=Manufacturer.PILGRIM,
                affixes=affixes,
            )

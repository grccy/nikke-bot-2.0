"""
测试 AffixRepository
"""

import pytest
from src.models.affix import Affix
from src.models.affix import Affix, AffixQuality


@pytest.fixture
async def _seed_equipment(equipment_repo, template_repo, user_repo):
    """创建测试装备"""
    from src.models.equipment import Equipment
    from src.models.equipment_template import EquipmentTemplate
    from src.models.enums import EquipmentType, EquipmentSlot, Manufacturer
    from src.models.user import User

    await user_repo.upsert(User(qq_id="affix_test_user"))
    tmpl = await template_repo.upsert(EquipmentTemplate(
        name="泰特拉防御头盔",
        type=EquipmentType.DEFENSE,
        slot=EquipmentSlot.HEAD,
        manufacturer=Manufacturer.TETRA,
    ))
    eq = await equipment_repo.insert(Equipment(
        owner_id="affix_test_user",
        template_id=tmpl.id,  # type: ignore
        name=tmpl.name, type=tmpl.type, slot=tmpl.slot,
        manufacturer=tmpl.manufacturer, level=0,
    ))
    return eq


@pytest.mark.asyncio
async def test_insert_affix(affix_repo, _seed_equipment):
    """插入词条"""
    eq = _seed_equipment
    affix = Affix(
        equipment_id=eq.id,  # type: ignore
        name="攻击力",
        value=15.6,
        quality=AffixQuality.GOLD,
        tier=9,
        sort_order=1,
    )
    saved = await affix_repo.insert(affix)
    assert saved.id is not None
    assert saved.tier == 9


@pytest.mark.asyncio
async def test_get_by_equipment(affix_repo, _seed_equipment):
    """按装备查询词条"""
    eq = _seed_equipment
    await affix_repo.insert(Affix(
        equipment_id=eq.id,  # type: ignore
        name="攻击力", value=10.0, quality=AffixQuality.BLUE, tier=5, sort_order=1,
    ))
    await affix_repo.insert(Affix(
        equipment_id=eq.id,  # type: ignore
        name="暴击伤害", value=20.0, quality=AffixQuality.PURPLE, tier=10, sort_order=2,
    ))

    affixes = await affix_repo.get_by_equipment(eq.id)  # type: ignore
    assert len(affixes) == 2


@pytest.mark.asyncio
async def test_insert_batch(affix_repo, _seed_equipment):
    """批量插入"""
    eq = _seed_equipment
    affixes = [
        Affix(equipment_id=eq.id, name=f"词条{i}", value=10.0 + i,  # type: ignore
              quality=AffixQuality.BLUE, tier=5, sort_order=i)
        for i in range(1, 4)
    ]
    saved = await affix_repo.insert_batch(affixes)
    assert len(saved) == 3

    loaded = await affix_repo.get_by_equipment(eq.id)  # type: ignore
    assert len(loaded) == 3

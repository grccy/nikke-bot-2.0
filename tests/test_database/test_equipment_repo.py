"""
测试 EquipmentRepository
"""

import pytest
from src.models.equipment import Equipment
from src.models.enums import EquipmentType, EquipmentSlot, Manufacturer, ScopeType
from src.utils.time_utils import utc_now


@pytest.fixture
async def _seed_template(template_repo):
    """插入测试模板"""
    from src.models.equipment_template import EquipmentTemplate
    tmpl = EquipmentTemplate(
        name="朝圣者火力头盔",
        type=EquipmentType.ATTACK,
        slot=EquipmentSlot.HEAD,
        manufacturer=Manufacturer.PILGRIM,
    )
    return await template_repo.upsert(tmpl)


@pytest.fixture
async def _seed_user(user_repo):
    """插入测试用户"""
    from src.models.user import User
    return await user_repo.upsert(User(qq_id="test_user_123", nickname="测试"))


@pytest.mark.asyncio
async def test_insert_equipment(equipment_repo, _seed_template, _seed_user):
    """插入装备"""
    template = _seed_template
    eq = Equipment(
        owner_id="test_user_123",
        template_id=template.id,  # type: ignore
        name=template.name,
        type=template.type,
        slot=template.slot,
        manufacturer=template.manufacturer,
        level=3,
    )
    saved = await equipment_repo.insert(eq)
    assert saved.id is not None
    assert saved.level == 3
    assert saved.created_at is not None


@pytest.mark.asyncio
async def test_get_by_id(equipment_repo, _seed_template, _seed_user):
    """按 ID 查询"""
    template = _seed_template
    eq = Equipment(
        owner_id="test_user_123",
        template_id=template.id,  # type: ignore
        name=template.name,
        type=template.type,
        slot=template.slot,
        manufacturer=template.manufacturer,
        level=0,
    )
    saved = await equipment_repo.insert(eq)
    fetched = await equipment_repo.get_by_id(saved.id)  # type: ignore
    assert fetched is not None
    assert fetched.name == "朝圣者火力头盔"


@pytest.mark.asyncio
async def test_get_by_owner(equipment_repo, _seed_template, _seed_user):
    """按用户查询"""
    template = _seed_template
    await equipment_repo.insert(Equipment(
        owner_id="test_user_123", template_id=template.id,  # type: ignore
        name=template.name, type=template.type, slot=template.slot,
        manufacturer=template.manufacturer, level=1,
    ))
    await equipment_repo.insert(Equipment(
        owner_id="test_user_123", template_id=template.id,  # type: ignore
        name=template.name, type=template.type, slot=template.slot,
        manufacturer=template.manufacturer, level=2,
    ))

    results = await equipment_repo.get_by_owner("test_user_123")
    assert len(results) == 2


@pytest.mark.asyncio
async def test_delete_equipment(equipment_repo, _seed_template, _seed_user):
    """删除装备"""
    template = _seed_template
    eq = await equipment_repo.insert(Equipment(
        owner_id="test_user_123", template_id=template.id,  # type: ignore
        name=template.name, type=template.type, slot=template.slot,
        manufacturer=template.manufacturer, level=0,
    ))
    deleted = await equipment_repo.delete(eq.id)  # type: ignore
    assert deleted is True

    fetched = await equipment_repo.get_by_id(eq.id)  # type: ignore
    assert fetched is None

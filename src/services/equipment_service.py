"""
装备业务服务

核心业务层，负责装备全生命周期管理。
Handler → EquipmentService → Repository → Database

使用 constructor injection 接收 Repository。
"""

import json
import logging
from typing import Optional

import aiosqlite

from src.database.repositories.equipment_repo import EquipmentRepository
from src.database.repositories.affix_repo import AffixRepository
from src.database.repositories.template_repo import TemplateRepository
from src.models.equipment import Equipment
from src.models.affix import Affix
from src.models.enums import (
    EquipmentType,
    EquipmentSlot,
    Manufacturer,
    ScopeType,
)
from src.models.dto.create_equipment import CreateEquipmentDTO, CreateAffixDTO
from src.services.score_service import calculate_tier

logger = logging.getLogger(__name__)


class EquipmentService:
    """装备核心业务服务。

    使用方式:
        service = EquipmentService(
            equip_repo=EquipmentRepository(db),
            affix_repo=AffixRepository(db),
            template_repo=TemplateRepository(db),
        )
        equipment = await service.create_equipment(dto)
    """

    def __init__(
        self,
        equip_repo: EquipmentRepository,
        affix_repo: AffixRepository,
        template_repo: TemplateRepository,
    ):
        self.equip_repo = equip_repo
        self.affix_repo = affix_repo
        self.template_repo = template_repo

    # ================================================================
    # 创建与保存
    # ================================================================

    async def create_equipment(self, dto: CreateEquipmentDTO) -> Equipment:
        """创建一件新装备（含词条）。

        流程：
        1. 验证模板存在
        2. 从模板填充冗余字段
        3. 插入装备记录
        4. 计算词条 tier
        5. 批量插入词条
        6. 返回完整装备对象
        """
        # 1. 验证模板
        template = await self.template_repo.get_by_id(dto.template_id)
        if template is None:
            raise ValueError(f"装备模板不存在: template_id={dto.template_id}")

        # 2. 构建装备对象
        equipment = Equipment(
            owner_id=dto.owner_id,
            template_id=dto.template_id,
            character_id=dto.character_id,
            name=template.name,
            type=template.type,
            slot=template.slot,
            manufacturer=template.manufacturer,
            level=dto.level,
            screenshot_path=dto.screenshot_path,
        )

        # 3. 插入装备
        equipment = await self.equip_repo.insert(equipment)

        # 4. 构建词条对象并计算 tier
        tier_version = _load_tier_version()

        affixes: list[Affix] = []
        for i, ad in enumerate(dto.affixes[:3], start=1):
            tier = calculate_tier(ad.quality, ad.value)
            affix = Affix(
                equipment_id=equipment.id,
                name=ad.name,
                value=ad.value,
                quality=ad.quality,  # type: ignore (str passed where enum expected — Pydantic coerces)
                tier=tier,
                sort_order=i,
                raw_name=ad.raw_name,
                tier_config_version=tier_version,
            )
            affixes.append(affix)

        # 5. 批量插入词条
        affixes = await self.affix_repo.insert_batch(affixes)

        equipment.affixes = affixes
        logger.info(f"用户 {dto.owner_id} 创建装备 #{equipment.id}: {equipment.name}")

        return equipment

    # ================================================================
    # 查询
    # ================================================================

    async def get_equipment_detail(self, equipment_id: int) -> Optional[Equipment]:
        """查询装备详情（含词条）。"""
        equipment = await self.equip_repo.get_by_id(equipment_id)
        if equipment is None:
            return None

        equipment.affixes = await self.affix_repo.get_by_equipment(equipment_id)
        return equipment

    async def get_user_equipments(
        self,
        owner_id: str,
        character_id: Optional[int] = None,
        type_: Optional[EquipmentType] = None,
        slot: Optional[EquipmentSlot] = None,
        manufacturer: Optional[Manufacturer] = None,
        page: int = 1,
        page_size: int = 5,
    ) -> tuple[list[Equipment], int]:
        """查询用户装备列表（分页，含词条）。"""
        offset = (page - 1) * page_size

        total = await self.equip_repo.count_by_owner(owner_id, character_id, type_)
        equipments = await self.equip_repo.get_by_owner(
            owner_id, character_id, type_, slot, manufacturer,
            limit=page_size, offset=offset,
        )

        for eq in equipments:
            eq.affixes = await self.affix_repo.get_by_equipment(eq.id)  # type: ignore

        return equipments, total

    async def search_by_affix(
        self, affix_name: str, owner_id: Optional[str] = None, limit: int = 20
    ) -> list[Equipment]:
        """按词条名称搜索装备。"""
        equipments = await self.equip_repo.search_by_affix_name(affix_name, owner_id, limit)
        for eq in equipments:
            eq.affixes = await self.affix_repo.get_by_equipment(eq.id)  # type: ignore
        return equipments

    async def get_top_by_score(self, limit: int = 10) -> list[Equipment]:
        """查询评分最高的装备（排行榜）。"""
        equipments = await self.equip_repo.get_top_by_score(limit)
        for eq in equipments:
            eq.affixes = await self.affix_repo.get_by_equipment(eq.id)  # type: ignore
        return equipments

    async def get_group_shared(
        self, group_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Equipment], int]:
        """查询群共享装备。"""
        offset = (page - 1) * page_size
        equipments = await self.equip_repo.get_group_shared(group_id, limit=page_size, offset=offset)
        for eq in equipments:
            eq.affixes = await self.affix_repo.get_by_equipment(eq.id)  # type: ignore
        return equipments, len(equipments)

    # ================================================================
    # 更新与删除
    # ================================================================

    async def update_equipment(
        self, equipment_id: int, owner_id: str, **kwargs
    ) -> Equipment:
        """更新装备属性。"""
        equipment = await self.equip_repo.get_by_id(equipment_id)
        if equipment is None:
            raise ValueError(f"装备不存在: #{equipment_id}")
        if equipment.owner_id != owner_id:
            raise ValueError("无权操作他人装备")
        if equipment.is_locked:
            raise RuntimeError(f"装备 #{equipment_id} 已锁定，请先解锁后再修改")

        for key, value in kwargs.items():
            if hasattr(equipment, key):
                setattr(equipment, key, value)

        equipment = await self.equip_repo.update(equipment)
        equipment.affixes = await self.affix_repo.get_by_equipment(equipment.id)  # type: ignore
        logger.info(f"用户 {owner_id} 更新装备 #{equipment_id}")
        return equipment

    async def delete_equipment(self, equipment_id: int, owner_id: str) -> bool:
        """删除装备（级联删除词条）。"""
        equipment = await self.equip_repo.get_by_id(equipment_id)
        if equipment is None:
            return False
        if equipment.owner_id != owner_id:
            raise ValueError("无权删除他人装备")
        if equipment.is_locked:
            raise RuntimeError(f"装备 #{equipment_id} 已锁定，请先解锁后再删除")

        result = await self.equip_repo.delete(equipment_id)
        if result:
            logger.info(f"用户 {owner_id} 删除装备 #{equipment_id}")
        return result

    async def toggle_lock(self, equipment_id: int, owner_id: str) -> Equipment:
        """切换装备锁定状态。"""
        equipment = await self.equip_repo.get_by_id(equipment_id)
        if equipment is None:
            raise ValueError(f"装备不存在: #{equipment_id}")
        if equipment.owner_id != owner_id:
            raise ValueError("无权操作他人装备")

        equipment.is_locked = not equipment.is_locked
        equipment = await self.equip_repo.update(equipment)
        equipment.affixes = await self.affix_repo.get_by_equipment(equipment.id)  # type: ignore
        return equipment

    async def update_affixes(
        self, equipment_id: int, owner_id: str, affixes_data: list[dict]
    ) -> Equipment:
        """替换装备的全部词条。"""
        equipment = await self.equip_repo.get_by_id(equipment_id)
        if equipment is None:
            raise ValueError(f"装备不存在: #{equipment_id}")
        if equipment.owner_id != owner_id:
            raise ValueError("无权操作他人装备")

        tier_version = _load_tier_version()

        new_affixes: list[Affix] = []
        for i, data in enumerate(affixes_data[:3], start=1):
            affix = Affix(
                equipment_id=equipment_id,
                name=data["name"],
                value=data["value"],
                quality=data["quality"],  # type: ignore
                tier=calculate_tier(data["quality"], data["value"]),
                sort_order=i,
                raw_name=data.get("raw_name"),
                tier_config_version=tier_version,
            )
            new_affixes.append(affix)

        new_affixes = await self.affix_repo.replace_affixes(equipment_id, new_affixes)
        equipment.affixes = new_affixes
        return equipment

    async def assign_character(
        self, equipment_id: int, owner_id: str, character_id: int
    ) -> Equipment:
        """将装备分配给指定角色。"""
        return await self.update_equipment(equipment_id, owner_id, character_id=character_id)

    async def share_to_group(self, equipment_id: int, owner_id: str, group_id: str) -> Equipment:
        """将装备分享到指定群。"""
        return await self.update_equipment(
            equipment_id, owner_id, scope=ScopeType.GROUP, group_id=group_id,
        )

    async def unshare(self, equipment_id: int, owner_id: str) -> Equipment:
        """取消装备分享。"""
        return await self.update_equipment(
            equipment_id, owner_id, scope=ScopeType.PRIVATE, group_id=None,
        )


def _load_tier_version() -> Optional[str]:
    """加载 tier.json 版本号"""
    try:
        from src.config import get_config
        tier_path = get_config().data_dir / "tier.json"
        with open(tier_path, "r", encoding="utf-8") as f:
            return json.load(f).get("version")
    except Exception:
        return None

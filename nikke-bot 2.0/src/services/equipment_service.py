"""
装备业务服务

核心业务层，负责装备全生命周期管理。
Handler → EquipmentService → Repository → Database
"""

import logging
from typing import Optional

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

logger = logging.getLogger(__name__)


class EquipmentService:
    """装备核心业务服务"""

    def __init__(self):
        self.equip_repo = EquipmentRepository()
        self.affix_repo = AffixRepository()
        self.template_repo = TemplateRepository()

    # ================================================================
    # 创建与保存
    # ================================================================

    async def create_equipment(
        self,
        owner_id: str,
        template_id: int,
        character_id: Optional[int],
        level: int,
        affixes_data: list[dict],
        screenshot_path: Optional[str] = None,
    ) -> Equipment:
        """创建一件新装备（含词条）。

        流程：
        1. 验证模板存在
        2. 从模板填充冗余字段
        3. 插入装备记录
        4. 计算词条 tier
        5. 批量插入词条
        6. 返回完整装备对象

        Args:
            owner_id: 用户 QQ 号
            template_id: 装备模板 ID
            character_id: 所属角色 ID
            level: 装备等级 0-5
            affixes_data: 词条数据列表 [{"name":"...", "value":26.36, "quality":"blue"}, ...]
            screenshot_path: 截图路径

        Returns:
            创建完成的装备对象（含 ID 和词条）

        Raises:
            ValueError: 模板不存在或数据校验失败
        """
        # 1. 验证模板
        template = await self.template_repo.get_by_id(template_id)
        if template is None:
            raise ValueError(f"装备模板不存在: template_id={template_id}")

        # 2. 构建装备对象
        equipment = Equipment(
            owner_id=owner_id,
            template_id=template_id,
            character_id=character_id,
            name=template.name,
            type=template.type,
            slot=template.slot,
            manufacturer=template.manufacturer,
            level=level,
            screenshot_path=screenshot_path,
        )

        # 3. 插入装备
        async with self.equip_repo as eq_repo:
            equipment = await eq_repo.insert(equipment)

        # 4. 构建词条对象并计算 tier
        from src.services.score_service import calculate_tier
        from src.config import get_config

        tier_version = None
        try:
            import json
            tier_path = get_config().data_dir / "tier.json"
            with open(tier_path, "r", encoding="utf-8") as f:
                tier_config = json.load(f)
                tier_version = tier_config.get("version")
        except Exception:
            pass

        affixes: list[Affix] = []
        for i, data in enumerate(affixes_data[:3], start=1):
            quality = data["quality"]
            value = data["value"]
            name = data["name"]
            tier = calculate_tier(quality, value)

            affix = Affix(
                equipment_id=equipment.id,
                name=name,
                value=value,
                quality=quality,
                tier=tier,
                sort_order=i,
                raw_name=data.get("raw_name"),
                tier_config_version=tier_version,
            )
            affixes.append(affix)

        # 5. 批量插入词条
        async with self.affix_repo as af_repo:
            affixes = await af_repo.insert_batch(affixes)

        equipment.affixes = affixes
        logger.info(f"用户 {owner_id} 创建装备 #{equipment.id}: {equipment.name}")

        return equipment

    # ================================================================
    # 查询
    # ================================================================

    async def get_equipment_detail(self, equipment_id: int) -> Optional[Equipment]:
        """查询装备详情（含词条）。

        Args:
            equipment_id: 装备 ID

        Returns:
            装备对象或 None
        """
        async with self.equip_repo as repo:
            equipment = await repo.get_by_id(equipment_id)
        if equipment is None:
            return None

        async with self.affix_repo as repo:
            equipment.affixes = await repo.get_by_equipment(equipment_id)

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
        """查询用户装备列表（分页，含词条）。

        Args:
            owner_id: 用户 QQ 号
            character_id: 角色筛选
            type_: 类型筛选
            slot: 部位筛选
            manufacturer: 制造商筛选
            page: 页码（从 1 开始）
            page_size: 每页数量

        Returns:
            (装备列表, 总数)
        """
        offset = (page - 1) * page_size

        async with self.equip_repo as repo:
            total = await repo.count_by_owner(owner_id, character_id, type_)
            equipments = await repo.get_by_owner(
                owner_id, character_id, type_, slot, manufacturer,
                limit=page_size, offset=offset,
            )

        # 批量加载词条
        async with self.affix_repo as af_repo:
            for eq in equipments:
                eq.affixes = await af_repo.get_by_equipment(eq.id)  # type: ignore

        return equipments, total

    async def search_by_affix(
        self, affix_name: str, owner_id: Optional[str] = None, limit: int = 20
    ) -> list[Equipment]:
        """按词条名称搜索装备。

        Args:
            affix_name: 词条规范名称
            owner_id: 用户筛选（可选）
            limit: 数量限制

        Returns:
            装备列表（含词条）
        """
        async with self.equip_repo as repo:
            equipments = await repo.search_by_affix_name(affix_name, owner_id, limit)

        async with self.affix_repo as af_repo:
            for eq in equipments:
                eq.affixes = await af_repo.get_by_equipment(eq.id)  # type: ignore

        return equipments

    async def get_top_by_score(self, limit: int = 10) -> list[Equipment]:
        """查询评分最高的装备（排行榜）。

        Args:
            limit: 数量限制

        Returns:
            装备列表（含词条）
        """
        async with self.equip_repo as repo:
            equipments = await repo.get_top_by_score(limit)

        async with self.affix_repo as af_repo:
            for eq in equipments:
                eq.affixes = await af_repo.get_by_equipment(eq.id)  # type: ignore

        return equipments

    async def get_group_shared(
        self, group_id: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Equipment], int]:
        """查询群共享装备。

        Args:
            group_id: 群号
            page: 页码
            page_size: 每页数量

        Returns:
            (装备列表, 总数)
        """
        offset = (page - 1) * page_size
        async with self.equip_repo as repo:
            equipments = await repo.get_group_shared(group_id, limit=page_size, offset=offset)

        async with self.affix_repo as af_repo:
            for eq in equipments:
                eq.affixes = await af_repo.get_by_equipment(eq.id)  # type: ignore

        return equipments, len(equipments)

    # ================================================================
    # 更新与删除
    # ================================================================

    async def update_equipment(
        self, equipment_id: int, owner_id: str, **kwargs
    ) -> Equipment:
        """更新装备属性。

        只更新提供的字段。词条更新需调用 update_affixes。

        Args:
            equipment_id: 装备 ID
            owner_id: 操作用户（校验权限）
            **kwargs: 要更新的字段

        Returns:
            更新后的装备

        Raises:
            ValueError: 装备不存在或无权操作
            RuntimeError: 装备已锁定
        """
        async with self.equip_repo as repo:
            equipment = await repo.get_by_id(equipment_id)
            if equipment is None:
                raise ValueError(f"装备不存在: #{equipment_id}")
            if equipment.owner_id != owner_id:
                raise ValueError("无权操作他人装备")
            if equipment.is_locked:
                raise RuntimeError(f"装备 #{equipment_id} 已锁定，请先解锁后再修改")

            # 应用更新
            for key, value in kwargs.items():
                if hasattr(equipment, key):
                    setattr(equipment, key, value)

            equipment = await repo.update(equipment)

        async with self.affix_repo as af_repo:
            equipment.affixes = await af_repo.get_by_equipment(equipment.id)  # type: ignore

        logger.info(f"用户 {owner_id} 更新装备 #{equipment_id}")
        return equipment

    async def delete_equipment(self, equipment_id: int, owner_id: str) -> bool:
        """删除装备（级联删除词条）。

        Args:
            equipment_id: 装备 ID
            owner_id: 操作用户（校验权限）

        Returns:
            是否删除成功

        Raises:
            RuntimeError: 装备已锁定
        """
        async with self.equip_repo as repo:
            equipment = await repo.get_by_id(equipment_id)
            if equipment is None:
                return False
            if equipment.owner_id != owner_id:
                raise ValueError("无权删除他人装备")
            if equipment.is_locked:
                raise RuntimeError(f"装备 #{equipment_id} 已锁定，请先解锁后再删除")

            result = await repo.delete(equipment_id)

        if result:
            logger.info(f"用户 {owner_id} 删除装备 #{equipment_id}")

        return result

    async def toggle_lock(self, equipment_id: int, owner_id: str) -> Equipment:
        """切换装备锁定状态。

        Args:
            equipment_id: 装备 ID
            owner_id: 操作用户

        Returns:
            更新后的装备
        """
        async with self.equip_repo as repo:
            equipment = await repo.get_by_id(equipment_id)
            if equipment is None:
                raise ValueError(f"装备不存在: #{equipment_id}")
            if equipment.owner_id != owner_id:
                raise ValueError("无权操作他人装备")

            equipment.is_locked = not equipment.is_locked
            equipment = await repo.update(equipment)

        async with self.affix_repo as af_repo:
            equipment.affixes = await af_repo.get_by_equipment(equipment.id)  # type: ignore

        return equipment

    async def update_affixes(
        self, equipment_id: int, owner_id: str, affixes_data: list[dict]
    ) -> Equipment:
        """替换装备的全部词条。

        Args:
            equipment_id: 装备 ID
            owner_id: 操作用户
            affixes_data: 新词条数据

        Returns:
            更新后的装备
        """
        async with self.equip_repo as repo:
            equipment = await repo.get_by_id(equipment_id)
            if equipment is None:
                raise ValueError(f"装备不存在: #{equipment_id}")
            if equipment.owner_id != owner_id:
                raise ValueError("无权操作他人装备")

        from src.services.score_service import calculate_tier
        from src.config import get_config
        import json

        tier_version = None
        try:
            tier_path = get_config().data_dir / "tier.json"
            with open(tier_path, "r", encoding="utf-8") as f:
                tier_config = json.load(f)
                tier_version = tier_config.get("version")
        except Exception:
            pass

        new_affixes: list[Affix] = []
        for i, data in enumerate(affixes_data[:3], start=1):
            affix = Affix(
                equipment_id=equipment_id,
                name=data["name"],
                value=data["value"],
                quality=data["quality"],
                tier=calculate_tier(data["quality"], data["value"]),
                sort_order=i,
                raw_name=data.get("raw_name"),
                tier_config_version=tier_version,
            )
            new_affixes.append(affix)

        async with self.affix_repo as af_repo:
            new_affixes = await af_repo.replace_affixes(equipment_id, new_affixes)

        equipment.affixes = new_affixes
        return equipment

    async def assign_character(
        self, equipment_id: int, owner_id: str, character_id: int
    ) -> Equipment:
        """将装备分配给指定角色。

        Args:
            equipment_id: 装备 ID
            owner_id: 操作用户
            character_id: 角色 ID

        Returns:
            更新后的装备
        """
        return await self.update_equipment(
            equipment_id, owner_id, character_id=character_id
        )

    async def share_to_group(self, equipment_id: int, owner_id: str, group_id: str) -> Equipment:
        """将装备分享到指定群。

        Args:
            equipment_id: 装备 ID
            owner_id: 操作用户
            group_id: 群号

        Returns:
            更新后的装备
        """
        return await self.update_equipment(
            equipment_id, owner_id,
            scope=ScopeType.GROUP,
            group_id=group_id,
        )

    async def unshare(self, equipment_id: int, owner_id: str) -> Equipment:
        """取消装备分享。

        Args:
            equipment_id: 装备 ID
            owner_id: 操作用户

        Returns:
            更新后的装备
        """
        return await self.update_equipment(
            equipment_id, owner_id,
            scope=ScopeType.PRIVATE,
            group_id=None,
        )

"""
装备 Repository

提供 equipments 表的 CRUD 和查询操作。
系统核心 Repository，90% 的查询围绕此表展开。
"""

import aiosqlite
from typing import Optional

from src.database.repositories import BaseRepository
from src.models.equipment import Equipment
from src.models.affix import Affix
from src.models.enums import (
    EquipmentType,
    EquipmentSlot,
    Manufacturer,
    AffixQuality,
    ScopeType,
)
from src.utils.time_utils import utc_now


class EquipmentRepository(BaseRepository):
    """装备实例数据访问层"""

    # ================================================================
    # 写入操作
    # ================================================================

    async def insert(self, equipment: Equipment) -> Equipment:
        """插入新装备（不包含词条，词条由 AffixRepository 单独写入）。

        使用事务：先插入装备，再插入词条。

        Args:
            equipment: 装备模型（id 会被忽略）

        Returns:
            包含数据库 ID 和时间戳的装备
        """
        now = utc_now()

        cursor = await self.db.execute(
            """
            INSERT INTO equipments (
                owner_id, template_id, character_id, name, type, slot, manufacturer,
                level, screenshot_path, scope, group_id, is_locked,
                score, is_bis, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipment.owner_id,
                equipment.template_id,
                equipment.character_id,
                equipment.name,
                equipment.type.value,
                equipment.slot.value,
                equipment.manufacturer.value,
                equipment.level,
                equipment.screenshot_path,
                equipment.scope.value,
                equipment.group_id,
                1 if equipment.is_locked else 0,
                equipment.score,
                1 if equipment.is_bis else 0 if equipment.is_bis is not None else None,
                now,
                now,
            ),
        )
        await self.db.commit()

        equipment.id = cursor.lastrowid
        equipment.created_at = now  # type: ignore
        equipment.updated_at = now  # type: ignore
        return equipment

    async def update(self, equipment: Equipment) -> Equipment:
        """更新装备基本信息（不含词条）。

        Args:
            equipment: 装备模型（id 必须存在）

        Returns:
            更新后的装备
        """
        if equipment.id is None:
            raise ValueError("更新装备时必须提供 id")

        now = utc_now()

        await self.db.execute(
            """
            UPDATE equipments SET
                character_id = ?,
                name = ?,
                type = ?,
                slot = ?,
                manufacturer = ?,
                level = ?,
                scope = ?,
                group_id = ?,
                is_locked = ?,
                score = ?,
                is_bis = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                equipment.character_id,
                equipment.name,
                equipment.type.value,
                equipment.slot.value,
                equipment.manufacturer.value,
                equipment.level,
                equipment.scope.value,
                equipment.group_id,
                1 if equipment.is_locked else 0,
                equipment.score,
                1 if equipment.is_bis else 0 if equipment.is_bis is not None else None,
                now,
                equipment.id,
            ),
        )
        await self.db.commit()

        equipment.updated_at = now  # type: ignore
        return equipment

    async def delete(self, equipment_id: int) -> bool:
        """删除装备（级联删除词条）。

        Args:
            equipment_id: 装备 ID

        Returns:
            是否删除成功
        """
        cursor = await self.db.execute(
            "DELETE FROM equipments WHERE id = ?", (equipment_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    # ================================================================
    # 读取操作
    # ================================================================

    async def get_by_id(self, equipment_id: int) -> Optional[Equipment]:
        """根据 ID 查询装备（不含词条）。

        Args:
            equipment_id: 装备 ID

        Returns:
            Equipment 或 None
        """
        cursor = await self.db.execute(
            """SELECT id, owner_id, template_id, character_id, name, type, slot,
                      manufacturer, level, screenshot_path, scope, group_id,
                      is_locked, score, is_bis, created_at, updated_at
               FROM equipments WHERE id = ?""",
            (equipment_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_equipment(row)

    async def get_by_owner(
        self,
        owner_id: str,
        character_id: Optional[int] = None,
        type_: Optional[EquipmentType] = None,
        slot: Optional[EquipmentSlot] = None,
        manufacturer: Optional[Manufacturer] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Equipment]:
        """查询用户装备，支持多条件筛选。

        Args:
            owner_id: 用户 QQ 号
            character_id: 角色 ID 筛选（可选）
            type_: 装备类型筛选（可选）
            slot: 装备部位筛选（可选）
            manufacturer: 制造商筛选（可选）
            limit: 每页数量
            offset: 偏移量

        Returns:
            装备列表（不含词条）
        """
        conditions = ["owner_id = ?"]
        params: list = [owner_id]

        if character_id is not None:
            conditions.append("character_id = ?")
            params.append(character_id)
        if type_ is not None:
            conditions.append("type = ?")
            params.append(type_.value)
        if slot is not None:
            conditions.append("slot = ?")
            params.append(slot.value)
        if manufacturer is not None:
            conditions.append("manufacturer = ?")
            params.append(manufacturer.value)

        where = " AND ".join(conditions)
        query = (
            f"SELECT id, owner_id, template_id, character_id, name, type, slot, "
            f"manufacturer, level, screenshot_path, scope, group_id, "
            f"is_locked, score, is_bis, created_at, updated_at "
            f"FROM equipments WHERE {where} "
            f"ORDER BY created_at DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, offset])

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

    async def count_by_owner(
        self,
        owner_id: str,
        character_id: Optional[int] = None,
        type_: Optional[EquipmentType] = None,
    ) -> int:
        """统计用户装备数量。

        Args:
            owner_id: 用户 QQ 号
            character_id: 角色 ID 筛选（可选）
            type_: 装备类型筛选（可选）

        Returns:
            装备数量
        """
        conditions = ["owner_id = ?"]
        params: list = [owner_id]
        if character_id is not None:
            conditions.append("character_id = ?")
            params.append(character_id)
        if type_ is not None:
            conditions.append("type = ?")
            params.append(type_.value)

        where = " AND ".join(conditions)
        cursor = await self.db.execute(
            f"SELECT COUNT(*) FROM equipments WHERE {where}", params
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def search_by_affix_name(
        self, affix_name: str, owner_id: Optional[str] = None, limit: int = 20
    ) -> list[Equipment]:
        """查询包含指定词条名称的装备。

        通过 JOIN affixes 表查询，按词条数值降序。

        Args:
            affix_name: 词条规范名称
            owner_id: 用户 QQ 号（可选，不传则查全部）
            limit: 返回数量

        Returns:
            装备列表（不含词条）
        """
        if owner_id:
            query = """
                SELECT DISTINCT e.id, e.owner_id, e.template_id, e.character_id,
                       e.name, e.type, e.slot, e.manufacturer, e.level,
                       e.screenshot_path, e.scope, e.group_id,
                       e.is_locked, e.score, e.is_bis, e.created_at, e.updated_at
                FROM equipments e
                INNER JOIN affixes a ON a.equipment_id = e.id
                WHERE a.name = ? AND e.owner_id = ?
                ORDER BY a.value DESC
                LIMIT ?
            """
            params = [affix_name, owner_id, limit]
        else:
            query = """
                SELECT DISTINCT e.id, e.owner_id, e.template_id, e.character_id,
                       e.name, e.type, e.slot, e.manufacturer, e.level,
                       e.screenshot_path, e.scope, e.group_id,
                       e.is_locked, e.score, e.is_bis, e.created_at, e.updated_at
                FROM equipments e
                INNER JOIN affixes a ON a.equipment_id = e.id
                WHERE a.name = ?
                ORDER BY a.value DESC
                LIMIT ?
            """
            params = [affix_name, limit]

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

    async def search_by_affix_tier(
        self, min_tier: int, owner_id: Optional[str] = None, limit: int = 20
    ) -> list[Equipment]:
        """查询词条阶级 >= min_tier 的装备。

        Args:
            min_tier: 最低阶级
            owner_id: 用户 QQ 号（可选）
            limit: 返回数量

        Returns:
            装备列表（不含词条）
        """
        if owner_id:
            query = """
                SELECT DISTINCT e.id, e.owner_id, e.template_id, e.character_id,
                       e.name, e.type, e.slot, e.manufacturer, e.level,
                       e.screenshot_path, e.scope, e.group_id,
                       e.is_locked, e.score, e.is_bis, e.created_at, e.updated_at
                FROM equipments e
                INNER JOIN affixes a ON a.equipment_id = e.id
                WHERE a.tier >= ? AND e.owner_id = ?
                ORDER BY a.tier DESC
                LIMIT ?
            """
            params = [min_tier, owner_id, limit]
        else:
            query = """
                SELECT DISTINCT e.id, e.owner_id, e.template_id, e.character_id,
                       e.name, e.type, e.slot, e.manufacturer, e.level,
                       e.screenshot_path, e.scope, e.group_id,
                       e.is_locked, e.score, e.is_bis, e.created_at, e.updated_at
                FROM equipments e
                INNER JOIN affixes a ON a.equipment_id = e.id
                WHERE a.tier >= ?
                ORDER BY a.tier DESC
                LIMIT ?
            """
            params = [min_tier, limit]

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

    async def get_top_by_score(self, limit: int = 10) -> list[Equipment]:
        """查询评分最高的装备。

        Args:
            limit: 返回数量

        Returns:
            装备列表（不含词条）
        """
        cursor = await self.db.execute(
            """SELECT id, owner_id, template_id, character_id, name, type, slot,
                      manufacturer, level, screenshot_path, scope, group_id,
                      is_locked, score, is_bis, created_at, updated_at
               FROM equipments
               WHERE score IS NOT NULL
               ORDER BY score DESC
               LIMIT ?""",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

    async def get_group_shared(
        self, group_id: str, limit: int = 50, offset: int = 0
    ) -> list[Equipment]:
        """查询群共享装备。

        Args:
            group_id: 群号
            limit: 每页数量
            offset: 偏移量

        Returns:
            装备列表（不含词条）
        """
        cursor = await self.db.execute(
            """SELECT id, owner_id, template_id, character_id, name, type, slot,
                      manufacturer, level, screenshot_path, scope, group_id,
                      is_locked, score, is_bis, created_at, updated_at
               FROM equipments
               WHERE scope = 'group' AND group_id = ?
               ORDER BY created_at DESC
               LIMIT ? OFFSET ?""",
            (group_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

    # ---- 内部方法 ----

    def _row_to_equipment(self, row: aiosqlite.Row) -> Equipment:
        """将数据库行转换为 Equipment 模型"""
        return Equipment(
            id=row["id"],
            owner_id=row["owner_id"],
            template_id=row["template_id"],
            character_id=row["character_id"],
            name=row["name"],
            type=EquipmentType(row["type"]),
            slot=EquipmentSlot(row["slot"]),
            manufacturer=Manufacturer(row["manufacturer"]),
            level=row["level"],
            screenshot_path=row["screenshot_path"],
            scope=ScopeType(row["scope"]),
            group_id=row["group_id"],
            is_locked=bool(row["is_locked"]),
            score=row["score"],
            is_bis=bool(row["is_bis"]) if row["is_bis"] is not None else None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            # affixes 需要单独查询后填充
            affixes=[],
        )

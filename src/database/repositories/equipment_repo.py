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
    ScopeType,
)
from src.utils.time_utils import utc_now


class EquipmentRepository(BaseRepository):
    """装备实例数据访问层。"""

    async def insert(self, equipment: Equipment) -> Equipment:
        """插入新装备（不含词条）。"""
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
        """更新装备基本信息（不含词条）。"""
        if equipment.id is None:
            raise ValueError("更新装备时必须提供 id")

        now = utc_now()

        await self.db.execute(
            """
            UPDATE equipments SET
                character_id = ?, name = ?, type = ?, slot = ?, manufacturer = ?,
                level = ?, scope = ?, group_id = ?,
                is_locked = ?, score = ?, is_bis = ?, updated_at = ?
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
        """删除装备（级联删除词条）。"""
        cursor = await self.db.execute(
            "DELETE FROM equipments WHERE id = ?", (equipment_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def get_by_id(self, equipment_id: int) -> Optional[Equipment]:
        """根据 ID 查询装备（不含词条）。"""
        cursor = await self.db.execute(
            _SELECT_EQUIPMENT + " WHERE id = ?",
            (equipment_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_equipment(row) if row else None

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
        """查询用户装备，支持多条件筛选。"""
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
            f"{_SELECT_EQUIPMENT} WHERE {where} "
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
        """统计用户装备数量。"""
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
        """查询包含指定词条名称的装备（JOIN affixes 表）。"""
        if owner_id:
            query = _SELECT_EQUIPMENT_JOIN_AFFIX + " WHERE a.name = ? AND e.owner_id = ? ORDER BY a.value DESC LIMIT ?"
            params = [affix_name, owner_id, limit]
        else:
            query = _SELECT_EQUIPMENT_JOIN_AFFIX + " WHERE a.name = ? ORDER BY a.value DESC LIMIT ?"
            params = [affix_name, limit]

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

    async def search_by_affix_tier(
        self, min_tier: int, owner_id: Optional[str] = None, limit: int = 20
    ) -> list[Equipment]:
        """查询词条阶级 >= min_tier 的装备。"""
        if owner_id:
            query = _SELECT_EQUIPMENT_JOIN_AFFIX + " WHERE a.tier >= ? AND e.owner_id = ? ORDER BY a.tier DESC LIMIT ?"
            params = [min_tier, owner_id, limit]
        else:
            query = _SELECT_EQUIPMENT_JOIN_AFFIX + " WHERE a.tier >= ? ORDER BY a.tier DESC LIMIT ?"
            params = [min_tier, limit]

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

    async def get_top_by_score(self, limit: int = 10) -> list[Equipment]:
        """查询评分最高的装备。"""
        cursor = await self.db.execute(
            _SELECT_EQUIPMENT + " WHERE score IS NOT NULL ORDER BY score DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

    async def get_group_shared(
        self, group_id: str, limit: int = 50, offset: int = 0
    ) -> list[Equipment]:
        """查询群共享装备。"""
        cursor = await self.db.execute(
            _SELECT_EQUIPMENT
            + " WHERE scope = 'group' AND group_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (group_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [self._row_to_equipment(r) for r in rows]

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
            affixes=[],
        )


# 复用 SQL 片段
_SELECT_EQUIPMENT = (
    "SELECT id, owner_id, template_id, character_id, name, type, slot, "
    "manufacturer, level, screenshot_path, scope, group_id, "
    "is_locked, score, is_bis, created_at, updated_at FROM equipments"
)

_SELECT_EQUIPMENT_JOIN_AFFIX = (
    "SELECT DISTINCT e.id, e.owner_id, e.template_id, e.character_id, "
    "e.name, e.type, e.slot, e.manufacturer, e.level, "
    "e.screenshot_path, e.scope, e.group_id, "
    "e.is_locked, e.score, e.is_bis, e.created_at, e.updated_at "
    "FROM equipments e INNER JOIN affixes a ON a.equipment_id = e.id"
)

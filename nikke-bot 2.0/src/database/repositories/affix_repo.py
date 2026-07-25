"""
词条 Repository

提供 affixes 表的 CRUD 操作。
"""

import aiosqlite

from src.database.repositories import BaseRepository
from src.models.affix import Affix
from src.models.enums import AffixQuality


class AffixRepository(BaseRepository):
    """词条数据访问层。"""

    async def insert(self, affix: Affix) -> Affix:
        """插入单条词条。"""
        cursor = await self.db.execute(
            """
            INSERT INTO affixes (
                equipment_id, name, value, quality, tier,
                raw_name, sort_order, tier_config_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                affix.equipment_id,
                affix.name,
                affix.value,
                affix.quality.value,
                affix.tier,
                affix.raw_name,
                affix.sort_order,
                affix.tier_config_version,
            ),
        )
        await self.db.commit()
        affix.id = cursor.lastrowid
        return affix

    async def insert_batch(self, affixes: list[Affix]) -> list[Affix]:
        """批量插入词条。"""
        rows = [
            (
                a.equipment_id,
                a.name,
                a.value,
                a.quality.value,
                a.tier,
                a.raw_name,
                a.sort_order,
                a.tier_config_version,
            )
            for a in affixes
        ]

        await self.db.executemany(
            """
            INSERT INTO affixes (
                equipment_id, name, value, quality, tier,
                raw_name, sort_order, tier_config_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        await self.db.commit()

        # 回填 ID
        if affixes and affixes[0].equipment_id is not None:
            eq_id = affixes[0].equipment_id
            inserted = await self.get_by_equipment(eq_id)
            for i in range(min(len(affixes), len(inserted))):
                affixes[i].id = inserted[i].id

        return affixes

    async def get_by_equipment(self, equipment_id: int) -> list[Affix]:
        """查询装备的所有词条，按 sort_order 升序。"""
        cursor = await self.db.execute(
            """SELECT id, equipment_id, name, value, quality, tier,
                      raw_name, sort_order, tier_config_version
               FROM affixes
               WHERE equipment_id = ?
               ORDER BY
                   CASE WHEN sort_order = 0 THEN 4 ELSE sort_order END ASC,
                   id ASC""",
            (equipment_id,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_affix(r) for r in rows]

    async def delete_by_equipment(self, equipment_id: int) -> int:
        """删除装备的所有词条。"""
        cursor = await self.db.execute(
            "DELETE FROM affixes WHERE equipment_id = ?", (equipment_id,)
        )
        await self.db.commit()
        return cursor.rowcount

    async def replace_affixes(
        self, equipment_id: int, affixes: list[Affix]
    ) -> list[Affix]:
        """替换装备的全部词条（先删后插）。"""
        await self.delete_by_equipment(equipment_id)
        for a in affixes:
            a.equipment_id = equipment_id
        return await self.insert_batch(affixes)

    def _row_to_affix(self, row: aiosqlite.Row) -> Affix:
        """将数据库行转换为 Affix 模型"""
        return Affix(
            id=row["id"],
            equipment_id=row["equipment_id"],
            name=row["name"],
            value=row["value"],
            quality=AffixQuality(row["quality"]),
            tier=row["tier"],
            raw_name=row["raw_name"],
            sort_order=row["sort_order"],
            tier_config_version=row["tier_config_version"],
        )

"""
装备模板 Repository

提供 equipment_templates 表的读写操作。
模板是静态数据（约 60 条），支持全量缓存。
"""

import aiosqlite
from typing import Optional

from src.database.repositories import BaseRepository
from src.models.equipment_template import EquipmentTemplate
from src.models.enums import EquipmentType, EquipmentSlot, Manufacturer


class TemplateRepository(BaseRepository):
    """装备模板数据访问层。"""

    async def upsert(self, template: EquipmentTemplate) -> EquipmentTemplate:
        """创建或更新装备模板（按 manufacturer+type+slot 去重）。"""
        await self.db.execute(
            """
            INSERT INTO equipment_templates (name, type, slot, manufacturer, rarity, icon_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(manufacturer, type, slot) DO UPDATE SET
                name = excluded.name,
                rarity = excluded.rarity,
                icon_name = excluded.icon_name
            """,
            (
                template.name,
                template.type.value,
                template.slot.value,
                template.manufacturer.value,
                template.rarity,
                template.icon_name,
            ),
        )
        await self.db.commit()

        row = await self.db.execute(
            "SELECT id FROM equipment_templates "
            "WHERE manufacturer = ? AND type = ? AND slot = ?",
            (template.manufacturer.value, template.type.value, template.slot.value),
        )
        result = await row.fetchone()
        if result:
            template.id = result[0] if isinstance(result, tuple) else result["id"]
        return template

    async def get_by_id(self, template_id: int) -> Optional[EquipmentTemplate]:
        """根据 ID 查询模板。"""
        cursor = await self.db.execute(
            "SELECT id, name, type, slot, manufacturer, rarity, icon_name "
            "FROM equipment_templates WHERE id = ?",
            (template_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_template(row) if row else None

    async def get_by_key(
        self, manufacturer: Manufacturer, type_: EquipmentType, slot: EquipmentSlot
    ) -> Optional[EquipmentTemplate]:
        """根据三元组查询模板。"""
        cursor = await self.db.execute(
            "SELECT id, name, type, slot, manufacturer, rarity, icon_name "
            "FROM equipment_templates WHERE manufacturer = ? AND type = ? AND slot = ?",
            (manufacturer.value, type_.value, slot.value),
        )
        row = await cursor.fetchone()
        return self._row_to_template(row) if row else None

    async def get_all(self) -> list[EquipmentTemplate]:
        """获取所有模板（全量加载，适合内存缓存）。"""
        cursor = await self.db.execute(
            "SELECT id, name, type, slot, manufacturer, rarity, icon_name "
            "FROM equipment_templates ORDER BY manufacturer, type, slot"
        )
        rows = await cursor.fetchall()
        return [self._row_to_template(r) for r in rows]

    async def count(self) -> int:
        """统计模板总数。"""
        cursor = await self.db.execute("SELECT COUNT(*) FROM equipment_templates")
        row = await cursor.fetchone()
        return row[0] if row else 0

    def _row_to_template(self, row: aiosqlite.Row) -> EquipmentTemplate:
        """将数据库行转换为 EquipmentTemplate 模型"""
        return EquipmentTemplate(
            id=row["id"],
            name=row["name"],
            type=EquipmentType(row["type"]),
            slot=EquipmentSlot(row["slot"]),
            manufacturer=Manufacturer(row["manufacturer"]),
            rarity=row["rarity"],
            icon_name=row["icon_name"],
        )

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
    """装备模板数据访问层"""

    async def upsert(self, template: EquipmentTemplate) -> EquipmentTemplate:
        """创建或更新装备模板（按 manufacturer+type+slot 去重）。

        Args:
            template: 模板模型

        Returns:
            包含数据库 ID 的模板
        """
        cursor = await self.db.execute(
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

        # 获取实际 ID
        row = await self.db.execute(
            "SELECT id FROM equipment_templates WHERE manufacturer = ? AND type = ? AND slot = ?",
            (template.manufacturer.value, template.type.value, template.slot.value),
        )
        result = await row.fetchone()
        if result:
            template.id = result[0] if isinstance(result, tuple) else result["id"]
        return template

    async def get_by_id(self, template_id: int) -> Optional[EquipmentTemplate]:
        """根据 ID 查询模板。

        Args:
            template_id: 模板 ID

        Returns:
            EquipmentTemplate 或 None
        """
        cursor = await self.db.execute(
            "SELECT id, name, type, slot, manufacturer, rarity, icon_name "
            "FROM equipment_templates WHERE id = ?",
            (template_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_template(row)

    async def get_by_key(
        self, manufacturer: Manufacturer, type_: EquipmentType, slot: EquipmentSlot
    ) -> Optional[EquipmentTemplate]:
        """根据三元组查询模板。

        Args:
            manufacturer: 制造商
            type_: 装备类型
            slot: 装备部位

        Returns:
            EquipmentTemplate 或 None
        """
        cursor = await self.db.execute(
            "SELECT id, name, type, slot, manufacturer, rarity, icon_name "
            "FROM equipment_templates WHERE manufacturer = ? AND type = ? AND slot = ?",
            (manufacturer.value, type_.value, slot.value),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_template(row)

    async def get_all(self) -> list[EquipmentTemplate]:
        """获取所有模板（全量加载，适合内存缓存）。

        Returns:
            模板列表
        """
        cursor = await self.db.execute(
            "SELECT id, name, type, slot, manufacturer, rarity, icon_name "
            "FROM equipment_templates ORDER BY manufacturer, type, slot"
        )
        rows = await cursor.fetchall()
        return [self._row_to_template(r) for r in rows]

    async def count(self) -> int:
        """统计模板总数。

        Returns:
            模板数量
        """
        cursor = await self.db.execute("SELECT COUNT(*) FROM equipment_templates")
        row = await cursor.fetchone()
        return row[0] if row else 0

    # ---- 内部方法 ----

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

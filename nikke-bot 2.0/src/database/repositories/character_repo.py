"""
角色 Repository

提供 characters 表的 CRUD 操作。
"""

import aiosqlite
from typing import Optional

from src.database.repositories import BaseRepository
from src.models.character import Character
from src.models.enums import Manufacturer
from src.utils.json_utils import safe_json_dumps, safe_json_loads


class CharacterRepository(BaseRepository):
    """角色数据访问层。"""

    async def insert(self, character: Character) -> Character:
        """插入新角色。"""
        aliases_json = safe_json_dumps(character.aliases)
        mfr_value = character.manufacturer.value if character.manufacturer else None

        cursor = await self.db.execute(
            """
            INSERT INTO characters (name, aliases, rarity, element, weapon_type, burst_level, manufacturer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                character.name,
                aliases_json,
                character.rarity,
                character.element,
                character.weapon_type,
                character.burst_level,
                mfr_value,
            ),
        )
        await self.db.commit()
        character.id = cursor.lastrowid
        return character

    async def upsert(self, character: Character) -> Character:
        """创建或更新角色（按 name 去重）。"""
        aliases_json = safe_json_dumps(character.aliases)
        mfr_value = character.manufacturer.value if character.manufacturer else None

        await self.db.execute(
            """
            INSERT INTO characters (name, aliases, rarity, element, weapon_type, burst_level, manufacturer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                aliases = excluded.aliases,
                rarity = excluded.rarity,
                element = excluded.element,
                weapon_type = excluded.weapon_type,
                burst_level = excluded.burst_level,
                manufacturer = excluded.manufacturer
            """,
            (
                character.name, aliases_json, character.rarity,
                character.element, character.weapon_type, character.burst_level, mfr_value,
            ),
        )
        await self.db.commit()

        row = await self.db.execute(
            "SELECT id FROM characters WHERE name = ?", (character.name,)
        )
        result = await row.fetchone()
        if result:
            character.id = result[0] if isinstance(result, tuple) else result["id"]
        return character

    async def get_by_id(self, char_id: int) -> Optional[Character]:
        """根据 ID 查询角色。"""
        cursor = await self.db.execute(
            "SELECT id, name, aliases, rarity, element, weapon_type, burst_level, manufacturer "
            "FROM characters WHERE id = ?",
            (char_id,),
        )
        row = await cursor.fetchone()
        return self._row_to_character(row) if row else None

    async def get_by_name(self, name: str) -> Optional[Character]:
        """根据规范名称查询角色。"""
        cursor = await self.db.execute(
            "SELECT id, name, aliases, rarity, element, weapon_type, burst_level, manufacturer "
            "FROM characters WHERE name = ?",
            (name,),
        )
        row = await cursor.fetchone()
        return self._row_to_character(row) if row else None

    async def search_by_alias(self, keyword: str) -> Optional[Character]:
        """通过别名搜索角色（先精确 name，再 LIKE aliases）。"""
        result = await self.get_by_name(keyword)
        if result:
            return result

        cursor = await self.db.execute(
            "SELECT id, name, aliases, rarity, element, weapon_type, burst_level, manufacturer "
            "FROM characters WHERE aliases LIKE ? LIMIT 1",
            (f"%{keyword}%",),
        )
        row = await cursor.fetchone()
        return self._row_to_character(row) if row else None

    async def get_all(self) -> list[Character]:
        """获取所有角色。"""
        cursor = await self.db.execute(
            "SELECT id, name, aliases, rarity, element, weapon_type, burst_level, manufacturer "
            "FROM characters ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [self._row_to_character(r) for r in rows]

    async def delete(self, char_id: int) -> bool:
        """删除角色（引用该角色的装备 character_id 置空）。"""
        cursor = await self.db.execute(
            "DELETE FROM characters WHERE id = ?", (char_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    def _row_to_character(self, row: aiosqlite.Row) -> Character:
        """将数据库行转换为 Character 模型"""
        aliases_raw = row["aliases"] or "[]"
        mfr_raw = row["manufacturer"]
        return Character(
            id=row["id"],
            name=row["name"],
            aliases=safe_json_loads(aliases_raw, default=[]),
            rarity=row["rarity"],
            element=row["element"],
            weapon_type=row["weapon_type"],
            burst_level=row["burst_level"],
            manufacturer=Manufacturer(mfr_raw) if mfr_raw else None,
        )

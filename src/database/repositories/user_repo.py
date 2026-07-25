"""
用户 Repository

提供 users 表的 CRUD 操作。
"""

import aiosqlite
from typing import Optional

from src.database.repositories import BaseRepository
from src.models.user import User, UserPreferences
from src.utils.time_utils import utc_now
from src.utils.json_utils import safe_json_dumps, safe_json_loads


class UserRepository(BaseRepository):
    """用户数据访问层。

    使用方式:
        repo = UserRepository(db)
        user = await repo.get_by_id("123456789")
    """

    async def upsert(self, user: User) -> User:
        """创建或更新用户。"""
        now = utc_now()
        prefs_json = safe_json_dumps(user.preferences.model_dump())

        await self.db.execute(
            """
            INSERT INTO users (qq_id, nickname, preferences, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(qq_id) DO UPDATE SET
                nickname = excluded.nickname,
                preferences = excluded.preferences,
                updated_at = excluded.updated_at
            """,
            (user.qq_id, user.nickname, prefs_json, now, now),
        )
        await self.db.commit()

        user.registered_at = user.registered_at or now  # type: ignore
        user.last_active_at = now  # type: ignore
        return user

    async def get_by_id(self, qq_id: str) -> Optional[User]:
        """根据 QQ 号查询用户。"""
        cursor = await self.db.execute(
            "SELECT qq_id, nickname, preferences, created_at, updated_at "
            "FROM users WHERE qq_id = ?",
            (qq_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    async def delete(self, qq_id: str) -> bool:
        """删除用户（级联删除其装备）。"""
        cursor = await self.db.execute(
            "DELETE FROM users WHERE qq_id = ?", (qq_id,)
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def exists(self, qq_id: str) -> bool:
        """检查用户是否存在。"""
        cursor = await self.db.execute(
            "SELECT 1 FROM users WHERE qq_id = ? LIMIT 1", (qq_id,)
        )
        return await cursor.fetchone() is not None

    def _row_to_user(self, row: aiosqlite.Row) -> User:
        """将数据库行转换为 User 模型"""
        prefs_raw = row["preferences"] or "{}"
        prefs_dict = safe_json_loads(prefs_raw, default={})
        return User(
            qq_id=row["qq_id"],
            nickname=row["nickname"] or "",
            preferences=UserPreferences(**prefs_dict),
            created_at=row["created_at"],
            last_active_at=row["updated_at"],
        )

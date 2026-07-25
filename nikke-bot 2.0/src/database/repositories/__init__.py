"""
Repository 基类

提供数据库连接的上下文管理，所有 Repository 继承此类。
"""

import aiosqlite
from typing import Optional

from src.database.connection import create_connection


class BaseRepository:
    """数据访问层基类。

    子类通过 self.db 访问数据库连接。
    支持外部传入连接（事务场景）或自动创建。
    """

    def __init__(self, db: Optional[aiosqlite.Connection] = None):
        self._db = db
        self._owns_connection = db is None

    async def __aenter__(self):
        if self._db is None:
            self._db = await create_connection()
            self._owns_connection = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._owns_connection and self._db:
            await self._db.close()

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Repository 未初始化，请使用 async with 上下文")
        return self._db

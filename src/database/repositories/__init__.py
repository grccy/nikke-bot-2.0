"""
Repository 基类

所有 Repository 通过 constructor injection 接收数据库连接。
连接由 DatabaseManager 统一管理。

使用方式：
    repo = UserRepository(db_manager.connection)
    user = await repo.get_by_id("123")
"""

import aiosqlite


class BaseRepository:
    """数据访问层基类。

    子类通过 self.db 访问数据库连接。
    所有 SQL 操作不显式管理事务——由调用方（Service 层）负责 commit / rollback。
    """

    def __init__(self, db: aiosqlite.Connection):
        if db is None:
            raise ValueError("数据库连接不能为空")
        self._db = db

    @property
    def db(self) -> aiosqlite.Connection:
        return self._db

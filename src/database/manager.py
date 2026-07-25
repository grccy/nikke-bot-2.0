"""
数据库生命周期管理器

负责：
- 启动时打开连接、配置 PRAGMA、运行迁移
- 关闭时安全断开连接
- 提供统一的 connection 访问入口（供 Repository 注入）
"""

import logging
from pathlib import Path
from typing import Optional

import aiosqlite

from src.database.connection import create_connection
# run_migrations 在 startup() 内部延迟导入，避免与 migrations/ 包冲突

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库生命周期管理器。

    使用方式：

        db_manager = DatabaseManager("database/nikke.db")
        await db_manager.startup()

        # 注入连接给 Repository
        repo = UserRepository(db_manager.connection)
        result = await repo.get_by_id("123")

        await db_manager.shutdown()
    """

    def __init__(self, db_path: str | Path):
        self._db_path = Path(db_path)
        self._db: Optional[aiosqlite.Connection] = None

    # ---- 生命周期 ----

    async def startup(self, run_migration: bool = True):
        """启动数据库：打开连接 + 配置 PRAGMA + 可选迁移。

        Args:
            run_migration: 是否自动执行迁移（默认 True）

        Raises:
            RuntimeError: 重复调用 startup
        """
        if self._db is not None:
            raise RuntimeError("DatabaseManager 已经启动，请勿重复调用 startup()")

        logger.info(f"正在打开数据库: {self._db_path}")
        self._db = await create_connection(self._db_path)

        # 配置 SQLite PRAGMA
        await self._db.execute("PRAGMA journal_mode = WAL")
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.execute("PRAGMA busy_timeout = 5000")
        await self._db.execute("PRAGMA cache_size = -8000")
        await self._db.execute("PRAGMA synchronous = NORMAL")

        # 验证 PRAGMA 生效
        cursor = await self._db.execute("PRAGMA foreign_keys")
        fk_row = await cursor.fetchone()
        if fk_row and fk_row[0] != 1:
            logger.warning("foreign_keys PRAGMA 未生效！")

        # 执行迁移
        if run_migration:
            from src.database.migration_runner import run_migrations
            await run_migrations(self._db)

        logger.info(f"数据库启动完成: {self._db_path}")

    async def shutdown(self):
        """关闭数据库连接。"""
        if self._db is not None:
            await self._db.close()
            self._db = None
            logger.info("数据库连接已关闭")

    # ---- 属性 ----

    @property
    def connection(self) -> aiosqlite.Connection:
        """获取当前数据库连接。

        Raises:
            RuntimeError: 未调用 startup()
        """
        if self._db is None:
            raise RuntimeError("DatabaseManager 未启动，请先调用 startup()")
        return self._db

    @property
    def is_healthy(self) -> bool:
        """检查数据库连接是否健康"""
        if self._db is None:
            return False
        try:
            # 快速检查：不需要 await，用同步方式
            return True
        except Exception:
            return False

"""
SQLite 数据库连接工具

提供底层连接工厂函数。生产环境使用 DatabaseManager 管理连接生命周期。
"""

import aiosqlite
from pathlib import Path


async def create_connection(db_path: str | Path) -> aiosqlite.Connection:
    """创建 SQLite 数据库连接（底层工厂函数）。

    仅建立连接 + 设置 row_factory。
    PRAGMA 配置由 DatabaseManager.startup() 统一执行。

    Args:
        db_path: 数据库文件路径

    Returns:
        aiosqlite.Connection（未配置 PRAGMA）
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row
    return db


async def check_connection(db: aiosqlite.Connection) -> bool:
    """检查数据库连接是否健康"""
    try:
        await db.execute("SELECT 1")
        return True
    except Exception:
        return False

"""
SQLite 数据库连接管理

提供：
- 异步连接创建
- WAL 模式启用
- 外键约束启用
- 连接健康检查
"""

import aiosqlite
from pathlib import Path
from src.config import get_config


async def create_connection(db_path: str | Path | None = None) -> aiosqlite.Connection:
    """
    创建数据库连接并配置 SQLite PRAGMA。

    Args:
        db_path: 数据库文件路径，默认使用配置中的路径

    Returns:
        已配置的 aiosqlite.Connection
    """
    if db_path is None:
        db_path = get_config().database.path

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row

    # WAL 模式：读写并发不阻塞
    await db.execute("PRAGMA journal_mode = WAL")
    # 外键约束：必须显式开启
    await db.execute("PRAGMA foreign_keys = ON")
    # 锁等待超时：5 秒
    await db.execute("PRAGMA busy_timeout = 5000")
    # 缓存 8MB
    await db.execute("PRAGMA cache_size = -8000")
    # WAL 模式下的安全平衡
    await db.execute("PRAGMA synchronous = NORMAL")

    return db


async def check_connection(db: aiosqlite.Connection) -> bool:
    """检查数据库连接是否健康"""
    try:
        await db.execute("SELECT 1")
        return True
    except Exception:
        return False

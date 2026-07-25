"""
数据库迁移管理器

统一使用增量迁移策略：
- 首次启动：从版本 0 执行到最新版本
- 后续启动：执行未应用的迁移
- 每个迁移在独立事务中运行
- 已应用的迁移不可修改

新增迁移步骤：
1. 在下方创建 @register 装饰的异步函数
2. 版本号递增
3. 重启机器人自动执行
"""

import logging
from pathlib import Path
from typing import Callable, Awaitable
import aiosqlite

from src.database.connection import create_connection

logger = logging.getLogger(__name__)

# 迁移定义：(版本号, 描述, 迁移函数)
Migration = tuple[int, str, Callable[[aiosqlite.Connection], Awaitable[None]]]

# 迁移注册表（按版本号排序）
_migrations: list[Migration] = []


def register(version: int, description: str):
    """装饰器：注册迁移函数"""

    def decorator(func: Callable[[aiosqlite.Connection], Awaitable[None]]):
        _migrations.append((version, description, func))
        _migrations.sort(key=lambda m: m[0])
        return func

    return decorator


# ============================================================
# 迁移 v1：初始建表
# ============================================================

@register(version=1, description="创建初始表结构（7 张核心表 + 全部索引）")
async def migration_001_initial_schema(db: aiosqlite.Connection):
    """创建全部核心表及索引"""
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")
    await db.executescript(schema_sql)


# ============================================================
# 后续迁移模板（按需取消注释并实现）
# ============================================================

# @register(version=2, description="优化索引：删除低效单列，新增复合索引")
# async def migration_002_optimize_indexes(db: aiosqlite.Connection):
#     await db.execute("DROP INDEX IF EXISTS idx_equipments_slot")
#     await db.execute("DROP INDEX IF EXISTS idx_equipments_manufacturer")
#     await db.execute(
#         "CREATE INDEX IF NOT EXISTS idx_equipments_filter "
#         "ON equipments(manufacturer, type, slot)"
#     )

# @register(version=3, description="强化约束：添加 CHECK 和 UNIQUE 约束")
# async def migration_003_strengthen_constraints(db: aiosqlite.Connection):
#     # 注意：此迁移已在 v1 schema.sql 中包含，仅用于从旧版本升级的场景
#     pass

# @register(version=4, description="OCR 外键修复：user_id 改为 SET NULL")
# async def migration_004_fix_ocr_fk(db: aiosqlite.Connection):
#     # 重建 ocr_records 表以修改外键策略
#     pass

# @register(version=5, description="新增 is_locked 字段")
# async def migration_005_add_is_locked(db: aiosqlite.Connection):
#     await db.execute(
#         "ALTER TABLE equipments ADD COLUMN is_locked INTEGER NOT NULL DEFAULT 0 "
#         "CHECK (is_locked IN (0, 1))"
#     )
#     await db.execute(
#         "CREATE INDEX IF NOT EXISTS idx_equipments_is_locked ON equipments(is_locked)"
#     )

# @register(version=6, description="创建 operation_logs 表")
# async def migration_006_create_operation_logs(db: aiosqlite.Connection):
#     pass


# ============================================================
# 迁移管理器
# ============================================================

async def _ensure_schema_version_table(db: aiosqlite.Connection):
    """确保 schema_version 表存在"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version   INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL
        )
    """)


async def _get_current_version(db: aiosqlite.Connection) -> int:
    """获取当前数据库版本（无记录返回 0）"""
    cursor = await db.execute("SELECT MAX(version) FROM schema_version")
    row = await cursor.fetchone()
    return row[0] if row and row[0] is not None else 0


async def run_migrations():
    """
    执行所有未应用的数据库迁移。

    策略：
    - 首次启动：current_version=0，执行所有迁移
    - 后续启动：执行 version > current_version 的迁移
    - 每个迁移在独立事务中运行，失败回滚
    """
    db = await create_connection()

    try:
        await _ensure_schema_version_table(db)
        current_version = await _get_current_version(db)

        logger.info(f"当前数据库版本: {current_version}")

        for version, description, migrate_func in _migrations:
            if version > current_version:
                logger.info(f"正在应用迁移 v{version}: {description}")

                try:
                    await db.execute("BEGIN")
                    await migrate_func(db)
                    await db.execute(
                        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                        (version, _utc_now()),
                    )
                    await db.execute("COMMIT")
                    logger.info(f"  迁移 v{version} 完成: {description}")

                except Exception:
                    await db.execute("ROLLBACK")
                    logger.error(
                        f"  迁移 v{version} 失败: {description}", exc_info=True
                    )
                    raise

        logger.info(f"数据库迁移完成，当前版本: {await _get_current_version(db)}")

    finally:
        await db.close()


def _utc_now() -> str:
    """返回 ISO 8601 UTC 时间戳"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

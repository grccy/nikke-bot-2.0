"""
数据库迁移管理器

从 database/schema/ 目录自动加载 .sql 文件作为迁移脚本。
文件名约定: vNNN_description.sql（NNN = 三位数版本号，如 v001_initial.sql）。

特性：
- 首次启动：扫描全部 SQL 文件，按版本号排序执行
- 后续启动：只执行 version > current_version 的迁移
- 每个迁移在独立事务中运行，失败回滚
- 已应用的迁移不可修改

新增迁移：
1. 在 database/schema/ 目录下新建 vNNN_description.sql 文件
2. 文件头部注释格式: -- vNNN: 简短标题
                                     -- Description: 详细描述
3. 重启机器人自动执行
"""

import logging
import re
from pathlib import Path
from typing import List, NamedTuple

import aiosqlite

logger = logging.getLogger(__name__)

# SQL 文件命名规范: v001_initial.sql
_FILENAME_PATTERN = re.compile(r"^v(\d{3})_(.+)\.sql$")

# 从 SQL 注释提取描述
_DESC_PATTERN = re.compile(r"--\s*Description:\s*(.+)")


class MigrationFile(NamedTuple):
    """迁移文件描述"""
    version: int
    name: str
    description: str
    path: Path

    @property
    def sql(self) -> str:
        return self.path.read_text(encoding="utf-8")


def _discover_migrations(schema_dir: Path) -> List[MigrationFile]:
    """扫描 schema/ 目录，发现并返回排序后的迁移文件列表。

    Args:
        schema_dir: schema SQL 文件所在目录

    Returns:
        按 version 排序的 MigrationFile 列表
    """
    if not schema_dir.exists():
        logger.warning(f"schema 目录不存在: {schema_dir}")
        return []

    migrations: List[MigrationFile] = []

    for filepath in sorted(schema_dir.glob("v*.sql")):
        match = _FILENAME_PATTERN.match(filepath.name)
        if not match:
            logger.warning(f"跳过不符合命名规范的 SQL 文件: {filepath.name}")
            continue

        version_str, name = match.groups()
        version = int(version_str)

        # 从 SQL 文件头部提取 Description
        description = name.replace("_", " ")
        try:
            first_lines = filepath.read_text(encoding="utf-8")[:500]
            desc_match = _DESC_PATTERN.search(first_lines)
            if desc_match:
                description = desc_match.group(1).strip()
        except Exception:
            pass

        migrations.append(MigrationFile(
            version=version,
            name=name,
            description=description,
            path=filepath,
        ))

    migrations.sort(key=lambda m: m.version)
    return migrations


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


async def _apply_migration(db: aiosqlite.Connection, migration: MigrationFile):
    """应用单个迁移文件。

    Args:
        db: 数据库连接
        migration: 迁移文件
    """
    sql = migration.sql
    logger.info(f"  执行 SQL ({len(sql)} bytes)...")
    await db.executescript(sql)
    await db.execute(
        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
        (migration.version, _utc_now()),
    )


async def run_migrations(db: aiosqlite.Connection):
    """执行所有未应用的数据库迁移。

    Args:
        db: 数据库连接（已由 DatabaseManager 创建和配置）
    """
    schema_dir = Path(__file__).parent / "schema"
    discovered = _discover_migrations(schema_dir)

    if not discovered:
        logger.warning("未发现任何迁移 SQL 文件")
        return

    await _ensure_schema_version_table(db)
    current_version = await _get_current_version(db)

    logger.info(f"当前数据库版本: {current_version}, "
                f"可用迁移: {[m.version for m in discovered]}")

    applied = 0
    for migration in discovered:
        if migration.version > current_version:
            logger.info(f"正在应用迁移 v{migration.version:03d}: {migration.description}")

            try:
                await db.execute("BEGIN")
                await _apply_migration(db, migration)
                await db.execute("COMMIT")
                logger.info(f"  ✓ 迁移 v{migration.version:03d} 完成")
                applied += 1

            except Exception:
                await db.execute("ROLLBACK")
                logger.error(
                    f"  ✗ 迁移 v{migration.version:03d} 失败: {migration.description}",
                    exc_info=True,
                )
                raise

    if applied > 0:
        logger.info(f"数据库迁移完成: {applied} 个已应用, "
                    f"当前版本: {await _get_current_version(db)}")
    else:
        logger.info("数据库已是最新版本，无需迁移")


def _utc_now() -> str:
    """返回 ISO 8601 UTC 时间戳"""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

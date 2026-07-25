"""
测试数据库迁移系统
"""

import pytest


@pytest.mark.asyncio
async def test_migrations_run(db_manager):
    """迁移后核心表应存在"""
    db = db_manager.connection
    tables = [
        "schema_version", "users", "characters",
        "equipment_templates", "equipments", "affixes",
        "ocr_records", "operation_logs",
    ]
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ("
        + ",".join(f"'{t}'" for t in tables) + ")"
    )
    rows = await cursor.fetchall()
    found = {r[0] for r in rows}
    for table in tables:
        assert table in found, f"表 {table} 未创建"


@pytest.mark.asyncio
async def test_schema_version_recorded(db_manager):
    """迁移后应有 schema_version 记录"""
    cursor = await db_manager.connection.execute(
        "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] >= 1


@pytest.mark.asyncio
async def test_foreign_keys_enabled(db_manager):
    """外键约束应开启"""
    cursor = await db_manager.connection.execute("PRAGMA foreign_keys")
    row = await cursor.fetchone()
    assert row[0] == 1, "foreign_keys 未开启"


@pytest.mark.asyncio
async def test_wal_mode_enabled(db_manager):
    """WAL 模式应开启"""
    cursor = await db_manager.connection.execute("PRAGMA journal_mode")
    row = await cursor.fetchone()
    assert row[0].lower() == "wal", f"journal_mode 不是 WAL: {row[0]}"


@pytest.mark.asyncio
async def test_idempotent_migrations(db_manager):
    """验证迁移的幂等性：第二次 startup 不应报错"""
    # DatabaseManager 在 fixture 中已 startup 一次
    # 手动再跑一次 run_migrations 验证幂等
    from src.database.migrations import run_migrations
    await run_migrations(db_manager.connection)
    # 不抛异常 = 通过

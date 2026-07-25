"""
测试数据库迁移系统
"""

import pytest
from src.database.connection import create_connection


@pytest.mark.asyncio
async def test_migrations_run():
    """迁移执行后表结构应存在"""
    db = await create_connection()
    try:
        # 检查核心表是否存在
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
        found_tables = {r[0] for r in rows}
        for table in tables:
            assert table in found_tables, f"表 {table} 未创建"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_schema_version_recorded():
    """迁移后 schema_version 应有记录"""
    db = await create_connection()
    try:
        cursor = await db.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] >= 1
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_foreign_keys_enabled():
    """外键约束应开启"""
    db = await create_connection()
    try:
        cursor = await db.execute("PRAGMA foreign_keys")
        row = await cursor.fetchone()
        assert row[0] == 1, "foreign_keys 未开启"
    finally:
        await db.close()


@pytest.mark.asyncio
async def test_wal_mode_enabled():
    """WAL 模式应开启"""
    db = await create_connection()
    try:
        cursor = await db.execute("PRAGMA journal_mode")
        row = await cursor.fetchone()
        assert row[0].lower() == "wal", f"journal_mode 不是 WAL: {row[0]}"
    finally:
        await db.close()

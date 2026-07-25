"""
测试公共配置

提供测试数据库和常用 Fixture。
"""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from src.config import _config, AppConfig, DatabaseConfig, reload_config


@pytest.fixture(scope="session")
def event_loop():
    """为整个测试 session 创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_test_env(monkeypatch, tmp_path):
    """每个测试前自动设置隔离环境。

    - 使用临时数据库
    - 不加载 .env 文件
    """
    # 设置临时数据库路径
    test_db = tmp_path / "test_nikke.db"

    # 重置全局配置为测试配置
    test_config = AppConfig(
        database=DatabaseConfig(path=test_db),
    )

    # 注入 Mock 配置
    global _config
    from src.config import _config
    _config = test_config

    # 创建数据库并运行迁移
    from src.database.connection import create_connection
    from src.database.migrations import run_migrations

    # 临时替换配置中的路径
    monkeypatch.setattr(
        "src.database.migrations.create_connection",
        lambda: create_connection(test_db),
    )
    monkeypatch.setattr(
        "src.database.connection.create_connection",
        lambda db_path=None: create_connection(test_db),
    )
    monkeypatch.setattr(
        "src.config.get_config",
        lambda: test_config,
    )

    await run_migrations()
    yield

    # 清理
    if test_db.exists():
        test_db.unlink()

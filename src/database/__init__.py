"""
数据库层

提供：
- DatabaseManager: 连接生命周期管理
- create_connection: 底层连接工厂（测试用）
- run_migrations: 迁移管理器

Repository 构造规范：
    所有 Repository 通过 constructor injection 接收 aiosqlite.Connection。
    连接由 DatabaseManager 在 startup 时创建，shutdown 时关闭。
"""

from src.database.connection import create_connection, check_connection
from src.database.manager import DatabaseManager

# 延迟导入：避免 migrations 包和 migrations.py 同名冲突
# run_migrations 由 DatabaseManager.startup() 内部调用

__all__ = [
    "DatabaseManager",
    "create_connection",
    "check_connection",
]

"""
测试公共配置

提供测试数据库和常用 Fixture。
使用内存数据库 + DatabaseManager 确保测试隔离。
"""

import asyncio
import pytest

from src.database.manager import DatabaseManager


@pytest.fixture(scope="session")
def event_loop():
    """为整个测试 session 创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_manager(tmp_path):
    """创建独立的测试数据库（文件模式，非内存，因为 WAL 需要文件）。

    每个测试使用独立的临时目录和数据库。
    """
    db_path = tmp_path / "test_nikke.db"
    mgr = DatabaseManager(db_path)
    await mgr.startup(run_migration=True)
    yield mgr
    await mgr.shutdown()


# ---- Repository fixtures ----

from src.database.repositories.user_repo import UserRepository
from src.database.repositories.equipment_repo import EquipmentRepository
from src.database.repositories.affix_repo import AffixRepository
from src.database.repositories.character_repo import CharacterRepository
from src.database.repositories.template_repo import TemplateRepository
from src.database.repositories.ocr_record_repo import OCRRecordRepository


@pytest.fixture
def user_repo(db_manager):
    return UserRepository(db_manager.connection)


@pytest.fixture
def equipment_repo(db_manager):
    return EquipmentRepository(db_manager.connection)


@pytest.fixture
def affix_repo(db_manager):
    return AffixRepository(db_manager.connection)


@pytest.fixture
def character_repo(db_manager):
    return CharacterRepository(db_manager.connection)


@pytest.fixture
def template_repo(db_manager):
    return TemplateRepository(db_manager.connection)


@pytest.fixture
def ocr_record_repo(db_manager):
    return OCRRecordRepository(db_manager.connection)


# ---- Service fixtures ----

from src.services.equipment_service import EquipmentService


@pytest.fixture
def equip_service(db_manager):
    return EquipmentService(
        equip_repo=EquipmentRepository(db_manager.connection),
        affix_repo=AffixRepository(db_manager.connection),
        template_repo=TemplateRepository(db_manager.connection),
    )

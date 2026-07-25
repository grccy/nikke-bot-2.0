"""
测试 UserRepository
"""

import pytest
from src.models.user import User
from src.database.repositories.user_repo import UserRepository


@pytest.mark.asyncio
async def test_insert_and_get_user():
    """插入并查询用户"""
    user = User(qq_id="111222333", nickname="测试")

    async with UserRepository() as repo:
        saved = await repo.upsert(user)
        assert saved.qq_id == "111222333"

    async with UserRepository() as repo:
        fetched = await repo.get_by_id("111222333")
        assert fetched is not None
        assert fetched.nickname == "测试"


@pytest.mark.asyncio
async def test_upsert_updates_nickname():
    """更新已存在用户的昵称"""
    async with UserRepository() as repo:
        user = User(qq_id="444555666", nickname="旧昵称")
        await repo.upsert(user)

        user.nickname = "新昵称"
        await repo.upsert(user)

        fetched = await repo.get_by_id("444555666")
        assert fetched.nickname == "新昵称"


@pytest.mark.asyncio
async def test_get_nonexistent_user():
    """查询不存在的用户返回 None"""
    async with UserRepository() as repo:
        result = await repo.get_by_id("999999999")
        assert result is None


@pytest.mark.asyncio
async def test_exists():
    """检查用户存在性"""
    async with UserRepository() as repo:
        await repo.upsert(User(qq_id="777888999"))
        assert await repo.exists("777888999") is True
        assert await repo.exists("000000000") is False

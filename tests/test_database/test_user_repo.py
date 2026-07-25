"""
测试 UserRepository
"""

import pytest
from src.models.user import User


@pytest.mark.asyncio
async def test_insert_and_get_user(user_repo):
    """插入并查询用户"""
    user = User(qq_id="111222333", nickname="测试")
    saved = await user_repo.upsert(user)
    assert saved.qq_id == "111222333"

    fetched = await user_repo.get_by_id("111222333")
    assert fetched is not None
    assert fetched.nickname == "测试"


@pytest.mark.asyncio
async def test_upsert_updates_nickname(user_repo):
    """更新已存在用户的昵称"""
    await user_repo.upsert(User(qq_id="444555666", nickname="旧昵称"))
    await user_repo.upsert(User(qq_id="444555666", nickname="新昵称"))
    fetched = await user_repo.get_by_id("444555666")
    assert fetched.nickname == "新昵称"


@pytest.mark.asyncio
async def test_get_nonexistent_user(user_repo):
    """查询不存在的用户返回 None"""
    result = await user_repo.get_by_id("999")
    assert result is None


@pytest.mark.asyncio
async def test_exists(user_repo):
    """检查用户存在性"""
    await user_repo.upsert(User(qq_id="777888999"))
    assert await user_repo.exists("777888999") is True
    assert await user_repo.exists("000") is False

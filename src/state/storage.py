"""
会话状态持久化存储

将用户状态存储到 SQLite user_states 表中。
支持超时自动清理。
"""

import aiosqlite
import logging
from typing import Optional

from src.database.connection import create_connection
from src.state.types import UserSession, SessionStateType
from src.utils.time_utils import utc_now, parse_utc
from src.utils.json_utils import safe_json_dumps, safe_json_loads

logger = logging.getLogger(__name__)

# 状态默认过期时间（分钟）
DEFAULT_TTL_MINUTES = 5


async def init_state_table():
    """初始化 user_states 表（在首次迁移后调用）"""
    db = await create_connection()
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_states (
                user_id    TEXT PRIMARY KEY,
                state_type TEXT NOT NULL,
                payload    TEXT NOT NULL DEFAULT '{}',
                message_id TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)
        await db.commit()
    finally:
        await db.close()


async def get_state(user_id: str) -> Optional[UserSession]:
    """获取用户当前会话状态。

    自动清除过期状态。

    Args:
        user_id: 用户 QQ 号

    Returns:
        UserSession 或 None（无活跃状态或已过期）
    """
    db = await create_connection()
    try:
        cursor = await db.execute(
            "SELECT user_id, state_type, payload, message_id, created_at, expires_at "
            "FROM user_states WHERE user_id = ?",
            (user_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        # 检查是否过期
        now = utc_now()
        if row["expires_at"] < now:
            await _clear_state_internal(db, user_id)
            return None

        return UserSession(
            user_id=row["user_id"],
            state_type=SessionStateType(row["state_type"]),
            payload=safe_json_loads(row["payload"]),
            message_id=row["message_id"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )
    finally:
        await db.close()


async def set_state(session: UserSession, ttl_minutes: int = DEFAULT_TTL_MINUTES) -> UserSession:
    """设置用户会话状态。

    使用 INSERT OR REPLACE，新状态覆盖旧状态。

    Args:
        session: 会话状态
        ttl_minutes: 过期时间（分钟）

    Returns:
        设置后的 UserSession（含时间戳）
    """
    from datetime import timedelta

    now = utc_now()
    # 计算过期时间
    expires = parse_utc(now) + timedelta(minutes=ttl_minutes)
    expires_str = expires.strftime("%Y-%m-%dT%H:%M:%SZ")

    session.created_at = now
    session.expires_at = expires_str

    db = await create_connection()
    try:
        await db.execute(
            """
            INSERT OR REPLACE INTO user_states (user_id, state_type, payload, message_id, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session.user_id,
                session.state_type.value,
                safe_json_dumps(session.payload),
                session.message_id,
                session.created_at,
                session.expires_at,
            ),
        )
        await db.commit()
        logger.debug(f"设置用户 {session.user_id} 状态: {session.state_type.value}")
        return session
    finally:
        await db.close()


async def clear_state(user_id: str) -> bool:
    """清除用户会话状态。

    Args:
        user_id: 用户 QQ 号

    Returns:
        是否清除了状态
    """
    db = await create_connection()
    try:
        return await _clear_state_internal(db, user_id)
    finally:
        await db.close()


async def _clear_state_internal(db: aiosqlite.Connection, user_id: str) -> bool:
    """内部清除方法（复用连接）"""
    cursor = await db.execute(
        "DELETE FROM user_states WHERE user_id = ?", (user_id,)
    )
    await db.commit()
    return cursor.rowcount > 0


async def has_active_state(user_id: str) -> bool:
    """检查用户是否有活跃状态。

    Args:
        user_id: 用户 QQ 号

    Returns:
        是否有活跃状态
    """
    state = await get_state(user_id)
    return state is not None and state.state_type != SessionStateType.IDLE


async def cleanup_expired() -> int:
    """清理所有过期状态。

    Returns:
        清理的数量
    """
    db = await create_connection()
    try:
        now = utc_now()
        cursor = await db.execute(
            "DELETE FROM user_states WHERE expires_at < ?", (now,)
        )
        await db.commit()
        count = cursor.rowcount
        if count > 0:
            logger.info(f"清理了 {count} 条过期会话状态")
        return count
    finally:
        await db.close()

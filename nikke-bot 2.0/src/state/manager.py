"""
会话状态管理器

对外提供统一的状态管理 API。
"""

from typing import Optional
from src.state.types import UserSession, SessionStateType
from src.state.storage import (
    init_state_table,
    get_state,
    set_state,
    clear_state,
    has_active_state,
    cleanup_expired,
)


class StateManager:
    """用户会话状态管理器。

    用于多轮对话流程：
    - OCR 录入 → 确认 → 保存
    - 编辑装备流程
    """

    @staticmethod
    async def initialize():
        """初始化状态表"""
        await init_state_table()

    @staticmethod
    async def get(user_id: str) -> Optional[UserSession]:
        """获取用户会话状态"""
        return await get_state(user_id)

    @staticmethod
    async def set_confirm_state(
        user_id: str,
        payload: dict,
        message_id: Optional[str] = None,
        ttl_minutes: int = 5,
    ) -> UserSession:
        """设置等待确认状态。

        Args:
            user_id: 用户 QQ 号
            payload: 待确认数据（OCR 识别结果等）
            message_id: 关联消息 ID
            ttl_minutes: 超时时间

        Returns:
            UserSession
        """
        session = UserSession(
            user_id=user_id,
            state_type=SessionStateType.WAITING_CONFIRM,
            payload=payload,
            message_id=message_id,
        )
        return await set_state(session, ttl_minutes)

    @staticmethod
    async def set_edit_state(
        user_id: str,
        payload: dict,
        message_id: Optional[str] = None,
        ttl_minutes: int = 10,
    ) -> UserSession:
        """设置等待编辑状态。

        Args:
            user_id: 用户 QQ 号
            payload: 编辑数据
            message_id: 关联消息 ID
            ttl_minutes: 超时时间

        Returns:
            UserSession
        """
        session = UserSession(
            user_id=user_id,
            state_type=SessionStateType.WAITING_EDIT,
            payload=payload,
            message_id=message_id,
        )
        return await set_state(session, ttl_minutes)

    @staticmethod
    async def clear(user_id: str) -> bool:
        """清除用户状态"""
        return await clear_state(user_id)

    @staticmethod
    async def is_waiting_confirm(user_id: str) -> bool:
        """检查用户是否在等待确认"""
        state = await get_state(user_id)
        return state is not None and state.state_type == SessionStateType.WAITING_CONFIRM

    @staticmethod
    async def cleanup():
        """清理过期状态"""
        await cleanup_expired()

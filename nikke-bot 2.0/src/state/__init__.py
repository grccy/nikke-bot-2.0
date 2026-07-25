"""
状态管理层

提供：
- types: 状态类型定义
- storage: 持久化存储（SQLite）
- manager: 状态管理器 API
"""

from src.state.types import UserSession, SessionStateType
from src.state.storage import init_state_table, get_state, set_state, clear_state, cleanup_expired
from src.state.manager import StateManager

__all__ = [
    "UserSession",
    "SessionStateType",
    "StateManager",
    "init_state_table",
    "get_state",
    "set_state",
    "clear_state",
    "cleanup_expired",
]

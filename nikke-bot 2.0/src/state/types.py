"""
用户会话状态类型定义
"""

from enum import Enum
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class SessionStateType(str, Enum):
    """会话状态类型"""
    IDLE = "idle"                          # 空闲
    WAITING_CONFIRM = "waiting_confirm"    # 等待确认 OCR 识别结果
    WAITING_EDIT = "waiting_edit"          # 等待编辑装备


class UserSession(BaseModel):
    """用户当前会话状态。

    用于多轮对话流程（OCR 录入确认等）。
    每次用户只能有一个活跃状态。
    """

    user_id: str = Field(..., description="用户 QQ 号")
    state_type: SessionStateType = Field(default=SessionStateType.IDLE, description="当前状态类型")
    payload: Optional[dict[str, Any]] = Field(default=None, description="状态携带的数据")
    message_id: Optional[str] = Field(default=None, description="关联的 Bot 消息 ID")
    created_at: str = Field(default="", description="状态创建时间 (ISO 8601 UTC)")
    expires_at: str = Field(default="", description="状态过期时间 (ISO 8601 UTC)")

"""数据库行 → 用户模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DbUser(BaseModel):
    """users 表的行对象。"""

    qq_id: str = Field(..., description="QQ 号")
    nickname: str = Field(default="", description="QQ 昵称")
    preferences: str = Field(default="{}", description="JSON 偏好设置")
    created_at: Optional[datetime] = Field(default=None, description="注册时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")

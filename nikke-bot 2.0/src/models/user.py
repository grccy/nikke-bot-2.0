"""
用户模型

机器人用户。QQ 号是全局唯一标识。
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    """用户偏好设置"""

    default_sort: str = Field(default="newest", description="默认排序: newest / level_desc / score_desc")
    default_character: Optional[str] = Field(default=None, description="默认角色名")
    items_per_page: int = Field(default=5, ge=1, le=20, description="每页装备数")
    language: str = Field(default="zh-CN", description="语言偏好（未来多语言）")


class User(BaseModel):
    """机器人用户。

    QQ 号作为全局唯一标识。
    """

    qq_id: str = Field(..., description="QQ 号（主键）")
    nickname: str = Field(default="", description="QQ 昵称，显示用")
    preferences: UserPreferences = Field(
        default_factory=UserPreferences, description="用户偏好设置"
    )

    registered_at: Optional[datetime] = Field(default=None, description="首次使用时间")
    last_active_at: Optional[datetime] = Field(default=None, description="最后活跃时间")

    model_config = {
        "json_schema_extra": {
            "example": {
                "qq_id": "123456789",
                "nickname": "小明",
                "preferences": {"default_sort": "newest", "default_character": None, "items_per_page": 5, "language": "zh-CN"},
            }
        }
    }

"""
装备实例模型

用户拥有的一件具体装备实例。
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from .enums import EquipmentType, EquipmentSlot, Manufacturer, ScopeType
from .affix import Affix


class Equipment(BaseModel):
    """用户拥有的一件装备实例。

    约束：
        - 0 <= level <= 5
        - 0 <= len(affixes) <= 3
        - 所有 affix.quality 必须一致
        - name/type/slot/manufacturer 必须与 template_id 对应模板一致（Service 层保证）
        - scope == GROUP ⇔ group_id is not None
    """

    # ---- 归属 ----
    owner_id: str = Field(..., description="用户 QQ 号")
    template_id: int = Field(..., description="装备模板 ID")

    # ---- 装备属性（冗余自模板，保存时校验一致性）----
    name: str = Field(..., description="装备规范名称，如'朝圣者火力头盔'")
    type: EquipmentType = Field(..., description="装备类型")
    slot: EquipmentSlot = Field(..., description="装备部位")
    manufacturer: Manufacturer = Field(..., description="制造商")
    level: int = Field(default=0, ge=0, le=5, description="装备等级")

    # ---- 关联 ----
    character_id: Optional[int] = Field(default=None, description="所属角色 ID")
    affixes: list[Affix] = Field(default_factory=list, max_length=3, description="词条列表")

    # ---- 可见范围 ----
    scope: ScopeType = Field(default=ScopeType.PRIVATE, description="可见范围")
    group_id: Optional[str] = Field(default=None, description="群号（scope=group 时必填）")

    # ---- 数据库分配 ----
    id: Optional[int] = Field(default=None, description="数据库主键")

    # ---- 截图 ----
    screenshot_path: Optional[str] = Field(default=None, description="原始截图文件路径")

    # ---- 时间戳 ----
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="最后更新时间")

    # ---- 未来扩展 ----
    is_locked: bool = Field(default=False, description="装备保护标记，锁定后禁止删除")
    score: Optional[float] = Field(default=None, ge=0, le=100, description="装备评分")
    is_bis: Optional[bool] = Field(default=None, description="是否为毕业装备")

    @model_validator(mode="after")
    def validate_scope_group_consistency(self):
        """验证 scope 与 group_id 的一致性"""
        if self.scope == ScopeType.GROUP and not self.group_id:
            raise ValueError("scope=group 时 group_id 不能为空")
        if self.scope != ScopeType.GROUP and self.group_id is not None:
            raise ValueError(f"scope={self.scope.value} 时 group_id 必须为空")
        return self

    @model_validator(mode="after")
    def validate_affixes_quality_consistency(self):
        """验证所有词条品质一致"""
        if self.affixes:
            qualities = {a.quality for a in self.affixes}
            if len(qualities) > 1:
                raise ValueError(f"同一装备的词条品质必须一致: {qualities}")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "owner_id": "123456789",
                "template_id": 37,
                "name": "朝圣者火力头盔",
                "type": "attack",
                "slot": "head",
                "manufacturer": "pilgrim",
                "level": 3,
                "character_id": 1,
                "affixes": [],
                "scope": "private",
                "is_locked": False,
            }
        }
    }

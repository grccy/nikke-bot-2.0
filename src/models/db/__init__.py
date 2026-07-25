"""
DB 模型层

数据库行对象的 1:1 映射。Repository._row_to_* 返回这些模型。
与 models/ 下的领域模型区分：
- models/  = 领域模型（用于 Service 和 Handler）
- models/db/ = 数据库行模型（用于 Repository 返回）
"""

from .db_equipment import DbEquipment
from .db_affix import DbAffix
from .db_user import DbUser

__all__ = ["DbEquipment", "DbAffix", "DbUser"]

"""
DTO 模型层

数据传输对象：用于 Service 和 Handler 之间的输入/输出。
与 models/ 下的领域模型区分：
- models/    = 领域模型（持久化实体）
- models/db/  = 数据库行模型（Repository 返回）
- models/dto/ = 数据传输对象（API 输入/输出）
"""

from .create_equipment import CreateEquipmentDTO
from .create_affix import CreateAffixDTO
from .update_equipment import UpdateEquipmentDTO
from .parse_result import ParseResultDTO

__all__ = [
    "CreateEquipmentDTO",
    "CreateAffixDTO",
    "UpdateEquipmentDTO",
    "ParseResultDTO",
]

"""
OCR 识别记录模型

每次 OCR 调用的完整记录。
只追加、不修改，用于调试和持续优化 OCR 识别准确率。
"""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class OCRRecord(BaseModel):
    """OCR 识别记录 —— 用于调试、优化与历史追溯。

    只追加，不修改。可定期清理旧记录。
    """

    user_id: str = Field(..., description="发起识别的用户 QQ 号")
    image_path: str = Field(..., description="原始图片文件路径")
    ocr_engine: str = Field(..., description="OCR 引擎标识: baidu / tencent / paddle / deepseek")
    raw_text: str = Field(..., description="OCR 返回的原始文本，完整保留不做处理")

    parsed_data: Optional[dict[str, Any]] = Field(
        default=None, description="解析器输出的结构化数据"
    )
    is_success: bool = Field(default=False, description="是否成功解析出装备数据")
    is_confirmed: bool = Field(default=False, description="用户是否确认保存")
    confirmed_equipment_id: Optional[int] = Field(
        default=None, description="确认后生成的装备 ID"
    )
    error_message: Optional[str] = Field(default=None, description="失败原因")
    processing_time_ms: Optional[int] = Field(default=None, ge=0, description="处理耗时（毫秒）")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    id: Optional[int] = Field(default=None, description="数据库主键")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123456789",
                "image_path": "screenshots/abc123.png",
                "ocr_engine": "paddle",
                "raw_text": "朝圣者 火力型 头部 攻击力+15.6% ...",
                "is_success": True,
                "is_confirmed": True,
            }
        }
    }

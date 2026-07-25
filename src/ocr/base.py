"""
OCR 抽象基类 + OCRResult

TencentOCR 是当前唯一的 Provider。
未来增加新 OCR 引擎时，继承 BaseOCR 即可。
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    """OCR 识别结果 —— 所有 OCR Provider 的统一返回格式。"""

    text: str = Field(default="", description="OCR 识别出的完整文本")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="置信度")
    engine: str = Field(default="tencent", description="OCR 引擎标识")
    success: bool = Field(default=True, description="是否识别成功")
    cost_time_ms: int = Field(default=0, ge=0, description="耗时（毫秒）")
    error: Optional[str] = Field(default=None, description="错误信息（success=False 时）")


class BaseOCR(ABC):
    """OCR 引擎抽象基类。

    子类只需实现 recognize() 方法。
    异常必须在内部捕获，转换为 OCRResult(success=False, error=...)。
    """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """引擎标识"""
        ...

    @abstractmethod
    async def recognize(self, image_path: str) -> OCRResult:
        """识别图片中的文字。

        Args:
            image_path: 图片文件路径

        Returns:
            OCRResult
        """
        ...

"""
OCR 引擎抽象基类

所有 OCR 实现必须继承此基类，确保可替换性。
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseOCR(ABC):
    """OCR 引擎抽象基类。

    子类需要实现 recognize() 方法。
    """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """引擎标识，如 'paddle', 'baidu', 'tencent', 'deepseek'"""
        ...

    @abstractmethod
    async def recognize(self, image_path: str) -> "OCRResult":
        """识别图片中的文字。

        Args:
            image_path: 图片文件路径

        Returns:
            OCRResult 对象，包含原始文本和置信度
        """
        ...


class OCRResult:
    """OCR 识别结果"""

    def __init__(
        self,
        raw_text: str,
        confidence: float = 0.0,
        engine: str = "",
        error: Optional[str] = None,
    ):
        self.raw_text = raw_text
        self.confidence = max(0.0, min(1.0, confidence))
        self.engine = engine
        self.error = error

    @property
    def is_success(self) -> bool:
        return self.error is None and self.raw_text.strip() != ""

    def __repr__(self) -> str:
        return f"OCRResult(engine={self.engine}, confidence={self.confidence:.2f}, ok={self.is_success})"

"""
OCR 引擎层

提供可替换的 OCR 引擎：
- base: 抽象基类 + OCRResult
- paddle_ocr: PaddleOCR 实现
- deepseek_ocr: DeepSeek Vision 实现
- factory: 引擎工厂 + 快捷调用
"""

from src.ocr.base import BaseOCR, OCRResult
from src.ocr.factory import create_ocr_engine, quick_recognize

__all__ = [
    "BaseOCR",
    "OCRResult",
    "create_ocr_engine",
    "quick_recognize",
]

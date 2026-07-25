"""
OCR 引擎层

当前 Provider: TencentOCR（腾讯云通用印刷体识别 API）
未来增加新 Provider 时，继承 BaseOCR 并在 services/ocr_service.py 中切换即可。
"""

from src.ocr.base import BaseOCR, OCRResult
from src.ocr.tencent_ocr import TencentOCR, create_tencent_ocr_from_config

__all__ = [
    "BaseOCR",
    "OCRResult",
    "TencentOCR",
    "create_tencent_ocr_from_config",
]

"""
PaddleOCR 本地识别引擎
"""

import logging
from src.ocr.base import BaseOCR, OCRResult

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
    _PADDLE_AVAILABLE = True
except ImportError:
    _PADDLE_AVAILABLE = False


class PaddleOCREngine(BaseOCR):
    """PaddleOCR 本地识别引擎"""

    @property
    def engine_name(self) -> str:
        return "paddle"

    def __init__(self):
        if not _PADDLE_AVAILABLE:
            raise ImportError("PaddleOCR 未安装，请执行: pip install paddleocr paddlepaddle")
        self._ocr = PaddleOCR(lang="ch", use_angle_cls=True, show_log=False)

    async def recognize(self, image_path: str) -> OCRResult:
        """识别图片文字"""
        try:
            raw = self._ocr.ocr(image_path, cls=True)

            if not raw or not raw[0]:
                return OCRResult(
                    raw_text="",
                    confidence=0.0,
                    engine=self.engine_name,
                    error="PaddleOCR 未检测到文字",
                )

            # 提取所有识别文本
            texts = []
            confidences = []
            for item in raw[0]:
                text = item[1][0]
                conf = item[1][1]
                texts.append(text)
                confidences.append(conf)

            full_text = "\n".join(texts)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

            return OCRResult(
                raw_text=full_text,
                confidence=round(avg_conf, 4),
                engine=self.engine_name,
            )

        except Exception as e:
            logger.error(f"PaddleOCR 识别失败: {e}")
            return OCRResult(
                raw_text="",
                confidence=0.0,
                engine=self.engine_name,
                error=str(e),
            )

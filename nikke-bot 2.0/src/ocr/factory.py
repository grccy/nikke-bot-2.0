"""
OCR 引擎工厂

根据配置选择合适的 OCR 引擎。
"""

import logging
from typing import Optional

from src.config import get_config
from src.ocr.base import BaseOCR, OCRResult

logger = logging.getLogger(__name__)


async def create_ocr_engine(engine_name: Optional[str] = None) -> BaseOCR:
    """创建 OCR 引擎实例。

    Args:
        engine_name: 引擎名称。'paddle' / 'baidu' / 'tencent' / 'deepseek' / 'auto'
                     默认从配置读取。

    Returns:
        BaseOCR 实例
    """
    if engine_name is None:
        engine_name = get_config().ocr.engine

    cfg = get_config().ocr

    # 尝试 PaddleOCR
    if engine_name in ("paddle", "auto"):
        try:
            from src.ocr.paddle_ocr import PaddleOCREngine
            return PaddleOCREngine()
        except ImportError:
            if engine_name == "paddle":
                raise RuntimeError("PaddleOCR 未安装，请执行: pip install paddleocr paddlepaddle")
            logger.info("PaddleOCR 未安装，尝试 DeepSeek 兜底")

    # 尝试 DeepSeek Vision
    if engine_name in ("deepseek", "auto"):
        if cfg.deepseek_api_key and "your-key" not in cfg.deepseek_api_key:
            from src.ocr.deepseek_ocr import DeepSeekOCREngine
            return DeepSeekOCREngine(
                api_key=cfg.deepseek_api_key,
                base_url=cfg.deepseek_base_url,
                model=cfg.deepseek_model,
            )
        else:
            if engine_name == "deepseek":
                raise RuntimeError("DeepSeek API Key 未配置")

    # 无可用引擎
    raise RuntimeError(
        f"无可用的 OCR 引擎。请安装 PaddleOCR 或配置 DeepSeek API Key。"
    )


async def quick_recognize(image_path: str) -> OCRResult:
    """快速识别图片（自动选择引擎）。

    Args:
        image_path: 图片路径

    Returns:
        OCRResult
    """
    engine = await create_ocr_engine()
    return await engine.recognize(image_path)

"""
OCR 识别服务

负责：
- 接收图片 → OCR → 保存记录
- 不负责解析装备数据（由 ParserService 负责）
"""

import time
import logging
from typing import Optional

from src.ocr.factory import create_ocr_engine
from src.ocr.base import OCRResult
from src.database.repositories.ocr_record_repo import OCRRecordRepository
from src.models.ocr_record import OCRRecord

logger = logging.getLogger(__name__)


class OCRService:
    """OCR 识别服务"""

    def __init__(self):
        self.record_repo = OCRRecordRepository()

    async def recognize(
        self,
        image_path: str,
        user_id: Optional[str] = None,
        engine_name: Optional[str] = None,
    ) -> tuple[OCRResult, OCRRecord]:
        """识别图片并保存记录。

        Args:
            image_path: 图片路径
            user_id: 用户 QQ 号（可选）
            engine_name: 引擎名称（可选）

        Returns:
            (OCRResult, OCRRecord)
        """
        start_time = time.time()

        # 获取引擎并识别
        engine = await create_ocr_engine(engine_name)
        result = await engine.recognize(image_path)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 保存 OCR 记录
        record = OCRRecord(
            user_id=user_id or "",
            image_path=image_path,
            ocr_engine=result.engine,
            raw_text=result.raw_text,
            confidence=result.confidence,
            is_success=result.is_success,
            is_confirmed=False,
            error_message=result.error,
            processing_time_ms=elapsed_ms,
        )

        async with self.record_repo as repo:
            record = await repo.insert(record)

        logger.info(
            f"OCR 识别完成: engine={result.engine}, "
            f"confidence={result.confidence:.2f}, "
            f"elapsed={elapsed_ms}ms"
        )

        return result, record

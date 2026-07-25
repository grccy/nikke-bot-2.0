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
    """OCR 识别服务。

    使用方式:
        service = OCRService(record_repo=OCRRecordRepository(db))
        result, record = await service.recognize("image.png", user_id="123")
    """

    def __init__(self, record_repo: OCRRecordRepository):
        self.record_repo = record_repo

    async def recognize(
        self,
        image_path: str,
        user_id: Optional[str] = None,
        engine_name: Optional[str] = None,
    ) -> tuple[OCRResult, OCRRecord]:
        """识别图片并保存记录。"""
        start_time = time.time()

        engine = await create_ocr_engine(engine_name)
        result = await engine.recognize(image_path)

        elapsed_ms = int((time.time() - start_time) * 1000)

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

        record = await self.record_repo.insert(record)

        logger.info(
            f"OCR 识别完成: engine={result.engine}, "
            f"confidence={result.confidence:.2f}, "
            f"elapsed={elapsed_ms}ms"
        )

        return result, record

"""
OCR 识别服务

负责：
- 接收图片 → 腾讯云 OCR → 保存 OCRRecord
- 不负责解析装备数据（由 Parser 层负责）
"""

import time
import logging
from typing import Optional

from src.ocr.base import OCRResult
from src.ocr.tencent_ocr import TencentOCR
from src.database.repositories.ocr_record_repo import OCRRecordRepository
from src.models.ocr_record import OCRRecord

logger = logging.getLogger(__name__)


class OCRService:
    """OCR 识别服务。

    使用方式:
        ocr = TencentOCR(...)
        repo = OCRRecordRepository(db)
        service = OCRService(ocr=ocr, record_repo=repo)
        result = await service.process_image(image_path, user_id="123")
    """

    def __init__(self, ocr: TencentOCR, record_repo: OCRRecordRepository):
        self._ocr = ocr
        self.record_repo = record_repo

    async def process_image(
        self,
        image_path: str,
        user_id: Optional[str] = None,
    ) -> OCRResult:
        """识别图片并保存 OCR 记录。

        Args:
            image_path: 图片文件路径
            user_id: 用户 QQ 号（可选）

        Returns:
            OCRResult
        """
        # 调用 OCR
        result = await self._ocr.recognize(image_path)

        # 保存记录
        record = OCRRecord(
            user_id=user_id or "",
            image_path=image_path,
            ocr_engine=result.engine,
            raw_text=result.text,
            confidence=result.confidence,
            is_success=result.success,
            is_confirmed=False,
            error_message=result.error,
            processing_time_ms=result.cost_time_ms,
        )
        await self.record_repo.insert(record)

        logger.info(
            f"OCR 完成: engine={result.engine}, "
            f"success={result.success}, "
            f"elapsed={result.cost_time_ms}ms"
        )

        return result

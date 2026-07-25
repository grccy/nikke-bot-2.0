"""
OCR 记录 Repository

提供 ocr_records 表的写入和查询操作。
只追加、不修改，用于调试和优化。
"""

import aiosqlite
from typing import Optional

from src.database.repositories import BaseRepository
from src.models.ocr_record import OCRRecord
from src.utils.time_utils import utc_now
from src.utils.json_utils import safe_json_dumps, safe_json_loads


class OCRRecordRepository(BaseRepository):
    """OCR 识别记录数据访问层。"""

    async def insert(self, record: OCRRecord) -> OCRRecord:
        """插入 OCR 记录。"""
        now = utc_now()
        parsed_json = (
            safe_json_dumps(record.parsed_data) if record.parsed_data else None
        )

        cursor = await self.db.execute(
            """
            INSERT INTO ocr_records (
                user_id, image_path, ocr_engine, raw_text, confidence,
                parser_result, is_success, is_confirmed,
                confirmed_equipment_id, error_message,
                processing_time_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.user_id,
                record.image_path,
                record.ocr_engine,
                record.raw_text,
                record.confidence,
                parsed_json,
                1 if record.is_success else 0,
                1 if record.is_confirmed else 0,
                record.confirmed_equipment_id,
                record.error_message,
                record.processing_time_ms,
                now,
            ),
        )
        await self.db.commit()

        record.id = cursor.lastrowid
        record.created_at = now  # type: ignore
        return record

    async def update_confirmation(
        self, record_id: int, confirmed: bool, equipment_id: Optional[int] = None
    ) -> bool:
        """更新 OCR 记录的确认状态。"""
        cursor = await self.db.execute(
            """UPDATE ocr_records SET
                 is_confirmed = ?, confirmed_equipment_id = ?
               WHERE id = ?""",
            (1 if confirmed else 0, equipment_id, record_id),
        )
        await self.db.commit()
        return cursor.rowcount > 0

    async def get_by_user(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> list[OCRRecord]:
        """查询用户的 OCR 记录。"""
        cursor = await self.db.execute(
            _SELECT_OCR + " WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [self._row_to_record(r) for r in rows]

    async def get_failed_records(self, limit: int = 50) -> list[OCRRecord]:
        """查询识别失败的 OCR 记录（用于调试和优化）。"""
        cursor = await self.db.execute(
            _SELECT_OCR + " WHERE is_success = 0 ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()
        return [self._row_to_record(r) for r in rows]

    def _row_to_record(self, row: aiosqlite.Row) -> OCRRecord:
        """将数据库行转换为 OCRRecord 模型"""
        parsed_raw = row["parser_result"]
        return OCRRecord(
            id=row["id"],
            user_id=row["user_id"] or "",
            image_path=row["image_path"],
            ocr_engine=row["ocr_engine"],
            raw_text=row["raw_text"],
            confidence=row["confidence"],
            parsed_data=safe_json_loads(parsed_raw) if parsed_raw else None,
            is_success=bool(row["is_success"]),
            is_confirmed=bool(row["is_confirmed"]),
            confirmed_equipment_id=row["confirmed_equipment_id"],
            error_message=row["error_message"],
            processing_time_ms=row["processing_time_ms"],
            created_at=row["created_at"],
        )


_SELECT_OCR = (
    "SELECT id, user_id, image_path, ocr_engine, raw_text, confidence, "
    "parser_result, is_success, is_confirmed, "
    "confirmed_equipment_id, error_message, "
    "processing_time_ms, created_at FROM ocr_records"
)

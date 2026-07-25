"""
DeepSeek Vision API 识别引擎（兜底方案）
"""

import base64
import json
import re
import logging
from pathlib import Path

from openai import AsyncOpenAI

from src.ocr.base import BaseOCR, OCRResult

logger = logging.getLogger(__name__)

# 精简提示词
VISION_PROMPT = """你是 NIKKE T10 装备词条识别器。提取截图中的所有文字，特别是：
- 装备类型（火力型/防御型/支援型）
- 装备部位（头/身/臂/腿）
- 制造商（朝圣者/极乐净土/米西利斯/泰特拉/反常）
- 词条属性名和数值（如"攻击力 +15.6%"）
- 品质标记（金/紫/蓝）

只需要返回截图中的所有文字内容，不需要任何其他解释。"""


class DeepSeekOCREngine(BaseOCR):
    """DeepSeek Vision API 识别引擎"""

    @property
    def engine_name(self) -> str:
        return "deepseek"

    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def recognize(self, image_path: str) -> OCRResult:
        """调用 Vision API 识别图片文字"""
        try:
            image_b64 = self._encode_image(image_path)

            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": VISION_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                },
                            },
                            {"type": "text", "text": "提取这件T10装备的所有文字内容"},
                        ],
                    },
                ],
                temperature=0.1,
                max_tokens=800,
            )

            raw_text = response.choices[0].message.content or ""
            return OCRResult(
                raw_text=raw_text,
                confidence=0.85,
                engine=self.engine_name,
            )

        except Exception as e:
            logger.error(f"DeepSeek OCR 识别失败: {e}")
            return OCRResult(
                raw_text="",
                confidence=0.0,
                engine=self.engine_name,
                error=str(e),
            )

    @staticmethod
    def _encode_image(image_path: str) -> str:
        """读取图片并转为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

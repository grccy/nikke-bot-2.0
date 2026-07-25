"""
腾讯云 OCR Provider

使用腾讯云通用印刷体识别 API（GeneralBasicOCR）。
异常全部内部捕获，不向上抛裸异常。

依赖: pip install tencentcloud-sdk-python
"""

import base64
import logging
import time
from pathlib import Path
from typing import Optional

from src.config import get_config
from src.ocr.base import BaseOCR, OCRResult

logger = logging.getLogger(__name__)

# 腾讯云 SDK 可选导入
try:
    from tencentcloud.common import credential
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
        TencentCloudSDKException,
    )
    from tencentcloud.ocr.v20181119 import ocr_client, models

    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False


class TencentOCR(BaseOCR):
    """腾讯云 OCR 引擎。

    使用方式:
        ocr = TencentOCR(secret_id="...", secret_key="...", region="ap-guangzhou")
        result = await ocr.recognize("screenshot.png")
    """

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        region: str = "ap-guangzhou",
    ):
        if not _SDK_AVAILABLE:
            raise ImportError(
                "腾讯云 OCR SDK 未安装。请执行: pip install tencentcloud-sdk-python"
            )
        if not secret_id or not secret_key:
            raise ValueError("Tencent OCR SecretId / SecretKey 不能为空")

        self._secret_id = secret_id
        self._secret_key = secret_key
        self._region = region

        cred = credential.Credential(secret_id, secret_key)
        self._client = ocr_client.OcrClient(cred, region)

    @property
    def engine_name(self) -> str:
        return "tencent"

    async def recognize(self, image_path: str) -> OCRResult:
        """调用腾讯云 GeneralBasicOCR 识别图片。

        Args:
            image_path: 图片文件路径

        Returns:
            OCRResult（异常时 success=False）
        """
        start = time.time()

        # 1. 读取图片 → Base64
        try:
            image_b64 = _read_image_base64(image_path)
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            return OCRResult(
                success=False,
                engine=self.engine_name,
                cost_time_ms=elapsed,
                error=f"图片读取失败: {e}",
            )

        # 2. 调用腾讯云 OCR
        req = models.GeneralBasicOCRRequest()
        req.ImageBase64 = image_b64

        try:
            resp = self._client.GeneralBasicOCR(req)
            elapsed = int((time.time() - start) * 1000)
        except TencentCloudSDKException as e:
            elapsed = int((time.time() - start) * 1000)
            logger.error(f"腾讯云 OCR API 错误: code={e.code}, message={e.message}")
            return OCRResult(
                success=False,
                engine=self.engine_name,
                cost_time_ms=elapsed,
                error=f"API 错误 [{e.code}]: {e.message}",
            )
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            logger.error(f"腾讯云 OCR 调用异常: {e}")
            return OCRResult(
                success=False,
                engine=self.engine_name,
                cost_time_ms=elapsed,
                error=f"网络/未知错误: {e}",
            )

        # 3. 解析返回文本
        texts: list[str] = []
        total_conf = 0.0
        if resp.TextDetections:
            for item in resp.TextDetections:  # type: ignore[attr-defined]
                texts.append(item.DetectedText or "")
                total_conf += item.Confidence / 100.0 if item.Confidence else 0.0

        full_text = "\n".join(texts)
        avg_conf = round(total_conf / len(texts), 4) if texts else 0.0

        logger.info(
            f"腾讯云 OCR 完成: {len(texts)} 行文字, "
            f"confidence={avg_conf:.2f}, elapsed={elapsed}ms"
        )

        return OCRResult(
            text=full_text,
            confidence=avg_conf,
            engine=self.engine_name,
            success=True,
            cost_time_ms=elapsed,
        )


def _read_image_base64(path: str) -> str:
    """读取图片并转为 Base64 字符串"""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def create_tencent_ocr_from_config() -> TencentOCR:
    """从全局配置创建 TencentOCR 实例。"""
    cfg = get_config().ocr
    return TencentOCR(
        secret_id=cfg.tencent_secret_id,
        secret_key=cfg.tencent_secret_key,
        region=cfg.tencent_region,
    )

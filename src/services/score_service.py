"""
词条阶级计算

根据 data/tier.json 配置，计算词条数值对应的阶级。
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def calculate_tier(quality: str, value: float) -> int:
    """根据品质和数值计算词条阶级。

    Args:
        quality: 词条品质 (blue/purple/gold)
        value: 词条数值

    Returns:
        阶级 1-15。如果无法匹配则返回 1。
    """
    tier_config = _load_tier_config()
    if tier_config is None:
        return 1

    tiers = tier_config.get("tiers", {})
    quality_tiers = tiers.get(quality)
    if quality_tiers is None:
        return 1

    ranges = quality_tiers.get("ranges", [])
    for entry in ranges:
        if entry["min"] <= value <= entry["max"]:
            return entry["tier"]

    # 超出所有范围：返回最高或最低阶级
    logger.warning(f"无法匹配阶级: quality={quality}, value={value}")
    return 1


_tier_cache: Optional[dict] = None
_tier_version: Optional[str] = None


def _load_tier_config() -> Optional[dict]:
    """加载 tier.json 配置（带缓存）"""
    global _tier_cache

    if _tier_cache is not None:
        return _tier_cache

    try:
        from src.config import get_config
        tier_path = get_config().data_dir / "tier.json"
        with open(tier_path, "r", encoding="utf-8") as f:
            _tier_cache = json.load(f)
        return _tier_cache
    except FileNotFoundError:
        logger.error("tier.json 文件不存在")
        return None
    except json.JSONDecodeError:
        logger.error("tier.json 格式错误")
        return None


def get_tier_config_version() -> Optional[str]:
    """获取当前 tier.json 的版本号"""
    config = _load_tier_config()
    if config:
        return config.get("version")
    return None


def reload_tier_config():
    """重新加载 tier.json（热重载）"""
    global _tier_cache
    _tier_cache = None
    _load_tier_config()
    logger.info(f"tier.json 已重新加载，版本: {get_tier_config_version()}")

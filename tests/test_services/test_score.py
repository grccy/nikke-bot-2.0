"""
测试词条阶级计算
"""

import json
import tempfile
from pathlib import Path

import pytest

# Tier 计算需要 tier.json，测试前 Mock 配置
from src.config import _config, AppConfig, DatabaseConfig


@pytest.fixture
def mock_tier_json(monkeypatch, tmp_path):
    """创建临时 tier.json 用于测试"""
    tier_data = {
        "version": "2.1.0",
        "tiers": {
            "blue": {
                "ranges": [
                    {"min": 0, "max": 5.99, "tier": 1},
                    {"min": 6, "max": 10.99, "tier": 5},
                    {"min": 11, "max": 99.99, "tier": 10},
                ]
            },
            "gold": {
                "ranges": [
                    {"min": 0, "max": 15.99, "tier": 5},
                    {"min": 16, "max": 99.99, "tier": 12},
                ]
            },
        },
    }
    tier_path = tmp_path / "tier.json"
    with open(tier_path, "w", encoding="utf-8") as f:
        json.dump(tier_data, f)

    # Mock 配置
    test_config = AppConfig(
        database=DatabaseConfig(path=tmp_path / "test.db"),
    )
    test_config.data_dir = tmp_path
    monkeypatch.setattr("src.config.get_config", lambda: test_config)

    # 清除缓存
    import src.services.score_service as ss
    ss._tier_cache = None

    yield tier_path


def test_calculate_blue_tier(mock_tier_json):
    """蓝色品质词条阶级计算"""
    from src.services.score_service import calculate_tier

    assert calculate_tier("blue", 3.0) == 1
    assert calculate_tier("blue", 8.0) == 5
    assert calculate_tier("blue", 15.0) == 10


def test_calculate_gold_tier(mock_tier_json):
    """金色品质词条阶级计算"""
    from src.services.score_service import calculate_tier

    assert calculate_tier("gold", 10.0) == 5
    assert calculate_tier("gold", 20.0) == 12


def test_unknown_quality_defaults_to_1(mock_tier_json):
    """未知品质默认返回 1"""
    from src.services.score_service import calculate_tier

    assert calculate_tier("unknown", 10.0) == 1

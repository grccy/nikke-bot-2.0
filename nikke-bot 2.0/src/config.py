"""
全局配置管理

从环境变量 + .env 文件加载配置，提供统一访问入口。
所有模块通过此模块获取配置，不直接读环境变量。
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class DatabaseConfig:
    path: Path = field(default_factory=lambda: PROJECT_ROOT / "database" / "nikke.db")


@dataclass
class OCRConfig:
    engine: str = "auto"          # paddle / baidu / tencent / deepseek / auto
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    baidu_app_id: str = ""
    baidu_api_key: str = ""
    baidu_secret_key: str = ""
    tencent_secret_id: str = ""
    tencent_secret_key: str = ""


@dataclass
class BotConfig:
    superusers: list[str] = field(default_factory=list)
    command_start: list[str] = field(default_factory=lambda: ["/"])
    nickname: list[str] = field(default_factory=lambda: ["妮姬助手"])
    onebot_ws_url: str = "ws://127.0.0.1:8080/onebot/v11/ws"


@dataclass
class LogConfig:
    level: str = "INFO"
    file: Optional[str] = "logs/nikke_bot.log"


@dataclass
class AppConfig:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    bot: BotConfig = field(default_factory=BotConfig)
    log: LogConfig = field(default_factory=LogConfig)

    # ---- 路径 ----
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    screenshots_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "screenshots")
    assets_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "assets")
    exports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "exports")


_config: Optional[AppConfig] = None


def _load_from_env() -> AppConfig:
    """从环境变量加载配置"""
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")

    return AppConfig(
        database=DatabaseConfig(
            path=Path(os.getenv("DATABASE_PATH", "database/nikke.db")),
        ),
        ocr=OCRConfig(
            engine=os.getenv("OCR_ENGINE", "auto"),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            baidu_app_id=os.getenv("BAIDU_OCR_APP_ID", ""),
            baidu_api_key=os.getenv("BAIDU_OCR_API_KEY", ""),
            baidu_secret_key=os.getenv("BAIDU_OCR_SECRET_KEY", ""),
            tencent_secret_id=os.getenv("TENCENT_OCR_SECRET_ID", ""),
            tencent_secret_key=os.getenv("TENCENT_OCR_SECRET_KEY", ""),
        ),
        bot=BotConfig(
            superusers=_parse_json_list(os.getenv("BOT_SUPERUSERS", "[]")),
            command_start=_parse_json_list(os.getenv("BOT_COMMAND_START", '["/"]')),
            nickname=_parse_json_list(os.getenv("BOT_NICKNAME", '["妮姬助手"]')),
            onebot_ws_url=os.getenv("ONEBOT_WS_URL", "ws://127.0.0.1:8080/onebot/v11/ws"),
        ),
        log=LogConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=os.getenv("LOG_FILE", "logs/nikke_bot.log"),
        ),
    )


def _parse_json_list(raw: str) -> list[str]:
    import json as _json
    try:
        result = _json.loads(raw)
        if isinstance(result, list):
            return result
        return []
    except (_json.JSONDecodeError, TypeError):
        return []


def get_config() -> AppConfig:
    """获取全局配置单例"""
    global _config
    if _config is None:
        _config = _load_from_env()
    return _config


def reload_config() -> AppConfig:
    """重新加载配置（用于热重载）"""
    global _config
    _config = _load_from_env()
    return _config

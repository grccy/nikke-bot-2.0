"""
NIKKE T10 装备词条管理 QQ 机器人 v2.1
基于 NoneBot2 + OneBot v11 适配器

启动流程：
1. 加载环境变量
2. 执行数据库迁移
3. 加载静态数据（角色、装备模板）
4. 初始化状态管理表
5. 注册 NoneBot 适配器
6. 加载插件
7. 启动
"""

import asyncio
import logging
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

from src.config import get_config


def setup_logging():
    """配置日志"""
    cfg = get_config().log

    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if cfg.file:
        from pathlib import Path
        log_path = Path(cfg.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(cfg.file, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, cfg.level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        handlers=handlers,
    )


async def startup():
    """启动初始化"""
    setup_logging()
    logger = logging.getLogger("nikke_bot")
    logger.info("NIKKE 装备管理机器人 v2.1 正在启动...")

    # 1. 执行数据库迁移
    from src.database.migrations import run_migrations
    logger.info("执行数据库迁移...")
    await run_migrations()

    # 2. 初始化状态管理表
    from src.state.storage import init_state_table
    await init_state_table()

    # 3. 加载静态数据
    from src.services.data_loader import load_all
    await load_all()

    logger.info("启动完成，等待消息...")


def main():
    """主入口"""
    nonebot.init()

    # 注册驱动和适配器
    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)

    # 注册启动钩子
    @driver.on_startup
    async def _startup():
        await startup()

    # 加载插件
    nonebot.load_plugins("src/bot/plugins")

    nonebot.run()


if __name__ == "__main__":
    main()

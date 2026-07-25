"""
NIKKE T10 装备词条管理 QQ 机器人 v2.1
基于 NoneBot2 + OneBot v11 适配器

启动流程：
1. 加载环境变量
2. 初始化 DatabaseManager
3. 执行数据库迁移
4. 加载静态数据（角色、装备模板）
5. 初始化状态管理表
6. 注册 NoneBot 适配器
7. 加载插件
8. 启动
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

    # 1. 初始化 DatabaseManager — startup 内部自动跑 migration

    # 2. 注入 DatabaseManager 给 Handler 层
    from src.bot.plugins.equipment.handlers import set_db_manager
    set_db_manager(db_manager)

    # 3. 初始化状态管理表
    from src.state.storage import init_state_table
    await init_state_table()

    # 4. 加载静态数据
    from src.services.data_loader import load_all
    await load_all()

    # 5. 保存 db_manager 引用供 shutdown 使用
    global _global_db_manager
    _global_db_manager = db_manager

    logger.info("启动完成，等待消息...")


_global_db_manager = None


def main():
    """主入口"""
    nonebot.init()

    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)

    @driver.on_startup
    async def _startup():
        await startup()

    @driver.on_shutdown
    async def _shutdown():
        global _global_db_manager
        if _global_db_manager:
            await _global_db_manager.shutdown()
            logging.getLogger("nikke_bot").info("数据库连接已关闭")

    nonebot.load_plugins("src/bot/plugins")
    nonebot.run()


if __name__ == "__main__":
    main()

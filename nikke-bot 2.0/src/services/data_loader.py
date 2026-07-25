"""
数据加载服务

启动时加载静态数据（角色、装备模板）到数据库。
"""

import json
import logging
from pathlib import Path
from typing import Optional

from src.config import get_config
from src.database.repositories.character_repo import CharacterRepository
from src.database.repositories.template_repo import TemplateRepository
from src.models.character import Character
from src.models.equipment_template import EquipmentTemplate
from src.models.enums import EquipmentType, EquipmentSlot, Manufacturer

logger = logging.getLogger(__name__)


async def load_characters(data_dir: Optional[Path] = None) -> int:
    """从 data/characters.json 加载角色到数据库。

    Args:
        data_dir: 数据目录路径，默认使用配置

    Returns:
        加载的角色数量

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 格式错误
    """
    if data_dir is None:
        data_dir = get_config().data_dir

    char_path = data_dir / "characters.json"
    with open(char_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    if not isinstance(raw_list, list):
        raise ValueError("characters.json 必须是数组格式")

    loaded = 0
    async with CharacterRepository() as repo:
        for item in raw_list:
            try:
                mfr = item.get("manufacturer")
                character = Character(
                    name=item["name"],
                    aliases=item.get("aliases", []),
                    rarity=item.get("rarity"),
                    element=item.get("element"),
                    weapon_type=item.get("weapon_type"),
                    burst_level=item.get("burst_level"),
                    manufacturer=Manufacturer(mfr) if mfr else None,
                )
                await repo.upsert(character)
                loaded += 1
            except Exception as e:
                logger.warning(f"跳过无效角色数据 {item.get('name', '?')}: {e}")

    logger.info(f"角色加载完成: {loaded}/{len(raw_list)}")
    return loaded


async def load_equipment_templates(data_dir: Optional[Path] = None) -> int:
    """从 data/equipment_templates.json 加载装备模板到数据库。

    Args:
        data_dir: 数据目录路径，默认使用配置

    Returns:
        加载的模板数量
    """
    if data_dir is None:
        data_dir = get_config().data_dir

    tmpl_path = data_dir / "equipment_templates.json"
    with open(tmpl_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    if not isinstance(raw_list, list):
        raise ValueError("equipment_templates.json 必须是数组格式")

    loaded = 0
    async with TemplateRepository() as repo:
        for item in raw_list:
            try:
                template = EquipmentTemplate(
                    name=item["name"],
                    type=EquipmentType(item["type"]),
                    slot=EquipmentSlot(item["slot"]),
                    manufacturer=Manufacturer(item["manufacturer"]),
                    rarity=item.get("rarity"),
                    icon_name=item.get("icon_name"),
                )
                await repo.upsert(template)
                loaded += 1
            except Exception as e:
                logger.warning(f"跳过无效模板数据 {item.get('name', '?')}: {e}")

    logger.info(f"装备模板加载完成: {loaded}/{len(raw_list)}")
    return loaded


async def load_all():
    """启动时加载全部静态数据。

    使用 INSERT OR IGNORE 策略，已存在的数据不会重复插入。
    """
    logger.info("正在加载静态数据...")

    try:
        chars = await load_characters()
        logger.info(f"  角色: {chars} 条")
    except Exception as e:
        logger.error(f"  角色加载失败: {e}")

    try:
        templates = await load_equipment_templates()
        logger.info(f"  装备模板: {templates} 条")
    except Exception as e:
        logger.error(f"  装备模板加载失败: {e}")

    logger.info("静态数据加载完成")

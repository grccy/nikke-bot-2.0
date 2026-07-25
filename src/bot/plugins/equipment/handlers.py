"""装备管理插件 — NoneBot Handler

所有 Handler 通过工厂函数获取 Service 实例，
Repository 依赖由 DatabaseManager 统一注入。
"""

import os
import aiohttp
import logging
from pathlib import Path

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import (
    Bot, MessageEvent, Message, MessageSegment,
)
from nonebot.params import CommandArg
from nonebot.rule import Rule

from src.services.equipment_service import EquipmentService
from src.services.ocr_service import OCRService
from src.services.parser_service import ParserService
from src.state.manager import StateManager
from src.state.types import SessionStateType
from src.database.repositories.user_repo import UserRepository
from src.database.repositories.character_repo import CharacterRepository
from src.database.repositories.template_repo import TemplateRepository
from src.database.repositories.equipment_repo import EquipmentRepository
from src.database.repositories.affix_repo import AffixRepository
from src.database.repositories.ocr_record_repo import OCRRecordRepository
from src.ocr.tencent_ocr import create_tencent_ocr_from_config
from src.models.enums import Manufacturer, EquipmentType, EquipmentSlot
from src.models.dto.create_equipment import CreateEquipmentDTO, CreateAffixDTO
from src.config import get_config

logger = logging.getLogger(__name__)

SCREENSHOTS_DIR = get_config().screenshots_dir

# ============================================================
# 服务工厂函数 — 每次请求时从 DatabaseManager 获取连接，创建 Service
# ============================================================

from src.database import DatabaseManager

_db_manager: "DatabaseManager | None" = None


def set_db_manager(mgr: "DatabaseManager"):
    """由 bot.py 在启动时调用，注入全局 DatabaseManager。"""
    global _db_manager
    _db_manager = mgr


def _get_db():
    if _db_manager is None:
        raise RuntimeError("DatabaseManager 未初始化")
    return _db_manager.connection


def _make_equip_service() -> EquipmentService:
    db = _get_db()
    return EquipmentService(
        equip_repo=EquipmentRepository(db),
        affix_repo=AffixRepository(db),
        template_repo=TemplateRepository(db),
    )


def _make_ocr_service() -> OCRService:
    ocr = create_tencent_ocr_from_config()
    return OCRService(ocr=ocr, record_repo=OCRRecordRepository(_get_db()))


def _make_parser_service() -> ParserService:
    return ParserService()


state_mgr = StateManager()


# ============================================================
# 辅助
# ============================================================

async def _ensure_user_registered(user_id: str, nickname: str = ""):
    """确保用户已注册（不存在则创建）"""
    from src.models.user import User
    repo = UserRepository(_get_db())
    exists = await repo.exists(user_id)
    if not exists:
        user = User(qq_id=user_id, nickname=nickname)
        await repo.upsert(user)
        logger.info(f"新用户注册: {user_id}")
    else:
        user = User(qq_id=user_id, nickname=nickname)
        await repo.upsert(user)


# ============================================================
# /装备录入 — OCR 录入流程
# ============================================================

record_cmd = on_command("装备录入", aliases={"录入装备", "词条录入", "录入词条"}, priority=5)


@record_cmd.handle()
async def handle_record(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    user_id = str(event.user_id)
    group_id = str(event.group_id) if hasattr(event, "group_id") and event.group_id else None

    await _ensure_user_registered(user_id, event.sender.nickname or "")

    # 检查图片
    img_urls = []
    for seg in event.message:
        if seg.type == "image":
            img_urls.append(seg.data.get("url", ""))

    if not img_urls:
        await record_cmd.finish(
            "请发送装备截图 + /装备录入\n\n"
            "用法：先发送一张 T10 装备词条界面截图，然后发送 /装备录入"
        )

    # 下载图片
    img_url = img_urls[0]
    img_path = SCREENSHOTS_DIR / f"{user_id}_{event.message_id}.png"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as resp:
                with open(img_path, "wb") as f:
                    f.write(await resp.read())
    except Exception as e:
        logger.error(f"图片下载失败: {e}")
        await record_cmd.finish("❌ 图片下载失败，请重试。")

    # OCR 识别
    await record_cmd.send("🔍 正在识别装备信息...")
    ocr_svc = _make_ocr_service()
    ocr_result = await ocr_svc.process_image(str(img_path), user_id)

    if not ocr_result.success:
        await record_cmd.finish(
            f"❌ OCR 识别失败：{ocr_result.error or '未检测到文字'}\n请重发清晰截图。"
        )

    # 解析文本
    parser_svc = _make_parser_service()
    parsed = await parser_svc.parse(ocr_result.text)
    logger.info(
        f"解析结果: mfr={parsed.manufacturer}, type={parsed.type}, "
        f"slot={parsed.slot}, affixes={len(parsed.affixes)}"
    )

    if len(parsed.affixes) < 1:
        await record_cmd.finish(
            f"❌ 未能解析出词条信息。\n\nOCR 识别文本：\n{ocr_result.text[:500]}\n\n"
            f"请确认截图包含 T10 装备词条界面。"
        )

    confirm_msg = _format_parsed_result(parsed, ocr_result.engine)

    await state_mgr.set_confirm_state(
        user_id=user_id,
        payload={
            "parsed": parsed.model_dump(),
            "img_path": str(img_path),
            "ocr_record_id": None,
            "group_id": group_id,
        },
    )

    await record_cmd.send(confirm_msg)


# ============================================================
# 全局消息监听 — 处理 Y/N 确认
# ============================================================

async def _confirm_rule(event: MessageEvent) -> bool:
    user_id = str(event.user_id)
    return await state_mgr.is_waiting_confirm(user_id)


confirm_handler = on_message(rule=Rule(_confirm_rule), priority=10)


@confirm_handler.handle()
async def handle_confirm(bot: Bot, event: MessageEvent):
    user_id = str(event.user_id)
    text = event.get_plaintext().strip().upper()

    if text not in ("Y", "N", "是", "否", "YES", "NO", "确认", "取消"):
        return

    state = await state_mgr.get(user_id)
    if state is None or state.payload is None:
        return

    payload = state.payload
    parsed = payload.get("parsed", None)
    img_path = payload.get("img_path", "")

    if not isinstance(parsed, dict):
        await state_mgr.clear(user_id)
        await confirm_handler.finish("❌ 会话数据已过期，请重新录入。")

    if text in ("N", "否", "NO", "取消"):
        await state_mgr.clear(user_id)
        await confirm_handler.finish("已取消录入。")

    await confirm_handler.send("⏳ 正在保存装备...")

    try:
        mfr_str = parsed.get("manufacturer", "")
        type_str = parsed.get("type", "")
        slot_str = parsed.get("slot", "")

        mfr = Manufacturer(mfr_str) if mfr_str else None
        etype = EquipmentType(type_str) if type_str else None
        eslot = EquipmentSlot(slot_str) if slot_str else None

        if not all([mfr, etype, eslot]):
            await state_mgr.clear(user_id)
            await confirm_handler.finish(
                "❌ 无法确定装备模板，缺少制造商/类型/部位信息。\n"
                f"制造商={mfr_str}, 类型={type_str}, 部位={slot_str}"
            )

        tmpl_repo = TemplateRepository(_get_db())
        template = await tmpl_repo.get_by_key(mfr, etype, eslot)
        if template is None:
            await state_mgr.clear(user_id)
            await confirm_handler.finish(
                f"❌ 未找到装备模板: {mfr.value} / {etype.value} / {eslot.value}"
            )

        # 构建 DTO
        affix_dtos = [
            CreateAffixDTO(
                name=a.get("name", ""),
                value=a.get("value", 0),
                quality=a.get("quality", "blue"),
                raw_name=a.get("raw_name"),
            )
            for a in parsed.get("affixes", [])
        ]
        dto = CreateEquipmentDTO(
            owner_id=user_id,
            template_id=template.id,  # type: ignore
            character_id=None,
            level=parsed.get("level", 0),
            affixes=affix_dtos,
            screenshot_path=img_path,
        )

        equip_svc = _make_equip_service()
        equipment = await equip_svc.create_equipment(dto)

        await state_mgr.clear(user_id)
        await confirm_handler.finish(
            f"✅ 装备已保存！\n\n"
            f"📦 {equipment.name}\n"
            f"🏷  ID: #{equipment.id}\n"
            f"⭐ Lv.{equipment.level}\n"
            f"📝 {len(equipment.affixes)} 条词条\n\n"
            f"使用 /我的装备 查看"
        )

    except Exception as e:
        logger.error(f"保存装备失败: {e}", exc_info=True)
        await state_mgr.clear(user_id)
        await confirm_handler.finish(f"❌ 保存失败: {e}")


# ============================================================
# /我的装备
# ============================================================

my_equip_cmd = on_command("我的装备", aliases={"查看装备", "装备列表"}, priority=5)


@my_equip_cmd.handle()
async def handle_my_equipment(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    user_id = str(event.user_id)
    await _ensure_user_registered(user_id, event.sender.nickname or "")

    page_str = args.extract_plain_text().strip()
    page = max(1, int(page_str)) if page_str.isdigit() else 1

    equip_svc = _make_equip_service()
    equipments, total = await equip_svc.get_user_equipments(
        owner_id=user_id, page=page, page_size=5,
    )

    if not equipments:
        await my_equip_cmd.finish(
            "你还没有录入任何装备。\n发送装备截图 + /装备录入 开始记录吧！"
        )

    lines = [f"📦 你的装备（共 {total} 件，第 {page} 页）：\n"]
    for eq in equipments:
        affix_summary = " / ".join(
            f"{a.name[:4]}+{a.value}%" for a in eq.affixes[:3]
        )
        lock = "🔒 " if eq.is_locked else ""
        score_str = f" | 评分 {eq.score:.0f}" if eq.score else ""
        lines.append(
            f"[#{eq.id}] {lock}{eq.name} Lv.{eq.level}{score_str}\n"
            f"  {affix_summary}"
        )

    if total > page * 5:
        lines.append(f"\n输入 /我的装备 {page + 1} 查看下一页")

    await my_equip_cmd.finish("\n\n".join(lines))


# ============================================================
# /删除装备
# ============================================================

delete_cmd = on_command("删除装备", aliases={"装备删除", "删除词条"}, priority=5)


@delete_cmd.handle()
async def handle_delete(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    user_id = str(event.user_id)
    raw = args.extract_plain_text().strip()

    if not raw.isdigit():
        await delete_cmd.finish("请指定要删除的装备 ID，例如：/删除装备 42")

    equipment_id = int(raw)
    equip_svc = _make_equip_service()

    try:
        success = await equip_svc.delete_equipment(equipment_id, user_id)
        if success:
            await delete_cmd.finish(f"✅ 已删除装备 #{equipment_id}")
        else:
            await delete_cmd.finish(f"❌ 未找到装备 #{equipment_id}")
    except ValueError as e:
        await delete_cmd.finish(f"❌ {e}")
    except RuntimeError as e:
        await delete_cmd.finish(f"🔒 {e}\n请先 /解锁装备 {equipment_id}")


# ============================================================
# /锁定装备 / /解锁装备
# ============================================================

lock_cmd = on_command("锁定装备", aliases={"装备锁定"}, priority=5)
unlock_cmd = on_command("解锁装备", aliases={"装备解锁"}, priority=5)


@lock_cmd.handle()
async def handle_lock(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    user_id = str(event.user_id)
    raw = args.extract_plain_text().strip()
    if not raw.isdigit():
        await lock_cmd.finish("用法：/锁定装备 <装备ID>")
    equipment_id = int(raw)

    try:
        equip_svc = _make_equip_service()
        eq = await equip_svc.get_equipment_detail(equipment_id)
        if eq and not eq.is_locked:
            await equip_svc.toggle_lock(equipment_id, user_id)
            await lock_cmd.finish(f"🔒 已锁定装备 #{equipment_id}")
        elif eq:
            await lock_cmd.finish(f"装备 #{equipment_id} 已经处于锁定状态")
        else:
            await lock_cmd.finish(f"❌ 未找到装备 #{equipment_id}")
    except Exception as e:
        await lock_cmd.finish(f"❌ {e}")


@unlock_cmd.handle()
async def handle_unlock(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    user_id = str(event.user_id)
    raw = args.extract_plain_text().strip()
    if not raw.isdigit():
        await unlock_cmd.finish("用法：/解锁装备 <装备ID>")
    equipment_id = int(raw)

    try:
        equip_svc = _make_equip_service()
        eq = await equip_svc.get_equipment_detail(equipment_id)
        if eq and eq.is_locked:
            await equip_svc.toggle_lock(equipment_id, user_id)
            await unlock_cmd.finish(f"🔓 已解锁装备 #{equipment_id}")
        elif eq:
            await unlock_cmd.finish(f"装备 #{equipment_id} 未锁定")
        else:
            await unlock_cmd.finish(f"❌ 未找到装备 #{equipment_id}")
    except Exception as e:
        await unlock_cmd.finish(f"❌ {e}")


# ============================================================
# /帮助
# ============================================================

help_cmd = on_command("帮助", aliases={"help", "菜单"}, priority=5)


@help_cmd.handle()
async def handle_help(bot: Bot, event: MessageEvent):
    msg = (
        "🤖 NIKKE 装备管理机器人 v2.1\n\n"
        "📸 /装备录入 — 发送截图 + 此命令录入装备\n"
        "📦 /我的装备 [页码] — 查看已录入装备\n"
        "🔍 /查询词条 <词条名> — 按词条搜索装备\n"
        "🔒 /锁定装备 <ID> — 锁定装备防止误删\n"
        "🔓 /解锁装备 <ID> — 解除锁定\n"
        "🗑  /删除装备 <ID> — 删除装备\n"
        "📊 /装备统计 — 个人装备统计\n"
        "📥 /导出装备 — 导出装备到 Excel\n"
        "🆔 /装备详情 <ID> — 查看装备详情\n\n"
        "💡 使用前请先发送 /注册"
    )
    await help_cmd.finish(msg)


# ============================================================
# 辅助函数
# ============================================================

def _format_parsed_result(parsed, engine: str) -> str:
    """格式化解析结果为可读确认文本"""
    engine_label = {"tencent": "腾讯云 OCR"}.get(engine, engine)

    lines = [
        f"📋 识别结果（{engine_label}）：\n",
        f"制造商: {parsed.manufacturer or '未知'}",
        f"类型: {parsed.type or '未知'}",
        f"部位: {parsed.slot or '未知'}",
        f"等级: Lv.{parsed.level}",
        f"\n词条:",
    ]

    for i, affix in enumerate(parsed.affixes, 1):
        quality_emoji = {"gold": "🟡", "purple": "🟣", "blue": "🔵"}.get(
            affix.quality, ""
        )
        lines.append(f"  [{i}] {affix.name} +{affix.value}% {quality_emoji}")

    lines.append(f"\n确认录入？回复 Y 确认，N 取消")

    return "\n".join(lines)

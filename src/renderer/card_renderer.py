"""
图片渲染器

负责生成装备卡片图片。
输入 Equipment + Character 对象，输出 PIL Image 或 bytes。
"""

import io
import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from src.config import get_config
from src.models.equipment import Equipment
from src.models.character import Character
from src.models.enums import AffixQuality

logger = logging.getLogger(__name__)

# 品质 → 颜色映射
QUALITY_COLORS = {
    "blue": "#4A90D9",
    "purple": "#9B59B6",
    "gold": "#F0C060",
}


class CardRenderer:
    """装备卡片渲染器"""

    # 卡片尺寸
    CARD_WIDTH = 600
    CARD_HEIGHT = 400
    PADDING = 20

    def __init__(self):
        self._font_cache: dict[int, ImageFont.FreeTypeFont] = {}
        self._load_fonts()

    def _load_fonts(self):
        """加载字体"""
        font_dir = get_config().assets_dir / "fonts"
        font_path = None

        # 按优先级查找可用字体
        candidates = [
            font_dir / "msyh.ttc",          # 微软雅黑
            font_dir / "NotoSansSC-Regular.otf",
            "C:/Windows/Fonts/msyh.ttc",    # Windows 系统字体
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
        ]
        for path in candidates:
            p = Path(path)
            if p.exists():
                font_path = str(p)
                break

        self._font_path = font_path

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """获取字体（带缓存）"""
        if size not in self._font_cache:
            try:
                if self._font_path:
                    self._font_cache[size] = ImageFont.truetype(self._font_path, size)
                else:
                    self._font_cache[size] = ImageFont.load_default()
            except Exception:
                self._font_cache[size] = ImageFont.load_default()
        return self._font_cache[size]

    def render_equipment_card(
        self,
        equipment: Equipment,
        character: Optional[Character] = None,
    ) -> bytes:
        """渲染单件装备卡片。

        Args:
            equipment: 装备对象
            character: 角色对象（可选）

        Returns:
            PNG 图片字节数据
        """
        img = Image.new("RGB", (self.CARD_WIDTH, self.CARD_HEIGHT), color="#1a1a2e")
        draw = ImageDraw.Draw(img)

        y = self.PADDING

        # ---- 标题 ----
        title = f"{equipment.manufacturer.value} {equipment.name}"
        draw.text((self.PADDING, y), title, fill="#FFFFFF", font=self._get_font(20))
        y += 30

        # ---- 基本信息行 ----
        info_line = (
            f"类型: {equipment.type.value}  |  "
            f"部位: {equipment.slot.value}  |  "
            f"等级: Lv.{equipment.level}"
        )
        draw.text((self.PADDING, y), info_line, fill="#AAAAAA", font=self._get_font(14))
        y += 24

        # 角色信息
        if character:
            draw.text(
                (self.PADDING, y),
                f"角色: {character.name}",
                fill="#AAAAAA",
                font=self._get_font(14),
            )
            y += 24

        y += 10

        # ---- 分隔线 ----
        draw.line(
            [(self.PADDING, y), (self.CARD_WIDTH - self.PADDING, y)],
            fill="#333355",
            width=1,
        )
        y += 16

        # ---- 词条 ----
        if equipment.affixes:
            draw.text(
                (self.PADDING, y),
                "词条属性:",
                fill="#CCCCCC",
                font=self._get_font(16),
            )
            y += 28

        for i, affix in enumerate(equipment.affixes):
            quality_color = QUALITY_COLORS.get(affix.quality.value, "#FFFFFF")

            # 词条序号 + 名称
            line = f"  [{i + 1}] {affix.name}"
            draw.text((self.PADDING, y), line, fill="#FFFFFF", font=self._get_font(14))

            # 数值 + 品质标记
            value_text = f"+{affix.value}%  "
            value_w = draw.textlength(value_text, font=self._get_font(14))

            draw.text(
                (self.PADDING + 280, y),
                value_text,
                fill=quality_color,
                font=self._get_font(14),
            )

            # 品质标签
            quality_label = {"blue": "蓝", "purple": "紫", "gold": "金"}.get(
                affix.quality.value, "?"
            )
            draw.text(
                (self.PADDING + 280 + value_w, y),
                quality_label,
                fill=quality_color,
                font=self._get_font(14),
            )

            # Tier
            tier_text = f"T{affix.tier}"
            draw.text(
                (self.PADDING + 450, y),
                tier_text,
                fill="#888888",
                font=self._get_font(12),
            )

            y += 22

        # ---- 底部信息 ----
        y = self.CARD_HEIGHT - 40
        if equipment.is_locked:
            draw.text(
                (self.PADDING, y), "🔒 已锁定", fill="#FF6B6B", font=self._get_font(12)
            )
        if equipment.score is not None:
            draw.text(
                (self.CARD_WIDTH - self.PADDING - 120, y),
                f"评分: {equipment.score:.1f}",
                fill="#F0C060",
                font=self._get_font(14),
            )

        # 输出 PNG bytes
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


# 全局单例
_card_renderer: Optional[CardRenderer] = None


def get_renderer() -> CardRenderer:
    """获取渲染器单例"""
    global _card_renderer
    if _card_renderer is None:
        _card_renderer = CardRenderer()
    return _card_renderer

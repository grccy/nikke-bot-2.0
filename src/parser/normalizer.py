"""
OCR 文本预处理

负责：
- 全角 → 半角
- 去除多余空格
- 常见 OCR 错误修正
"""

import re

# 全角 → 半角映射
_FULLWIDTH_MAP: dict[int, int] = {}
for _i in range(0xFF01, 0xFF5F):
    _FULLWIDTH_MAP[_i] = _i - 0xFEE0
_FULLWIDTH_MAP[0x3000] = 0x20  # 全角空格 → 半角空格

# 常见 OCR 错字修正
_OCR_CORRECTIONS: list[tuple[str, str]] = [
    # 日文假名（OCR 容易误识为相似汉字）
    ("カ", "力"),   # 攻击カ → 攻击力
    ("ヶ", "力"),   # 攻击ヶ → 攻击力
    ("ィ", "小"),   # 小 → 小
    ("ェ", "工"),
    ("ォ", "才"),
    ("ッ", "你"),   # 不同语境不同，大概率错

    # 常见字母数字误识
    ("Lv", "Lv"),
    ("LV", "LV"),
    ("lv", "Lv"),
    ("L V", "Lv"),
    ("L.V", "Lv"),

    # 常见中文错字
    ("装弾", "装弹"),
    ("弾夹", "弹夹"),
    ("弾数", "弹数"),
    ("暴擎", "暴击"),
    ("会心", "暴击"),
    ("充能", "蓄力"),
    ("攻击型", "火力型"),
]


def normalize_text(text: str) -> str:
    """OCR 文本预处理。

    处理顺序：
    1. 全角 → 半角
    2. 去除首尾空白
    3. 常见 OCR 错误修正

    Args:
        text: OCR 原始识别文本

    Returns:
        规范化后的文本
    """
    # 全角 → 半角
    text = text.translate(_FULLWIDTH_MAP)

    # 去除首尾空白（保留内部空格用于分词）
    text = text.strip()

    # 合并连续空白
    text = re.sub(r"[ \t]+", " ", text)

    return text


def correct_ocr_errors(text: str) -> str:
    """修正常见 OCR 识别错误。

    Args:
        text: 待修正文本

    Returns:
        修正后的文本
    """
    for wrong, correct in _OCR_CORRECTIONS:
        text = text.replace(wrong, correct)
    return text

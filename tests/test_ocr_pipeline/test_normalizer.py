"""
测试 Normalizer —— OCR 文本预处理
"""

import pytest
from src.parser.normalizer import normalize_text, correct_ocr_errors


class TestNormalizeText:
    """文本规范化"""

    def test_fullwidth_to_halfwidth(self):
        """全角字符应转换为半角"""
        text = "攻撃力　＋１５．６％"  # 全角空格+全角数字
        result = normalize_text(text)
        # 全角空格→半角空格, 全角数字→半角数字
        assert "+" in result or "15.6" in result or "15" in result

    def test_strips_whitespace(self):
        """应去除首尾空白"""
        result = normalize_text("  朝圣者 火力头盔  \n")
        assert result == "朝圣者 火力头盔"

    def test_collapses_multiple_spaces(self):
        """多个连续空格应合并为一个"""
        result = normalize_text("攻击力     +15.6%")
        assert "    " not in result
        assert "攻击力 +15.6%" in result

    def test_preserves_newlines(self):
        """应保留换行符"""
        text = "朝圣者\n火力型\n头盔\n攻击力 +15%"
        result = normalize_text(text)
        assert "\n" in result

    def test_empty_string(self):
        """空字符串不应报错"""
        result = normalize_text("")
        assert result == ""

    def test_english_text_preserved(self):
        """英文应保留"""
        result = normalize_text("PILGRIM Attack Head")
        assert "PILGRIM" in result


class TestCorrectOCRErrors:
    """OCR 错字修正"""

    def test_katakana_force_correction(self):
        """日文假名カ应修正为力"""
        # "攻击カ" → "攻击力"
        result = correct_ocr_errors("攻击カ +15.6%")
        assert "攻击力" in result
        assert "カ" not in result

    def test_danmu_correction(self):
        """弾应修正为弹"""
        result = correct_ocr_errors("最大装弾数 +50%")
        assert "最大装弹数" in result

    def test_huixin_correction(self):
        """会心应修正为暴击"""
        result = correct_ocr_errors("会心率 +5%")
        assert "暴击率" in result

    def test_chongneng_correction(self):
        """充能应修正为蓄力"""
        result = correct_ocr_errors("充能速度 +8%")
        assert "蓄力速度" in result

    def test_attack_type_correction(self):
        """攻击型应修正为火力型"""
        result = correct_ocr_errors("攻击型头盔")
        assert "火力型" in result

    def test_no_false_positive(self):
        """不应错误修正正确文本"""
        text = "攻击力 +15.6% 暴击伤害 +24.3%"
        result = correct_ocr_errors(text)
        assert result == text

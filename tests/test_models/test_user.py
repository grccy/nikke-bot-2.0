"""
测试 User 用户模型
"""

from src.models.user import User, UserPreferences


class TestUserModel:
    """用户模型单元测试"""

    def test_create_user(self):
        """创建用户"""
        user = User(qq_id="123456789", nickname="测试用户")
        assert user.qq_id == "123456789"
        assert user.nickname == "测试用户"
        assert isinstance(user.preferences, UserPreferences)

    def test_default_preferences(self):
        """默认偏好设置"""
        prefs = UserPreferences()
        assert prefs.default_sort == "newest"
        assert prefs.items_per_page == 5
        assert prefs.language == "zh-CN"

    def test_user_preferences_default(self):
        """用户默认偏好"""
        user = User(qq_id="123")
        assert user.preferences.default_sort == "newest"

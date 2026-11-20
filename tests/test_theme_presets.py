import unittest

from pomodoro.theme_presets import (
    APPLE_THEME_KEYS,
    DEFAULT_THEME_KEY,
    THEMES,
    THEME_NAMES,
    find_theme,
    find_theme_by_name,
    get_theme,
)

REQUIRED_COLORS = {
    "bg",
    "card",
    "card_light",
    "track",
    "text",
    "muted",
    "focus",
    "focus_hover",
    "short",
    "long",
    "danger",
    "on_accent",
}


class ThemePresetTests(unittest.TestCase):
    def test_all_themes_are_complete(self) -> None:
        self.assertEqual(
            THEME_NAMES,
            ("云端白", "曜石黑", "海蓝", "薄荷绿", "暖阳橙", "暮光紫"),
        )
        self.assertEqual(tuple(theme.key for theme in THEMES), APPLE_THEME_KEYS)
        for theme in THEMES:
            self.assertTrue(REQUIRED_COLORS.issubset(theme.colors))
            self.assertTrue(theme.font)
            self.assertTrue(theme.description)

    def test_lookup_by_key_and_name(self) -> None:
        self.assertIs(find_theme("apple_light"), THEMES[0])
        self.assertIs(find_theme_by_name("云端白"), THEMES[0])
        self.assertIsNone(find_theme("business"))
        self.assertIsNone(find_theme_by_name("国风"))

    def test_get_theme_falls_back_to_default(self) -> None:
        default = get_theme(DEFAULT_THEME_KEY)
        self.assertEqual(default.key, "apple_light")
        self.assertIs(get_theme(None), default)
        self.assertIs(get_theme("unknown"), default)


if __name__ == "__main__":
    unittest.main()

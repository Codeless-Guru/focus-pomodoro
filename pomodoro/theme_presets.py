"""界面风格预设。

v0.3.0 使用 6 套参考 Apple 设计语言重新设计的主题：低饱和背景、清晰层级、
高辨识度强调色和更克制的文字颜色。切换主题时只替换配色和字体，不改动业务逻辑。
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_THEME_KEY = "apple_light"

APPLE_THEME_KEYS: tuple[str, ...] = (
    "apple_light",
    "apple_dark",
    "apple_blue",
    "apple_mint",
    "apple_orange",
    "apple_purple",
)


@dataclass(frozen=True)
class ThemePreset:
    """一套完整的界面风格。"""

    key: str
    name: str
    description: str
    font: str
    colors: dict[str, str]


THEMES: tuple[ThemePreset, ...] = (
    ThemePreset(
        key="apple_light",
        name="云端白",
        description="接近系统浅色模式的柔和灰白背景，蓝色强调，干净克制。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#F5F5F7",
            "card": "#FFFFFF",
            "card_light": "#E8E8ED",
            "track": "#D2D2D7",
            "text": "#1D1D1F",
            "muted": "#6E6E73",
            "focus": "#0071E3",
            "focus_hover": "#0A84FF",
            "short": "#248A3D",
            "long": "#8944AB",
            "danger": "#D70015",
            "on_accent": "#FFFFFF",
        },
    ),
    ThemePreset(
        key="apple_dark",
        name="曜石黑",
        description="深黑背景配高亮蓝绿点缀，接近系统深色模式。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#0C0C0E",
            "card": "#1C1C1E",
            "card_light": "#2C2C2E",
            "track": "#3A3A3C",
            "text": "#F5F5F7",
            "muted": "#98989D",
            "focus": "#0A84FF",
            "focus_hover": "#409CFF",
            "short": "#30D158",
            "long": "#BF5AF2",
            "danger": "#FF453A",
            "on_accent": "#FFFFFF",
        },
    ),
    ThemePreset(
        key="apple_blue",
        name="海蓝",
        description="浅蓝雾面背景与经典系统蓝，清爽专注。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#EEF5FF",
            "card": "#FFFFFF",
            "card_light": "#DCEAFF",
            "track": "#BBD6FF",
            "text": "#0B1F33",
            "muted": "#5B7392",
            "focus": "#0071E3",
            "focus_hover": "#0A84FF",
            "short": "#248A3D",
            "long": "#5E5CE6",
            "danger": "#D70015",
            "on_accent": "#FFFFFF",
        },
    ),
    ThemePreset(
        key="apple_mint",
        name="薄荷绿",
        description="低饱和薄荷背景与深绿色强调，轻盈但不刺眼。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#EFFBF6",
            "card": "#FFFFFF",
            "card_light": "#D9F5E8",
            "track": "#BCE9D4",
            "text": "#0B2E22",
            "muted": "#5A7C6E",
            "focus": "#0B8A5B",
            "focus_hover": "#30B97A",
            "short": "#0A84FF",
            "long": "#8944AB",
            "danger": "#C92A2A",
            "on_accent": "#FFFFFF",
        },
    ),
    ThemePreset(
        key="apple_orange",
        name="暖阳橙",
        description="暖白底色与柔和橙色强调，明亮温暖。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#FFF7EF",
            "card": "#FFFFFF",
            "card_light": "#FFE7CC",
            "track": "#FFD2A8",
            "text": "#3A2412",
            "muted": "#8A6A4F",
            "focus": "#D97900",
            "focus_hover": "#FF9500",
            "short": "#248A3D",
            "long": "#8944AB",
            "danger": "#C92A2A",
            "on_accent": "#FFFFFF",
        },
    ),
    ThemePreset(
        key="apple_purple",
        name="暮光紫",
        description="淡紫背景与柔紫强调，安静柔和，适合晚间专注。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#F7F2FF",
            "card": "#FFFFFF",
            "card_light": "#E9DFFF",
            "track": "#D6C4F5",
            "text": "#2A1B3D",
            "muted": "#74658A",
            "focus": "#8944AB",
            "focus_hover": "#AF52DE",
            "short": "#248A3D",
            "long": "#0071E3",
            "danger": "#C92A2A",
            "on_accent": "#FFFFFF",
        },
    ),
)

THEME_NAMES: tuple[str, ...] = tuple(theme.name for theme in THEMES)


def find_theme(key: str) -> ThemePreset | None:
    """按键查找主题预设。"""
    for theme in THEMES:
        if theme.key == key:
            return theme
    return None


def find_theme_by_name(name: str) -> ThemePreset | None:
    """按中文名称查找主题预设。"""
    for theme in THEMES:
        if theme.name == name:
            return theme
    return None


def get_theme(key: str | None) -> ThemePreset:
    """取得主题；未知或空值回退到默认云端白主题。"""
    if key is not None:
        theme = find_theme(key)
        if theme is not None:
            return theme
    for theme in THEMES:
        if theme.key == DEFAULT_THEME_KEY:
            return theme
    return THEMES[0]

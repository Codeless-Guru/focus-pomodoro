"""界面风格预设。

每个预设只包含配色和字体，界面控件在切换时按这些值重新构建。
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_THEME_KEY = "business"


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
        key="guofeng",
        name="国风",
        description="宣纸底色、朱砂点缀、青玉辅助，搭配楷体气质。",
        font="KaiTi",
        colors={
            "bg": "#F3EBDD",
            "card": "#FFF9EF",
            "card_light": "#EADFC9",
            "track": "#D8C7A8",
            "text": "#2E2118",
            "muted": "#7A6752",
            "focus": "#A33B2A",
            "focus_hover": "#C3553F",
            "short": "#3F7D63",
            "long": "#B08432",
            "danger": "#B23A2E",
            "on_accent": "#FFF9EF",
        },
    ),
    ThemePreset(
        key="business",
        name="商务",
        description="深蓝背景与高对比强调色，沉稳专注。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#0B1220",
            "card": "#111C31",
            "card_light": "#182740",
            "track": "#24314A",
            "text": "#F1F5F9",
            "muted": "#94A3B8",
            "focus": "#38BDF8",
            "focus_hover": "#7DD3FC",
            "short": "#34D399",
            "long": "#A78BFA",
            "danger": "#FB7185",
            "on_accent": "#06121F",
        },
    ),
    ThemePreset(
        key="children",
        name="儿童",
        description="明亮活泼的糖果色，适合轻松的任务节奏。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#FFF7E6",
            "card": "#FFFFFF",
            "card_light": "#FFF0C7",
            "track": "#FFD9A0",
            "text": "#3B2A1A",
            "muted": "#8A6B4F",
            "focus": "#FF7A59",
            "focus_hover": "#FF9A80",
            "short": "#43C59E",
            "long": "#7C6CF0",
            "danger": "#FF4D6D",
            "on_accent": "#FFFFFF",
        },
    ),
    ThemePreset(
        key="fairy",
        name="仙女",
        description="柔和粉紫与浅蓝渐变感，轻盈梦幻。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#FDF4FF",
            "card": "#FFFFFF",
            "card_light": "#F7E6FF",
            "track": "#E9D5FF",
            "text": "#4A2B5A",
            "muted": "#8B6A9C",
            "focus": "#D946EF",
            "focus_hover": "#E879F9",
            "short": "#7DD3FC",
            "long": "#C084FC",
            "danger": "#FB7185",
            "on_accent": "#FFFFFF",
        },
    ),
    ThemePreset(
        key="fresh",
        name="清爽",
        description="浅青与白色搭配，简洁明快。",
        font="Microsoft YaHei UI",
        colors={
            "bg": "#F0FDFA",
            "card": "#FFFFFF",
            "card_light": "#E6FFFA",
            "track": "#CCFBF1",
            "text": "#134E4A",
            "muted": "#5E8C86",
            "focus": "#0EA5A4",
            "focus_hover": "#14B8A6",
            "short": "#22C55E",
            "long": "#6366F1",
            "danger": "#F97373",
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
    """取得主题；未知或空值回退到默认商务主题。"""
    if key is not None:
        theme = find_theme(key)
        if theme is not None:
            return theme
    for theme in THEMES:
        if theme.key == DEFAULT_THEME_KEY:
            return theme
    return THEMES[0]

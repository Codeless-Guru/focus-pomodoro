"""桌面番茄钟核心包。"""

VERSION = "0.3.0"

from .calendar_store import CalendarEvent, CalendarStore
from .duration_presets import PRESETS, DurationPreset, find_preset
from .theme_presets import (
    APPLE_THEME_KEYS,
    THEMES,
    THEME_NAMES,
    ThemePreset,
    get_theme,
)
from .timer import Phase, PomodoroTimer, TimerConfig, TimerEvent, TimerSnapshot, format_duration

__all__ = [
    "VERSION",
    "APPLE_THEME_KEYS",
    "THEMES",
    "THEME_NAMES",
    "ThemePreset",
    "get_theme",
    "CalendarEvent",
    "CalendarStore",
    "PRESETS",
    "DurationPreset",
    "find_preset",
    "Phase",
    "PomodoroTimer",
    "TimerConfig",
    "TimerEvent",
    "TimerSnapshot",
    "format_duration",
]

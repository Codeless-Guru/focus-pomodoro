"""桌面番茄钟核心包。"""

VERSION = "0.2.0"

from .duration_presets import PRESETS, DurationPreset, find_preset
from .theme_presets import THEMES, THEME_NAMES, ThemePreset, get_theme
from .timer import Phase, PomodoroTimer, TimerConfig, TimerEvent, TimerSnapshot, format_duration

__all__ = [
    "VERSION",
    "THEMES",
    "THEME_NAMES",
    "ThemePreset",
    "get_theme",
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

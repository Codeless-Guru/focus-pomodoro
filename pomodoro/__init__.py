"""桌面番茄钟核心包。"""

from .duration_presets import PRESETS, DurationPreset, find_preset
from .timer import Phase, PomodoroTimer, TimerConfig, TimerEvent, TimerSnapshot, format_duration

__all__ = [
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

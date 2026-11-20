"""番茄钟时长方案预设。

预设只保存时长组合，真正的范围校验仍由 TimerConfig 负责。
"""

from __future__ import annotations

from dataclasses import dataclass

from .timer import TimerConfig


@dataclass(frozen=True)
class DurationPreset:
    """一个可直接套用的时长方案。"""

    name: str
    description: str
    config: TimerConfig

    @property
    def summary(self) -> str:
        """返回用于界面展示的简短摘要。"""
        return (
            f"{self.config.focus_minutes}/{self.config.short_break_minutes}/"
            f"{self.config.long_break_minutes}，{self.config.sessions_before_long_break} 轮"
        )


PRESETS: tuple[DurationPreset, ...] = (
    DurationPreset(
        "经典番茄",
        "最常用的番茄工作法，适合日常任务。",
        TimerConfig(25, 5, 15, 4),
    ),
    DurationPreset(
        "短时专注",
        "较短的专注块，适合容易被打断的环境。",
        TimerConfig(15, 3, 10, 4),
    ),
    DurationPreset(
        "深度工作",
        "更长的专注块，适合阅读、写作和复杂任务。",
        TimerConfig(50, 10, 20, 4),
    ),
    DurationPreset(
        "轻量循环",
        "短节奏、多轮次，适合整理和机械性工作。",
        TimerConfig(10, 2, 8, 6),
    ),
)


def find_preset(config: TimerConfig) -> DurationPreset | None:
    """如果配置与某个预设完全一致，返回该预设，否则返回 None。"""
    for preset in PRESETS:
        if preset.config == config:
            return preset
    return None

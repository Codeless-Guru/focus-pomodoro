"""应用设置的读取与持久化。

设置以 JSON 文件保存；文件缺失或损坏时自动回退到默认值。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .theme_presets import DEFAULT_THEME_KEY, find_theme
from .timer import TimerConfig

# 默认把用户设置保存在主目录下，避免污染程序目录。
DEFAULT_SETTINGS_PATH = Path.home() / ".focus_pomodoro" / "settings.json"


@dataclass
class AppSettings:
    """界面相关设置，计时时长仍由 TimerConfig 负责。"""
    timer: TimerConfig = field(default_factory=TimerConfig)
    auto_start_next: bool = True
    sound_enabled: bool = True
    always_on_top: bool = False
    calendar_alerts_enabled: bool = True
    task_name: str = ""
    theme_key: str = DEFAULT_THEME_KEY

    def to_dict(self) -> dict[str, Any]:
        return {
            "focus_minutes": self.timer.focus_minutes,
            "short_break_minutes": self.timer.short_break_minutes,
            "long_break_minutes": self.timer.long_break_minutes,
            "sessions_before_long_break": self.timer.sessions_before_long_break,
            "auto_start_next": self.auto_start_next,
            "sound_enabled": self.sound_enabled,
            "always_on_top": self.always_on_top,
            "calendar_alerts_enabled": self.calendar_alerts_enabled,
            "task_name": self.task_name,
            "theme_key": self.theme_key,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AppSettings:
        default = cls()
        timer = TimerConfig(
            focus_minutes=data.get("focus_minutes", default.timer.focus_minutes),
            short_break_minutes=data.get(
                "short_break_minutes", default.timer.short_break_minutes
            ),
            long_break_minutes=data.get(
                "long_break_minutes", default.timer.long_break_minutes
            ),
            sessions_before_long_break=data.get(
                "sessions_before_long_break",
                default.timer.sessions_before_long_break,
            ),
        )
        return cls(
            timer=timer,
            auto_start_next=_read_bool(
                data, "auto_start_next", default.auto_start_next
            ),
            sound_enabled=_read_bool(data, "sound_enabled", default.sound_enabled),
            always_on_top=_read_bool(
                data, "always_on_top", default.always_on_top
            ),
            calendar_alerts_enabled=_read_bool(
                data, "calendar_alerts_enabled", default.calendar_alerts_enabled
            ),
            task_name=_read_str(data, "task_name", default.task_name),
            theme_key=_read_theme_key(data, "theme_key", default.theme_key),
        )


def _read_bool(data: Mapping[str, Any], key: str, default: bool) -> bool:
    value = data.get(key, default)
    return value if isinstance(value, bool) else default


def _read_str(data: Mapping[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    return value if isinstance(value, str) else default


def _read_theme_key(data: Mapping[str, Any], key: str, default: str) -> str:
    value = data.get(key, default)
    if isinstance(value, str) and find_theme(value) is not None:
        return value
    return default


def load_settings(path: Path | str | None = None) -> AppSettings:
    """读取设置；文件不存在或内容非法时使用默认设置。"""
    settings_path = Path(path) if path is not None else DEFAULT_SETTINGS_PATH
    if not settings_path.exists():
        return AppSettings()
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return AppSettings()
        return AppSettings.from_dict(data)
    except (OSError, ValueError, TypeError):
        return AppSettings()


def save_settings(
    settings: AppSettings,
    path: Path | str | None = None,
) -> Path:
    """把当前设置写入 JSON 文件，并确保父目录存在。"""
    settings_path = Path(path) if path is not None else DEFAULT_SETTINGS_PATH
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return settings_path

"""本地专注统计。

统计只保存在用户目录，不上传网络；日期可通过参数注入以便测试。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable

DEFAULT_STATS_PATH = Path.home() / ".focus_pomodoro" / "stats.json"
DateProvider = Callable[[], date]


@dataclass(frozen=True)
class DailyStat:
    """某一天的专注统计。"""

    day: date
    pomodoros: int
    minutes: int


@dataclass(frozen=True)
class StatsSummary:
    """统计面板使用的汇总结果。"""

    total_pomodoros: int
    total_minutes: int
    today_pomodoros: int
    week_pomodoros: int
    streak_days: int
    last_7_days: tuple[DailyStat, ...]


def _default_today() -> date:
    return datetime.now().date()


class StatsStore:
    """负责记录每日番茄并生成统计摘要。"""

    def __init__(
        self,
        path: Path | str | None = None,
        *,
        today_provider: DateProvider | None = None,
    ) -> None:
        self.path = Path(path) if path is not None else DEFAULT_STATS_PATH
        self._today_provider = today_provider or _default_today
        self.days: dict[date, DailyStat] = self._load()

    def _load(self) -> dict[date, DailyStat]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            items = data.get("days", {}) if isinstance(data, dict) else {}
            if not isinstance(items, dict):
                return {}
            result: dict[date, DailyStat] = {}
            for key, value in items.items():
                day = date.fromisoformat(key)
                if not isinstance(value, dict):
                    continue
                pomodoros = value.get("pomodoros", 0)
                minutes = value.get("minutes", 0)
                if isinstance(pomodoros, int) and isinstance(minutes, int):
                    result[day] = DailyStat(day, max(0, pomodoros), max(0, minutes))
            return result
        except (OSError, ValueError, TypeError):
            return {}

    def save(self) -> None:
        """把统计数据写入 JSON 文件。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "days": {
                day.isoformat(): {
                    "pomodoros": stat.pomodoros,
                    "minutes": stat.minutes,
                }
                for day, stat in sorted(self.days.items())
            }
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def record_focus(self, minutes: int) -> None:
        """记录一次自然完成的专注番茄。"""
        if isinstance(minutes, bool) or not isinstance(minutes, int):
            raise ValueError("专注分钟数必须是整数")
        if minutes <= 0:
            raise ValueError("专注分钟数必须大于 0")

        today = self._today_provider()
        old = self.days.get(today, DailyStat(today, 0, 0))
        self.days[today] = DailyStat(
            day=today,
            pomodoros=old.pomodoros + 1,
            minutes=old.minutes + minutes,
        )
        self.save()

    def summary(self) -> StatsSummary:
        """生成统计面板和成就系统使用的摘要。"""
        today = self._today_provider()
        last_7_days = tuple(
            self.days.get(today - timedelta(days=offset), DailyStat(today - timedelta(days=offset), 0, 0))
            for offset in range(6, -1, -1)
        )
        total_pomodoros = sum(stat.pomodoros for stat in self.days.values())
        total_minutes = sum(stat.minutes for stat in self.days.values())
        week_pomodoros = sum(stat.pomodoros for stat in last_7_days)
        today_pomodoros = self.days.get(today, DailyStat(today, 0, 0)).pomodoros

        cursor = today if today in self.days else today - timedelta(days=1)
        streak = 0
        while cursor in self.days and self.days[cursor].pomodoros > 0:
            streak += 1
            cursor -= timedelta(days=1)

        return StatsSummary(
            total_pomodoros=total_pomodoros,
            total_minutes=total_minutes,
            today_pomodoros=today_pomodoros,
            week_pomodoros=week_pomodoros,
            streak_days=streak,
            last_7_days=last_7_days,
        )

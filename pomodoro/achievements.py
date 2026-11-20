"""成就判定逻辑。

成就根据本地统计和任务状态实时计算，无需额外存储。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .stats import StatsSummary
from .tasks import Task


@dataclass(frozen=True)
class Achievement:
    """一个可解锁成就。"""

    key: str
    name: str
    description: str


ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement("first", "初次专注", "完成第 1 个番茄"),
    Achievement("ten", "十全十美", "累计完成 10 个番茄"),
    Achievement("daily_four", "今日发力", "一天完成 4 个番茄"),
    Achievement("weekly_twenty", "周勤者", "近 7 天完成 20 个番茄"),
    Achievement("streak_three", "三连打卡", "连续 3 天有专注记录"),
    Achievement("deep_five_hours", "深耕者", "累计专注 300 分钟"),
    Achievement("task_finisher", "任务收尾人", "完成一个已估算的任务"),
)


def unlocked_achievements(
    summary: StatsSummary,
    tasks: Iterable[Task],
) -> tuple[Achievement, ...]:
    """返回当前已解锁的成就。"""
    conditions = {
        "first": summary.total_pomodoros >= 1,
        "ten": summary.total_pomodoros >= 10,
        "daily_four": summary.today_pomodoros >= 4,
        "weekly_twenty": summary.week_pomodoros >= 20,
        "streak_three": summary.streak_days >= 3,
        "deep_five_hours": summary.total_minutes >= 300,
        "task_finisher": any(
            task.estimate > 0 and task.completed >= task.estimate for task in tasks
        ),
    }
    return tuple(item for item in ACHIEVEMENTS if conditions.get(item.key, False))

"""桌面日历与闹钟提醒的本地存储。

日历事件同时承担日程和闹钟角色：支持指定日期、时间、备注，以及不重复/每天/每周
三种重复规则。数据只保存在用户目录，不上传网络。
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable

DEFAULT_CALENDAR_PATH = Path.home() / ".focus_pomodoro" / "calendar.json"

REPEAT_NONE = "none"
REPEAT_DAILY = "daily"
REPEAT_WEEKLY = "weekly"
REPEAT_LABELS: dict[str, str] = {
    REPEAT_NONE: "不重复",
    REPEAT_DAILY: "每天",
    REPEAT_WEEKLY: "每周",
}
REPEAT_NAMES: tuple[str, ...] = tuple(REPEAT_LABELS.values())

ALARM_WINDOW_SECONDS = 300
NowProvider = Callable[[], datetime]


def _default_now() -> datetime:
    return datetime.now()


def _read_bool(value: object, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def _parse_time(value: object) -> time | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


@dataclass
class CalendarEvent:
    """一条日历提醒/闹钟。"""

    id: str
    title: str
    event_date: date
    event_time: time
    note: str = ""
    repeat: str = REPEAT_NONE
    enabled: bool = True
    last_triggered: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "date": self.event_date.isoformat(),
            "time": self.event_time.strftime("%H:%M"),
            "note": self.note,
            "repeat": self.repeat,
            "enabled": self.enabled,
            "last_triggered": self.last_triggered,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalendarEvent | None:
        title = data.get("title")
        raw_date = data.get("date")
        event_time = _parse_time(data.get("time"))
        if not isinstance(title, str) or not title.strip():
            return None
        if not isinstance(raw_date, str) or event_time is None:
            return None
        try:
            event_date = date.fromisoformat(raw_date)
        except ValueError:
            return None

        event_id = data.get("id")
        if not isinstance(event_id, str) or not event_id:
            event_id = uuid.uuid4().hex[:8]
        repeat = data.get("repeat")
        if repeat not in REPEAT_LABELS:
            repeat = REPEAT_NONE
        note = data.get("note")
        last_triggered = data.get("last_triggered")
        return cls(
            id=event_id,
            title=title.strip(),
            event_date=event_date,
            event_time=event_time,
            note=note.strip() if isinstance(note, str) else "",
            repeat=str(repeat),
            enabled=_read_bool(data.get("enabled"), True),
            last_triggered=last_triggered if isinstance(last_triggered, str) else None,
        )

    def repeat_label(self) -> str:
        return REPEAT_LABELS.get(self.repeat, REPEAT_LABELS[REPEAT_NONE])


class CalendarStore:
    """负责日历提醒的读写、重复规则和到点提醒判定。"""

    def __init__(
        self,
        path: Path | str | None = None,
        *,
        now_provider: NowProvider | None = None,
    ) -> None:
        self.path = Path(path) if path is not None else DEFAULT_CALENDAR_PATH
        self._now_provider = now_provider or _default_now
        self.events: list[CalendarEvent] = self._load()

    def _load(self) -> list[CalendarEvent]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            items = data.get("events", []) if isinstance(data, dict) else []
            if not isinstance(items, list):
                return []
            events: list[CalendarEvent] = []
            for item in items:
                if isinstance(item, dict):
                    event = CalendarEvent.from_dict(item)
                    if event is not None:
                        events.append(event)
            return events
        except (OSError, ValueError, TypeError):
            return []

    def save(self) -> None:
        """把日历提醒写入 JSON 文件。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"events": [event.to_dict() for event in self.events]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def add(
        self,
        title: str,
        event_date: date,
        event_time: time,
        note: str = "",
        repeat: str = REPEAT_NONE,
        enabled: bool = True,
    ) -> CalendarEvent:
        """新增提醒；标题不能为空，重复规则非法时按“不重复”处理。"""
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("提醒标题不能为空")
        if repeat not in REPEAT_LABELS:
            repeat = REPEAT_NONE
        event = CalendarEvent(
            id=uuid.uuid4().hex[:8],
            title=cleaned,
            event_date=event_date,
            event_time=event_time,
            note=note.strip(),
            repeat=repeat,
            enabled=bool(enabled),
        )
        self.events.append(event)
        self.save()
        return event

    def update(
        self,
        event_id: str,
        *,
        title: str,
        event_date: date,
        event_time: time,
        note: str,
        repeat: str,
        enabled: bool,
    ) -> None:
        """更新已有提醒；修改后重新允许当天提醒。"""
        event = self.find(event_id)
        if event is None:
            raise ValueError("提醒不存在")
        cleaned = title.strip()
        if not cleaned:
            raise ValueError("提醒标题不能为空")
        event.title = cleaned
        event.event_date = event_date
        event.event_time = event_time
        event.note = note.strip()
        event.repeat = repeat if repeat in REPEAT_LABELS else REPEAT_NONE
        event.enabled = bool(enabled)
        event.last_triggered = None
        self.save()

    def remove(self, event_id: str) -> None:
        """删除指定提醒。"""
        self.events = [event for event in self.events if event.id != event_id]
        self.save()

    def find(self, event_id: str) -> CalendarEvent | None:
        """按 ID 查找提醒。"""
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def events_for(self, day: date) -> tuple[CalendarEvent, ...]:
        """返回指定日期实际会发生的提醒，包含重复事件，并按时间排序。"""
        results = [event for event in self.events if self._occurs_on(event, day)]
        results.sort(key=lambda event: (event.event_time, event.title))
        return tuple(results)

    def due_events(
        self,
        now: datetime | None = None,
        *,
        window_seconds: int = ALARM_WINDOW_SECONDS,
    ) -> tuple[CalendarEvent, ...]:
        """返回当前时间窗口内尚未提醒过的事件。"""
        current = now or self._now_provider()
        trigger_key = current.date().isoformat()
        results: list[CalendarEvent] = []
        for event in self.events:
            if not event.enabled or event.last_triggered == trigger_key:
                continue
            if not self._occurs_on(event, current.date()):
                continue
            scheduled = datetime.combine(current.date(), event.event_time)
            delta = (current - scheduled).total_seconds()
            if 0 <= delta <= window_seconds:
                results.append(event)
        results.sort(key=lambda event: (event.event_time, event.title))
        return tuple(results)

    def mark_triggered(
        self, event_id: str, now: datetime | None = None
    ) -> None:
        """记录提醒已触发，避免同一天重复打扰。"""
        event = self.find(event_id)
        if event is None:
            return
        current = now or self._now_provider()
        event.last_triggered = current.date().isoformat()
        self.save()

    def next_event(self, now: datetime | None = None) -> CalendarEvent | None:
        """返回下一次启用的提醒；没有时返回 None。"""
        current = now or self._now_provider()
        candidates: list[tuple[datetime, CalendarEvent]] = []
        for event in self.events:
            if not event.enabled:
                continue
            next_time = self._next_occurrence(event, current)
            if next_time is not None:
                candidates.append((next_time, event))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1].title))
        return candidates[0][1]

    def next_summary(self, now: datetime | None = None) -> str:
        """生成主界面的一句话提醒摘要。"""
        event = self.next_event(now)
        if event is None:
            return "今日提醒：暂无安排"
        next_time = self._next_occurrence(event, now or self._now_provider())
        assert next_time is not None
        return f"下一个提醒：{next_time:%m-%d %H:%M} · {event.title}"

    @staticmethod
    def _occurs_on(event: CalendarEvent, day: date) -> bool:
        if day < event.event_date:
            return False
        if event.repeat == REPEAT_DAILY:
            return True
        if event.repeat == REPEAT_WEEKLY:
            return day.weekday() == event.event_date.weekday()
        return day == event.event_date

    @staticmethod
    def _next_occurrence(
        event: CalendarEvent, now: datetime
    ) -> datetime | None:
        if event.repeat == REPEAT_NONE:
            candidate = datetime.combine(event.event_date, event.event_time)
            return candidate if candidate >= now else None

        if event.repeat == REPEAT_WEEKLY:
            days_ahead = (event.event_date.weekday() - now.date().weekday()) % 7
            target = now.date() + timedelta(days=days_ahead)
            if target < event.event_date:
                target = event.event_date
            candidate = datetime.combine(target, event.event_time)
            if candidate < now:
                candidate += timedelta(days=7)
            return candidate

        target = now.date()
        if target < event.event_date:
            target = event.event_date
        candidate = datetime.combine(target, event.event_time)
        if candidate < now:
            candidate += timedelta(days=1)
        return candidate

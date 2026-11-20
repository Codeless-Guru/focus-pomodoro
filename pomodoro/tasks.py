"""任务计划存储。

任务与番茄钟状态分离：一个任务可以估算多个番茄，专注完成后自动累加当前任务进度。
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_TASKS_PATH = Path.home() / ".focus_pomodoro" / "tasks.json"


def _read_int(value: object, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


@dataclass
class Task:
    """一个可跟踪番茄进度的任务。"""

    id: str
    name: str
    estimate: int
    completed: int = 0
    active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "estimate": self.estimate,
            "completed": self.completed,
            "active": self.active,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task | None:
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            return None
        task_id = data.get("id")
        if not isinstance(task_id, str) or not task_id:
            task_id = uuid.uuid4().hex[:8]
        estimate = _read_int(data.get("estimate"), 1)
        completed = _read_int(data.get("completed"), 0)
        return cls(
            id=task_id,
            name=name.strip(),
            estimate=max(1, min(50, estimate)),
            completed=max(0, completed),
            active=bool(data.get("active", False)),
        )


class TaskStore:
    """负责任务的读写和当前任务进度更新。"""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else DEFAULT_TASKS_PATH
        self.tasks: list[Task] = self._load()

    def _load(self) -> list[Task]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            items = data.get("tasks", []) if isinstance(data, dict) else []
            if not isinstance(items, list):
                return []
            tasks = []
            for item in items:
                if isinstance(item, dict):
                    task = Task.from_dict(item)
                    if task is not None:
                        tasks.append(task)
            return tasks
        except (OSError, ValueError, TypeError):
            return []

    def save(self) -> None:
        """把任务列表写入 JSON 文件。"""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {"tasks": [task.to_dict() for task in self.tasks]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def add(self, name: str, estimate: int) -> Task:
        """新增任务；名称不能为空，估算番茄数限制在 1 到 50。"""
        cleaned = name.strip()
        if not cleaned:
            raise ValueError("任务名称不能为空")
        if isinstance(estimate, bool) or not isinstance(estimate, int):
            raise ValueError("估算番茄数必须是整数")
        if not 1 <= estimate <= 50:
            raise ValueError("估算番茄数必须在 1 到 50 之间")

        task = Task(
            id=uuid.uuid4().hex[:8],
            name=cleaned,
            estimate=estimate,
            active=not any(item.active for item in self.tasks),
        )
        self.tasks.append(task)
        self.save()
        return task

    def remove(self, task_id: str) -> None:
        """删除任务；如果删除的是当前任务，自动选中第一项。"""
        self.tasks = [task for task in self.tasks if task.id != task_id]
        if not any(task.active for task in self.tasks) and self.tasks:
            self.tasks[0].active = True
        self.save()

    def select(self, task_id: str) -> None:
        """把指定任务设为当前任务。"""
        found = False
        for task in self.tasks:
            task.active = task.id == task_id
            found = found or task.active
        if not found:
            raise ValueError("任务不存在")
        self.save()

    def active_task(self) -> Task | None:
        """返回当前任务。"""
        for task in self.tasks:
            if task.active:
                return task
        return None

    def record_focus(self) -> str | None:
        """为一个自然完成的专注番茄累加进度，返回刚完成的任务名。"""
        task = self.active_task()
        if task is None:
            return None
        task.completed += 1
        self.save()
        if task.completed >= task.estimate:
            return task.name
        return None

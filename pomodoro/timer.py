"""番茄钟核心计时逻辑。

本模块只负责阶段切换、剩余时间计算和完成次数统计，不依赖任何图形界面。
时钟通过参数注入，便于在测试中精确模拟时间流逝。
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable


# 时钟函数类型：返回单调递增的秒数。
Clock = Callable[[], float]


class Phase(str, Enum):
    """番茄钟当前所处的阶段。"""

    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"

    @property
    def label(self) -> str:
        """返回用于界面显示的中文阶段名称。"""
        return {
            Phase.FOCUS: "专注",
            Phase.SHORT_BREAK: "短休息",
            Phase.LONG_BREAK: "长休息",
        }[self]


def _require_int(name: str, value: object, minimum: int, maximum: int) -> None:
    """校验整数字段：不接受布尔值，并限制在允许范围内。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} 必须是整数")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} 必须在 {minimum} 到 {maximum} 之间")


@dataclass(frozen=True)
class TimerConfig:
    """番茄钟时长配置，单位为分钟。"""

    focus_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4

    def __post_init__(self) -> None:
        """在创建配置对象时立即校验所有字段。"""
        _require_int("专注时长", self.focus_minutes, 1, 180)
        _require_int("短休息时长", self.short_break_minutes, 1, 60)
        _require_int("长休息时长", self.long_break_minutes, 1, 90)
        _require_int("长休息轮次", self.sessions_before_long_break, 2, 12)

    @property
    def focus_seconds(self) -> int:
        return self.focus_minutes * 60

    @property
    def short_break_seconds(self) -> int:
        return self.short_break_minutes * 60

    @property
    def long_break_seconds(self) -> int:
        return self.long_break_minutes * 60


def seconds_for_phase(phase: Phase, config: TimerConfig) -> int:
    """根据当前阶段从配置中取得该阶段的总秒数。"""
    if phase is Phase.FOCUS:
        return config.focus_seconds
    if phase is Phase.SHORT_BREAK:
        return config.short_break_seconds
    return config.long_break_seconds


def format_duration(total_seconds: int) -> str:
    """把秒数格式化为 `分:秒` 文本，用于界面显示。"""
    seconds = max(0, int(total_seconds))
    minutes, remainder = divmod(seconds, 60)
    return f"{minutes:02d}:{remainder:02d}"


@dataclass(frozen=True)
class TimerEvent:
    """一次阶段变化事件，区分自然完成和手动跳过。"""

    kind: str
    from_phase: Phase
    to_phase: Phase

    @property
    def is_completion(self) -> bool:
        """是否为自然计时完成，而不是手动跳过。"""
        return self.kind == "completed"


@dataclass(frozen=True)
class TimerSnapshot:
    """某一时刻的只读计时快照，供界面渲染使用。"""

    phase: Phase
    remaining_seconds: float
    total_seconds: int
    is_running: bool
    completed_focus_sessions: int
    cycle_length: int
    cycle_index: int

    @property
    def remaining_whole_seconds(self) -> int:
        return math.ceil(max(0.0, self.remaining_seconds))

    @property
    def progress(self) -> float:
        if self.total_seconds <= 0:
            return 0.0
        elapsed = self.total_seconds - max(0.0, self.remaining_seconds)
        return min(1.0, max(0.0, elapsed / self.total_seconds))


class PomodoroTimer:
    """与界面无关的番茄钟状态机，时钟可注入以便测试。"""

    def __init__(
        self,
        config: TimerConfig | None = None,
        *,
        clock: Clock | None = None,
        auto_start_next: bool = True,
    ) -> None:
        """初始化计时器；默认从专注阶段、未运行状态开始。"""
        if not isinstance(auto_start_next, bool):
            raise ValueError("auto_start_next 必须是布尔值")
        self._config = config or TimerConfig()
        # 使用可注入时钟，测试时可用假时钟快进时间。
        self._clock: Clock = clock or time.monotonic
        self.auto_start_next = auto_start_next
        self._phase = Phase.FOCUS
        self._remaining = float(self._config.focus_seconds)
        self._deadline: float | None = None
        self._running = False
        self.completed_focus_sessions = 0

    @property
    def config(self) -> TimerConfig:
        return self._config

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """开始或继续当前阶段，按当前剩余时间设置截止时间。"""
        if self._running:
            return
        if self._remaining <= 0:
            self._remaining = float(seconds_for_phase(self._phase, self._config))
        self._deadline = self._clock() + self._remaining
        self._running = True

    def pause(self) -> None:
        """暂停计时，并保存此刻的剩余时间。"""
        if not self._running:
            return
        self._remaining = max(0.0, self._deadline - self._clock())
        self._running = False
        self._deadline = None

    def reset(self) -> None:
        """把当前阶段恢复为完整时长并暂停。"""
        self._running = False
        self._deadline = None
        self._remaining = float(seconds_for_phase(self._phase, self._config))

    def skip(self) -> TimerEvent:
        """手动跳到下一阶段，不计入已完成专注次数。"""
        return self._advance(completed=False)

    def update(self) -> TimerEvent | None:
        """根据当前时钟刷新状态；阶段结束则返回一次阶段变化事件。"""
        if not self._running or self._deadline is None:
            return None
        remaining = self._deadline - self._clock()
        if remaining > 0:
            self._remaining = remaining
            return None
        self._remaining = 0.0
        return self._advance(completed=True)

    def configure(
        self,
        config: TimerConfig,
        *,
        auto_start_next: bool | None = None,
    ) -> None:
        """应用新配置；时长变化时从新时长重新开始当前阶段。"""
        if not isinstance(config, TimerConfig):
            raise ValueError("config 必须是 TimerConfig")
        if auto_start_next is not None and not isinstance(auto_start_next, bool):
            raise ValueError("auto_start_next 必须是布尔值")

        changed = config != self._config
        self._config = config
        if changed:
            self._remaining = float(seconds_for_phase(self._phase, config))
            if self._running:
                self._deadline = self._clock() + self._remaining
        if auto_start_next is not None:
            self.auto_start_next = auto_start_next

    def snapshot(self) -> TimerSnapshot:
        """生成当前状态快照，供界面一次性读取并渲染。"""
        if self._running and self._deadline is not None:
            remaining = max(0.0, self._deadline - self._clock())
        else:
            remaining = self._remaining

        cycle = self._config.sessions_before_long_break
        if self._phase is Phase.FOCUS:
            cycle_index = self.completed_focus_sessions % cycle + 1
        elif self.completed_focus_sessions == 0:
            cycle_index = 1
        else:
            cycle_index = (self.completed_focus_sessions - 1) % cycle + 1

        return TimerSnapshot(
            phase=self._phase,
            remaining_seconds=remaining,
            total_seconds=seconds_for_phase(self._phase, self._config),
            is_running=self._running,
            completed_focus_sessions=self.completed_focus_sessions,
            cycle_length=cycle,
            cycle_index=cycle_index,
        )

    def _advance(self, *, completed: bool) -> TimerEvent:
        """切换到下一阶段。自然完成时累计专注次数，手动跳过时不累计。"""
        from_phase = self._phase
        was_running = self._running

        if from_phase is Phase.FOCUS:
            if completed:
                self.completed_focus_sessions += 1
                # 每完成设定轮数后进入长休息，否则进入短休息。
                if (
                    self.completed_focus_sessions
                    % self._config.sessions_before_long_break
                    == 0
                ):
                    to_phase = Phase.LONG_BREAK
                else:
                    to_phase = Phase.SHORT_BREAK
            else:
                to_phase = Phase.SHORT_BREAK
        else:
            to_phase = Phase.FOCUS

        self._phase = to_phase
        self._remaining = float(seconds_for_phase(to_phase, self._config))

        keep_running = was_running and (not completed or self.auto_start_next)
        if keep_running:
            self._running = True
            self._deadline = self._clock() + self._remaining
        else:
            self._running = False
            self._deadline = None

        return TimerEvent(
            kind="completed" if completed else "skipped",
            from_phase=from_phase,
            to_phase=to_phase,
        )

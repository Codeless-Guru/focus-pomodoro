import unittest

from pomodoro.timer import (
    Phase,
    PomodoroTimer,
    TimerConfig,
    format_duration,
)


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TimerConfigTests(unittest.TestCase):
    def test_defaults(self) -> None:
        config = TimerConfig()
        self.assertEqual(config.focus_seconds, 25 * 60)
        self.assertEqual(config.short_break_seconds, 5 * 60)
        self.assertEqual(config.long_break_seconds, 15 * 60)

    def test_rejects_invalid_values(self) -> None:
        with self.assertRaises(ValueError):
            TimerConfig(focus_minutes=0)
        with self.assertRaises(ValueError):
            TimerConfig(short_break_minutes=True)
        with self.assertRaises(ValueError):
            TimerConfig(sessions_before_long_break=1)


class PomodoroTimerTests(unittest.TestCase):
    def make_timer(
        self,
        clock: FakeClock,
        *,
        focus: int = 25,
        short: int = 5,
        long: int = 15,
        cycle: int = 4,
        auto_start_next: bool = True,
    ) -> PomodoroTimer:
        return PomodoroTimer(
            TimerConfig(
                focus_minutes=focus,
                short_break_minutes=short,
                long_break_minutes=long,
                sessions_before_long_break=cycle,
            ),
            clock=clock,
            auto_start_next=auto_start_next,
        )

    def test_counts_down_while_running(self) -> None:
        clock = FakeClock(100.0)
        timer = self.make_timer(clock)
        timer.start()

        clock.advance(10)
        self.assertIsNone(timer.update())
        snapshot = timer.snapshot()

        self.assertAlmostEqual(snapshot.remaining_seconds, 25 * 60 - 10)
        self.assertTrue(snapshot.is_running)

    def test_pause_preserves_remaining_time(self) -> None:
        clock = FakeClock()
        timer = self.make_timer(clock)
        timer.start()
        clock.advance(5)

        timer.pause()
        clock.advance(100)
        snapshot = timer.snapshot()

        self.assertAlmostEqual(snapshot.remaining_seconds, 25 * 60 - 5)
        self.assertFalse(snapshot.is_running)
        self.assertIsNone(timer.update())

    def test_focus_completion_switches_to_short_break(self) -> None:
        clock = FakeClock()
        timer = self.make_timer(clock, focus=1, short=2, long=3)

        timer.start()
        clock.advance(60)
        event = timer.update()

        self.assertIsNotNone(event)
        self.assertTrue(event.is_completion)
        self.assertIs(event.from_phase, Phase.FOCUS)
        self.assertIs(event.to_phase, Phase.SHORT_BREAK)
        snapshot = timer.snapshot()
        self.assertIs(snapshot.phase, Phase.SHORT_BREAK)
        self.assertAlmostEqual(snapshot.remaining_seconds, 120)
        self.assertEqual(snapshot.completed_focus_sessions, 1)

    def test_long_break_after_configured_number_of_focus_sessions(self) -> None:
        clock = FakeClock()
        timer = self.make_timer(clock, focus=1, short=2, long=3, cycle=4)

        for index in range(4):
            timer.start()
            clock.advance(60)
            event = timer.update()
            self.assertIsNotNone(event)
            self.assertIs(event.to_phase, Phase.LONG_BREAK if index == 3 else Phase.SHORT_BREAK)

            if index < 3:
                clock.advance(120)
                break_event = timer.update()
                self.assertIsNotNone(break_event)
                self.assertIs(break_event.to_phase, Phase.FOCUS)

        snapshot = timer.snapshot()
        self.assertEqual(snapshot.completed_focus_sessions, 4)
        self.assertIs(snapshot.phase, Phase.LONG_BREAK)
        self.assertAlmostEqual(snapshot.remaining_seconds, 180)
        self.assertEqual(snapshot.cycle_index, 4)

    def test_break_completion_returns_to_focus(self) -> None:
        clock = FakeClock()
        timer = self.make_timer(clock, focus=1, short=2)

        timer.start()
        clock.advance(60)
        timer.update()
        clock.advance(120)
        event = timer.update()

        self.assertIs(event.to_phase, Phase.FOCUS)
        self.assertEqual(timer.snapshot().completed_focus_sessions, 1)

    def test_skip_does_not_count_as_completed(self) -> None:
        clock = FakeClock()
        timer = self.make_timer(clock, focus=1, short=2)

        timer.start()
        clock.advance(30)
        event = timer.skip()

        self.assertEqual(event.kind, "skipped")
        self.assertIs(event.to_phase, Phase.SHORT_BREAK)
        snapshot = timer.snapshot()
        self.assertEqual(snapshot.completed_focus_sessions, 0)
        self.assertTrue(snapshot.is_running)
        self.assertAlmostEqual(snapshot.remaining_seconds, 120)

    def test_reset_restores_phase_duration_and_pauses(self) -> None:
        clock = FakeClock()
        timer = self.make_timer(clock, focus=1)

        timer.start()
        clock.advance(30)
        timer.reset()
        snapshot = timer.snapshot()

        self.assertAlmostEqual(snapshot.remaining_seconds, 60)
        self.assertFalse(snapshot.is_running)

    def test_auto_start_next_can_be_disabled(self) -> None:
        clock = FakeClock()
        timer = self.make_timer(clock, focus=1, short=2, auto_start_next=False)

        timer.start()
        clock.advance(60)
        event = timer.update()
        snapshot = timer.snapshot()

        self.assertIsNotNone(event)
        self.assertIs(snapshot.phase, Phase.SHORT_BREAK)
        self.assertFalse(snapshot.is_running)
        self.assertAlmostEqual(snapshot.remaining_seconds, 120)

    def test_configure_resets_current_phase(self) -> None:
        clock = FakeClock()
        timer = self.make_timer(clock, focus=1)
        timer.start()
        clock.advance(30)

        timer.configure(TimerConfig(focus_minutes=3, short_break_minutes=2))

        self.assertAlmostEqual(timer.snapshot().remaining_seconds, 180)
        self.assertTrue(timer.is_running)


class FormatDurationTests(unittest.TestCase):
    def test_format(self) -> None:
        self.assertEqual(format_duration(0), "00:00")
        self.assertEqual(format_duration(65), "01:05")
        self.assertEqual(format_duration(3661), "61:01")


if __name__ == "__main__":
    unittest.main()

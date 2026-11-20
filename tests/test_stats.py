import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from pomodoro.stats import DailyStat, StatsStore


class StatsStoreTests(unittest.TestCase):
    def test_record_and_summarize(self) -> None:
        today = date(2026, 11, 21)
        with tempfile.TemporaryDirectory() as directory:
            store = StatsStore(
                Path(directory) / "stats.json",
                today_provider=lambda: today,
            )
            store.record_focus(25)
            store.record_focus(50)

            summary = store.summary()

            self.assertEqual(summary.total_pomodoros, 2)
            self.assertEqual(summary.total_minutes, 75)
            self.assertEqual(summary.today_pomodoros, 2)
            self.assertEqual(summary.week_pomodoros, 2)
            self.assertEqual(summary.streak_days, 1)
            self.assertEqual(summary.last_7_days[-1].pomodoros, 2)

    def test_streak_counts_consecutive_days(self) -> None:
        today = date(2026, 11, 21)
        yesterday = today - timedelta(days=1)
        with tempfile.TemporaryDirectory() as directory:
            store = StatsStore(
                Path(directory) / "stats.json",
                today_provider=lambda: today,
            )
            store.days[yesterday] = DailyStat(yesterday, 1, 25)
            store.days[yesterday - timedelta(days=1)] = DailyStat(
                yesterday - timedelta(days=1), 2, 50
            )

            self.assertEqual(store.summary().streak_days, 2)

    def test_persistence_and_validation(self) -> None:
        today = date(2026, 11, 21)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.json"
            store = StatsStore(path, today_provider=lambda: today)
            with self.assertRaises(ValueError):
                store.record_focus(0)

            store.record_focus(25)
            reloaded = StatsStore(path, today_provider=lambda: today)

            self.assertEqual(reloaded.summary().today_pomodoros, 1)


if __name__ == "__main__":
    unittest.main()

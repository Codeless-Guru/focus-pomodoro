import tempfile
import unittest
from datetime import date, datetime, time
from pathlib import Path

from pomodoro.calendar_store import CalendarStore, REPEAT_DAILY, REPEAT_WEEKLY


class CalendarStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "calendar.json"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_events_are_saved_and_reloaded(self) -> None:
        store = CalendarStore(self.path)
        event = store.add(
            "项目评审",
            date(2026, 11, 21),
            time(14, 30),
            note="带上线清单",
        )

        reloaded = CalendarStore(self.path)
        self.assertEqual(len(reloaded.events), 1)
        self.assertEqual(reloaded.events[0].title, event.title)
        self.assertEqual(reloaded.events[0].note, "带上线清单")

    def test_daily_and_weekly_events_appear_on_expected_days(self) -> None:
        store = CalendarStore(self.path)
        store.add("每日站会", date(2026, 11, 21), time(9, 0), repeat=REPEAT_DAILY)
        store.add("周复盘", date(2026, 11, 21), time(17, 0), repeat=REPEAT_WEEKLY)

        self.assertEqual(len(store.events_for(date(2026, 11, 22))), 1)
        self.assertEqual(len(store.events_for(date(2026, 11, 28))), 2)
        titles = [event.title for event in store.events_for(date(2026, 11, 28))]
        self.assertEqual(titles, ["每日站会", "周复盘"])

    def test_due_events_only_alert_once_inside_window(self) -> None:
        store = CalendarStore(self.path)
        event = store.add("喝水", date(2026, 11, 21), time(9, 0))
        now = datetime(2026, 11, 21, 9, 3)

        due = store.due_events(now)
        self.assertEqual([item.id for item in due], [event.id])

        store.mark_triggered(event.id, now)
        self.assertEqual(store.due_events(now), ())
        self.assertEqual(store.due_events(datetime(2026, 11, 21, 10, 0)), ())

    def test_next_summary_contains_time_and_title(self) -> None:
        store = CalendarStore(self.path)
        store.add("晨会", date(2026, 11, 21), time(9, 0))
        summary = store.next_summary(datetime(2026, 11, 21, 8, 30))

        self.assertIn("11-21 09:00", summary)
        self.assertIn("晨会", summary)


if __name__ == "__main__":
    unittest.main()

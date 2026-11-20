import tempfile
import unittest
from pathlib import Path

from pomodoro.tasks import TaskStore


class TaskStoreTests(unittest.TestCase):
    def test_add_and_select_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = TaskStore(Path(directory) / "tasks.json")
            first = store.add("写发布说明", 2)
            second = store.add("整理资料", 1)

            self.assertTrue(first.active)
            self.assertFalse(second.active)
            self.assertIs(store.active_task(), first)

            store.select(second.id)
            self.assertIs(store.active_task(), second)

    def test_record_focus_increments_active_task(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = TaskStore(Path(directory) / "tasks.json")
            task = store.add("写一个番茄", 1)

            finished = store.record_focus()

            self.assertEqual(finished, "写一个番茄")
            self.assertEqual(task.completed, 1)

    def test_validation_and_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tasks.json"
            store = TaskStore(path)
            with self.assertRaises(ValueError):
                store.add("", 1)
            with self.assertRaises(ValueError):
                store.add("任务", 0)

            store.add("复盘本周", 3)
            reloaded = TaskStore(path)

            self.assertEqual(len(reloaded.tasks), 1)
            self.assertEqual(reloaded.tasks[0].name, "复盘本周")
            self.assertEqual(reloaded.tasks[0].estimate, 3)


if __name__ == "__main__":
    unittest.main()

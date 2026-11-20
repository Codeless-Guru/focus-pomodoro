import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from pomodoro.feature_dialogs import RewardDialog, StatsDialog, TaskDialog
from pomodoro.stats import StatsStore
from pomodoro.tasks import TaskStore
from pomodoro.theme_presets import get_theme


class FeatureDialogTests(unittest.TestCase):
    def test_dialogs_can_be_created_and_closed(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                theme = get_theme("fresh")
                tasks = TaskStore(base / "tasks.json")
                stats = StatsStore(base / "stats.json")
                tasks.add("写测试", 2)

                task_dialog = TaskDialog(root, tasks, theme)
                root.update()
                self.assertEqual(len(task_dialog.tree.get_children()), 1)
                task_dialog.close()

                stats_dialog = StatsDialog(root, stats, tasks, theme)
                root.update()
                self.assertEqual(stats_dialog.unlocked, ())
                stats_dialog.close()

                reward_dialog = RewardDialog(root, theme)
                root.update()
                reward_dialog.start_spin()
                root.update()
                self.assertTrue(reward_dialog.reward_var.get())
                reward_dialog.close()

                root.update()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    unittest.main()

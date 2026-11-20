import tempfile
import tkinter as tk
import unittest
from datetime import date, time
from pathlib import Path

from pomodoro.calendar_dialog import CalendarDialog
from pomodoro.calendar_store import CalendarStore
from pomodoro.theme_presets import get_theme


class CalendarDialogTests(unittest.TestCase):
    def test_dialog_can_be_opened(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                store = CalendarStore(Path(directory) / "calendar.json")
                dialog = CalendarDialog(root, store, get_theme("apple_light"))
                root.update()
                self.assertTrue(dialog.winfo_exists())
                self.assertTrue(hasattr(dialog, "dialog_canvas"))
                self.assertTrue(hasattr(dialog, "all_tree"))
                dialog.close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_event_can_be_added_from_dialog_form(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                store = CalendarStore(Path(directory) / "calendar.json")
                dialog = CalendarDialog(root, store, get_theme("apple_light"))
                root.update()

                dialog.title_var.set("写发布方案")
                dialog.time_var.set("10:30")
                dialog.repeat_var.set("每天")
                dialog.note_var.set("完成后同步给团队")
                dialog.save_event()

                self.assertEqual(len(store.events), 1)
                self.assertEqual(store.events[0].title, "写发布方案")
                self.assertEqual(store.events[0].repeat_label(), "每天")
                self.assertEqual(store.events[0].note, "完成后同步给团队")
                self.assertEqual(len(dialog.all_tree.get_children()), 1)
                self.assertEqual(dialog.all_count_label.cget("text"), "共 1 条")

                dialog.close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_all_event_selection_jumps_to_event_date(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            with tempfile.TemporaryDirectory() as directory:
                store = CalendarStore(Path(directory) / "calendar.json")
                store.add("月度复盘", date(2026, 12, 15), time(16, 0))
                dialog = CalendarDialog(root, store, get_theme("apple_light"))
                root.update()

                item = dialog.all_tree.get_children()[0]
                dialog.all_tree.selection_set(item)
                dialog._on_all_tree_select()

                self.assertEqual(dialog.selected_date, date(2026, 12, 15))
                self.assertEqual(dialog.title_var.get(), "月度复盘")
                self.assertEqual(dialog.time_var.get(), "16:00")

                dialog.close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    unittest.main()

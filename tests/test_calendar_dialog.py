import tempfile
import tkinter as tk
import unittest
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
                dialog.close()
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    unittest.main()

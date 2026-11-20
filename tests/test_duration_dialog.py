import tkinter as tk
import unittest

from pomodoro.duration_dialog import CUSTOM_VALUE, DurationDialog
from pomodoro.duration_presets import PRESETS
from pomodoro.timer import TimerConfig


class DurationDialogTests(unittest.TestCase):
    def test_preset_can_be_selected_and_applied(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        applied: list[TimerConfig] = []
        try:
            preset = PRESETS[1]
            dialog = DurationDialog(root, TimerConfig(), lambda config: applied.append(config))
            root.update()

            dialog.preset_var.set(preset.name)
            dialog._select_preset()
            root.update()

            self.assertEqual(dialog.vars["focus_minutes"].get(), preset.config.focus_minutes)
            self.assertEqual(
                dialog.vars["short_break_minutes"].get(),
                preset.config.short_break_minutes,
            )
            self.assertEqual(dialog.preset_var.get(), preset.name)

            dialog.apply_and_close()
            root.update()

            self.assertEqual(applied, [preset.config])
            self.assertEqual(dialog.result, preset.config)
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def test_editing_value_switches_to_custom(self) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"当前环境没有图形界面：{exc}")
            return

        root.withdraw()
        try:
            dialog = DurationDialog(root, TimerConfig(), lambda _config: None)
            root.update()

            dialog.vars["focus_minutes"].set(30)
            root.update()

            self.assertEqual(dialog.preset_var.get(), CUSTOM_VALUE)
            dialog.cancel()
            root.update()
            self.assertIsNone(dialog.result)
        finally:
            try:
                root.destroy()
            except tk.TclError:
                pass


if __name__ == "__main__":
    unittest.main()

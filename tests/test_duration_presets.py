import unittest

from pomodoro.duration_presets import PRESETS, DurationPreset, find_preset
from pomodoro.timer import TimerConfig


class DurationPresetTests(unittest.TestCase):
    def test_presets_are_valid(self) -> None:
        self.assertGreaterEqual(len(PRESETS), 4)
        for preset in PRESETS:
            self.assertIsInstance(preset, DurationPreset)
            self.assertIsInstance(preset.config, TimerConfig)
            self.assertIn(str(preset.config.focus_minutes), preset.summary)

    def test_find_preset_matches_exact_config(self) -> None:
        preset = PRESETS[0]
        matched = find_preset(preset.config)
        self.assertIs(matched, preset)

    def test_find_preset_returns_none_for_custom_config(self) -> None:
        self.assertIsNone(find_preset(TimerConfig(33, 7, 11, 5)))


if __name__ == "__main__":
    unittest.main()

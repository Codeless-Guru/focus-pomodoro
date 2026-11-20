import unittest

from pomodoro.ui_utils import blend_color


class UiUtilsTests(unittest.TestCase):
    def test_blend_color_endpoints_and_midpoint(self) -> None:
        self.assertEqual(blend_color("#000000", "#FFFFFF", 0), "#000000")
        self.assertEqual(blend_color("#000000", "#FFFFFF", 1), "#FFFFFF")
        self.assertEqual(blend_color("#000000", "#FFFFFF", 0.5), "#808080")

    def test_blend_color_clamps_ratio(self) -> None:
        self.assertEqual(blend_color("#000000", "#FFFFFF", -1), "#000000")
        self.assertEqual(blend_color("#000000", "#FFFFFF", 2), "#FFFFFF")


if __name__ == "__main__":
    unittest.main()

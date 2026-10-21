from pathlib import Path
import unittest


class LoginUIAnimationTests(unittest.TestCase):
    def setUp(self):
        self.source = Path("public/login.html").read_text(encoding="utf-8")

    def test_login_uses_emotion_instead_of_legacy_style_block(self):
        self.assertIn("/vendor/emotion-css.umd.min.js", self.source)
        self.assertIn("const { css, keyframes, injectGlobal } = window.emotion;", self.source)
        self.assertIn("css`", self.source)
        self.assertIn("keyframes`", self.source)
        self.assertIn("injectGlobal`", self.source)
        self.assertNotIn("<style", self.source.lower())

    def test_login_animations_are_layered_and_respect_reduced_motion(self):
        for token in ("cardEntrance", "pageFloat", "iconPulse", "prefers-reduced-motion"):
            self.assertIn(token, self.source)

        self.assertGreaterEqual(self.source.count("animation-delay"), 2)

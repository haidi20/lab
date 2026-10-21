from pathlib import Path
import unittest


class EmotionStandardTests(unittest.TestCase):
    def test_emotion_is_documented_as_ui_standard(self):
        agents = Path("AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("## UI/UX Animation Standard: Emotion", agents)
        self.assertIn("Emotion adalah standar WAJIB", agents)
        self.assertIn("TIDAK BOLEH memakai blok `<style>` lama", agents)
        self.assertIn("skills/emotion-ui-ux/SKILL.md", agents)

    def test_emotion_skill_defines_required_contract(self):
        skill = Path("skills/emotion-ui-ux/SKILL.md").read_text(encoding="utf-8")

        self.assertIn("name: emotion-ui-ux", skill)
        self.assertIn("description:", skill)
        self.assertIn("JANGAN gunakan blok `<style>`", skill)
        self.assertIn("css`", skill)
        self.assertIn("keyframes`", skill)
        self.assertIn("prefers-reduced-motion", skill)
        self.assertIn("public/vendor/emotion-css.umd.min.js", skill)

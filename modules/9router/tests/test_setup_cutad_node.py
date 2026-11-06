"""Tests untuk modules/9router/setup_cutad_node.js (bridge Codex -> cutad).

Script ini membuat node provider cutad di 9Router lokal dengan apiType
'chat' (upstream cutad hanya stabil di chat completions) + koneksi API key
+ gateway key sk_9router. Codex modern (0.149+) mewajibkan wire_api
'responses', jadi 9Router dipakai sebagai jembatan Responses -> Chat.
"""
import os
import unittest

SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "setup_cutad_node.js",
)


class TestScriptSetupCutad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SCRIPT, encoding="utf-8") as f:
            cls.source = f.read()

    def test_file_script_ada(self) -> None:
        self.assertTrue(os.path.isfile(SCRIPT))

    def test_apitye_chat_bukan_responses(self) -> None:
        # Upstream cutad menolak stream di /v1/responses; node harus 'chat'.
        self.assertIn("apiType", self.source)
        self.assertIn('"chat"', self.source)

    def test_base_url_dan_prefix_cutad(self) -> None:
        self.assertIn("https://ai.cutad.web.id/v1", self.source)
        self.assertIn('prefix: "cd"', self.source)

    def test_idempoten_cek_node_dan_koneksi_sudah_ada(self) -> None:
        self.assertIn("sudah ada", self.source)
        self.assertIn("getProviderNodes", self.source)
        self.assertIn("getProviders", self.source)

    def test_membuat_gateway_key_sk_9router(self) -> None:
        self.assertIn("createApiKey", self.source)
        self.assertIn("sk_9router", self.source)


if __name__ == "__main__":
    unittest.main()

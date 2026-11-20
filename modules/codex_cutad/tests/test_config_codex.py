"""Tests untuk modules/codex_cutad/config_codex.py (TDD).

Config `~/.codex/config.toml` harus mengarahkan Codex ke shim lokal, bukan
langsung ke gateway: gateway menolak `role:"developer"` dan
`previous_response_id` yang selalu dikirim Codex 0.167.1.
"""
import importlib
import unittest

cfg = importlib.import_module("modules.codex_cutad.config_codex")

CONTOH = """\
model = "deepseek-v4-pro"
model_provider = "cutad"
model_context_window = 1000000
model_max_output_tokens = 15000

[model_providers.cutad]
name = "Cutad AI"
base_url = "https://ai.cutad.web.id/v1"
env_key = "CODEX_CUTAD_API_KEY"
wire_api = "responses"
"""

SUDAH_SHIP = """\
model = "deepseek-v4-pro"
model_provider = "cutad"
model_context_window = 1000000

[model_providers.cutad]
name = "Cutad AI (via shim lokal)"
base_url = "http://127.0.0.1:8787/v1"
env_key = "CODEX_CUTAD_API_KEY"
wire_api = "responses"
"""


class TestDeteksi(unittest.TestCase):
    def test_gateway_langsung_perlu_shim(self) -> None:
        self.assertTrue(cfg.perlu_shim(CONTOH))

    def test_config_shim_dianggap_ok(self) -> None:
        self.assertFalse(cfg.perlu_shim(SUDAH_SHIP))

    def test_config_tanpa_provider_cutad_tidak_disentuh(self) -> None:
        self.assertFalse(cfg.perlu_shim('model = "x"\n'))


class TestArahkanKeShim(unittest.TestCase):
    def test_base_url_diganti_ke_loopback(self) -> None:
        hasil = cfg.arahkan_ke_shim(CONTOH)
        self.assertIn('base_url = "http://127.0.0.1:8787/v1"', hasil)
        self.assertNotIn("ai.cutad.web.id/v1", hasil)

    def test_wire_api_tetap_responses(self) -> None:
        hasil = cfg.arahkan_ke_shim(CONTOH)
        self.assertIn('wire_api = "responses"', hasil)

    def test_env_key_dipertahankan(self) -> None:
        hasil = cfg.arahkan_ke_shim(CONTOH)
        self.assertIn('env_key = "CODEX_CUTAD_API_KEY"', hasil)

    def test_model_dan_context_dipertahankan(self) -> None:
        hasil = cfg.arahkan_ke_shim(CONTOH)
        self.assertIn('model = "deepseek-v4-pro"', hasil)
        self.assertIn("model_context_window = 1000000", hasil)

    def test_model_max_output_tokens_dihapus(self) -> None:
        """Codex 0.167.1 mengabaikannya dan mencetak warning deprecation."""
        hasil = cfg.arahkan_ke_shim(CONTOH)
        self.assertNotIn("model_max_output_tokens", hasil)

    def test_idempoten(self) -> None:
        sekali = cfg.arahkan_ke_shim(CONTOH)
        dua = cfg.arahkan_ke_shim(sekali)
        self.assertEqual(sekali, dua)

    def test_tabel_proyek_dipertahankan(self) -> None:
        isi = CONTOH + "\n[projects.'d:\\projects\\karta_spa']\ntrust_level = \"trusted\"\n"
        hasil = cfg.arahkan_ke_shim(isi)
        self.assertIn("[projects.'d:\\projects\\karta_spa']", hasil)
        self.assertIn('trust_level = "trusted"', hasil)

    def test_tabel_provider_lain_dipertahankan(self) -> None:
        isi = CONTOH + '\n[model_providers.lain]\nbase_url = "https://contoh.test/v1"\n'
        hasil = cfg.arahkan_ke_shim(isi)
        self.assertIn("[model_providers.lain]", hasil)
        self.assertIn('base_url = "https://contoh.test/v1"', hasil)


class TestPort(unittest.TestCase):
    def test_port_default_8787(self) -> None:
        self.assertEqual(cfg.PORT, 8787)

    def test_url_shim(self) -> None:
        self.assertEqual(cfg.BASE_SHIM, "http://127.0.0.1:8787/v1")


if __name__ == "__main__":
    unittest.main()
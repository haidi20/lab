"""Tests untuk modules/codex_cutad/fix_wire_api.py.

Codex CLI error `upstream_error` / `unsupported_parameter` saat pakai
provider cutad karena config memakai `wire_api = "responses"` padahal
proxy ai.cutad.web.id menolak `stream: true` di `/v1/responses`.
Endpoint `/v1/chat/completions` terbukti mendukung streaming + tools +
reasoning untuk ketiga model. Fix: wire_api harus "chat".
"""
import importlib
import os
import unittest
from unittest import mock

fix = importlib.import_module("modules.codex_cutad.fix_wire_api")


class TestDeteksi(unittest.TestCase):
    def test_config_responses_terdeteksi_rusak(self) -> None:
        isi = 'model = "z-ai/glm-5.2"\nwire_api = "responses"\n'
        self.assertEqual(fix.wire_api_dari_config(isi), "responses")
        self.assertTrue(fix.perlu_perbaikan(isi))

    def test_config_chat_dianggap_sehat(self) -> None:
        isi = 'wire_api = "chat"\n'
        self.assertEqual(fix.wire_api_dari_config(isi), "chat")
        self.assertFalse(fix.perlu_perbaikan(isi))

    def test_tanpa_wire_api_di_remarks_sebagai_upstream_error_potensial(self) -> None:
        isi = 'model = "x"\n'
        self.assertIsNone(fix.wire_api_dari_config(isi))
        self.assertFalse(fix.perlu_perbaikan(isi))


class TestPerbaikan(unittest.TestCase):
    def test_responses_diubah_menjadi_chat(self) -> None:
        isi = 'model_provider = "cutad"\nwire_api = "responses"\n'
        hasil = fix.ubah_wire_api(isi)
        self.assertIn('wire_api = "chat"', hasil)
        self.assertNotIn('"responses"', hasil)

    def test_konten_lain_tidak_berubah(self) -> None:
        isi = (
            'model_provider = "cutad"\n'
            'model = "z-ai/glm-5.2"\n'
            'wire_api = "responses"\n'
            "\n"
            '[model_providers.cutad]\n'
            'base_url = "https://ai.cutad.web.id/v1"\n'
        )
        hasil = fix.ubah_wire_api(isi)
        self.assertIn('model = "z-ai/glm-5.2"', hasil)
        self.assertIn('base_url = "https://ai.cutad.web.id/v1"', hasil)
        # hanya 1 baris wire_api
        self.assertEqual(hasil.count("wire_api"), 1)

    def test_tanpa_baris_wire_api_menambahkan_setelah_model_provider(self) -> None:
        isi = 'model_provider = "cutad"\nmodel = "z-ai/glm-5.2"\n'
        hasil = fix.ubah_wire_api(isi)
        self.assertIn('wire_api = "chat"', hasil)
        # disisipkan sebelum baris model
        self.assertLess(
            hasil.index("wire_api"), hasil.index("model =")
        )


class TestTerapkan(unittest.TestCase):
    def test_file_diperbaiki_dan_dibackup(self) -> None:
        with mock.patch.dict(os.environ, {"CODEX_CONFIG": "/tmp/x.toml"}):
            with mock.patch("os.path.exists", return_value=True):
                pass  # placeholder, gunakan tmpdir nyata di bawah

        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.toml")
            with open(path, "w", encoding="utf-8") as f:
                f.write('wire_api = "responses"\n')

            hasil = fix.terapkan(path,backup_dir=tmp)

            self.assertEqual(hasil["status"], "fixed")
            self.assertEqual(hasil["dari"], "responses")
            self.assertEqual(hasil["ke"], "chat")
            with open(path, encoding="utf-8") as f:
                self.assertIn('wire_api = "chat"', f.read())
            backup_files = [
                fn for fn in os.listdir(tmp) if fn.startswith("config.toml.bak-")
            ]
            self.assertEqual(len(backup_files), 1)
            with open(os.path.join(tmp, backup_files[0]), encoding="utf-8") as f:
                self.assertIn('"responses"', f.read())

    def test_sudah_chat_tidak_rewrite(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.toml")
            with open(path, "w", encoding="utf-8") as f:
                f.write('wire_api = "chat"\n')

            hasil = fix.terapkan(path, backup_dir=tmp)

            self.assertEqual(hasil["status"], "sudah-ok")


if __name__ == "__main__":
    unittest.main()

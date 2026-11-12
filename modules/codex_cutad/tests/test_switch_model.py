"""Tests untuk modules/codex_cutad/switch_model.py.

Ganti model DEFAULT Codex (panel Cursor + CLI) dari GLM 5.2 ke Tencent
Hy4 preview. Bukan sekadar ganti string `model`: Hy4 preview WAJIB lewat
shim ([model_providers.cutad] -> 127.0.0.1:8787) karena CutadAI menolak
role:"developer" (kode 11128) khusus model ini, sementara Codex 0.167.1
responses-only selalu mengirim role tersebut.
"""
import importlib
import os
import tempfile
import unittest

import tomli

switch = importlib.import_module("modules.codex_cutad.switch_model")
probe = importlib.import_module("modules.codex_cutad.probe_model")

# Potongan config menyerupai ~/.codex/config.toml aktif (GLM 5.2).
CONFIG_GLM = """\
# Codex global config - dipakai panel Codex di Cursor DAN codex CLI terminal.
model = "z-ai/glm-5.2"
model_provider = "cutad-direct"
model_context_window = 1000000
model_reasoning_effort = "high"

approval_policy = "never"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true

[windows]
sandbox = "elevated"

[projects.'d:\\learns\\random']
trust_level = "trusted"

[tui]
screen_reader_detection_done = true

[model_providers.cutad-direct]
name = "CutadAI (direct)"
base_url = "https://ai.cutad.web.id/v1"
wire_api = "responses"
experimental_bearer_token = "cag_TESTTOKEN"

[model_providers.cutad]
name = "CutadAI (via hy4 shim)"
base_url = "http://127.0.0.1:8787/v1"
wire_api = "responses"
experimental_bearer_token = "cag_TESTTOKEN"
"""


def _parse(isi):
    """Parse TOML; gagal bila struktur tidak valid."""
    return tomli.loads(isi)


class TestDeteksi(unittest.TestCase):
    def test_config_glm_terdeteksi_bukan_hy4(self):
        self.assertFalse(switch.sudah_hy4(CONFIG_GLM))
        self.assertEqual(switch.model_dari_config(CONFIG_GLM), "z-ai/glm-5.2")
        self.assertEqual(
            switch.provider_dari_config(CONFIG_GLM), "cutad-direct"
        )

    def test_config_hy4_terdeteksi_sudah_benar(self):
        self.assertTrue(switch.sudah_hy4(switch.ubah_ke_hy4(CONFIG_GLM)))

    def test_deteksi_tanpa_kunci_top_level(self):
        self.assertIsNone(switch.model_dari_config("[tui]\nx = 1\n"))
        self.assertIsNone(switch.provider_dari_config("[tui]\nx = 1\n"))


class TestPerubahan(unittest.TestCase):
    def setUp(self):
        self.hasil = switch.ubah_ke_hy4(CONFIG_GLM)

    def test_model_dan_provider_diganti(self):
        self.assertIn('model = "tencent/hy4-preview"', self.hasil)
        self.assertIn('model_provider = "cutad"', self.hasil)
        self.assertNotIn('"z-ai/glm-5.2"', self.hasil)
        self.assertNotIn('"cutad-direct"', self.hasil.split("[model_providers")[0])

    def test_hasil_tetap_toml_yang_valid(self):
        data = _parse(self.hasil)
        self.assertEqual(data["model"], "tencent/hy4-preview")
        self.assertEqual(data["model_provider"], "cutad")

    def test_kunci_top_level_tetap_sebelum_header_tabel_pertama(self):
        baris = self.hasil.splitlines()
        idx_tabel = next(
            i for i, b in enumerate(baris) if b.strip().startswith("[")
        )
        self.assertLess(
            next(i for i, b in enumerate(baris) if b.strip().startswith("model =")),
            idx_tabel,
        )
        self.assertLess(
            next(i for i, b in enumerate(baris)
                 if b.strip().startswith("model_provider =")),
            idx_tabel,
        )

    def test_provider_yang_dipilih_punya_tabel_shim(self):
        data = _parse(self.hasil)
        tabel = data["model_providers"][data["model_provider"]]
        self.assertEqual(tabel["base_url"], "http://127.0.0.1:8787/v1")
        self.assertEqual(tabel["wire_api"], "responses")

    def test_tabel_lain_tidak_berubah(self):
        for potongan in (
            "[model_providers.cutad-direct]",
            'base_url = "https://ai.cutad.web.id/v1"',
            "[projects.'d:\\learns\\random']",
            "[sandbox_workspace_write]",
            "[windows]",
            "[tui]",
        ):
            self.assertIn(potongan, self.hasil)

    def test_metadata_model_dipertahankan(self):
        self.assertIn("model_context_window = 1000000", self.hasil)
        self.assertIn('model_reasoning_effort = "high"', self.hasil)

    def test_tidak_menambah_model_max_output_tokens(self):
        # Codex 0.167.1 mengabaikan key ini -> jangan dipaksakan untuk Hy4.
        self.assertNotIn("model_max_output_tokens", self.hasil)

    def test_idempoten(self):
        self.assertEqual(switch.ubah_ke_hy4(self.hasil), self.hasil)

    def test_komentar_lama_tidak_didistorsi(self):
        self.assertIn("# Codex global config", self.hasil)


class TestTerapkan(unittest.TestCase):
    def test_file_ditulis_backup_dan_toml_valid(self):
        asli = switch.probe.kirim
        switch.probe.kirim = lambda *a, **k: {
            "status": 200, "kode": None, "teks": "PONG", "ok": True
        }
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = os.path.join(tmp, "config.toml")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(CONFIG_GLM)

                hasil = switch.terapkan(path, backup_dir=tmp)

                self.assertEqual(hasil["status"], "fixed")
                self.assertEqual(hasil["dari"], "z-ai/glm-5.2")
                self.assertEqual(hasil["ke"], "tencent/hy4-preview")
                with open(path, encoding="utf-8") as f:
                    baru = f.read()
                self.assertEqual(_parse(baru)["model"], "tencent/hy4-preview")
                self.assertEqual(_parse(baru)["model_provider"], "cutad")

                backup = [
                    fn for fn in os.listdir(tmp)
                    if fn.startswith("config.toml.bak-")
                ]
                self.assertEqual(len(backup), 1)
                with open(os.path.join(tmp, backup[0]), encoding="utf-8") as f:
                    self.assertIn('"z-ai/glm-5.2"', f.read())
        finally:
            switch.probe.kirim = asli

    def test_sudah_hy4_tidak_rewrite_dan_tidak_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "config.toml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(switch.ubah_ke_hy4(CONFIG_GLM))

            hasil = switch.terapkan(path, backup_dir=tmp)

            self.assertEqual(hasil["status"], "sudah-ok")
            self.assertEqual(
                [fn for fn in os.listdir(tmp) if ".bak-" in fn], []
            )



# --- Target model generik (2026-11-12: deepseek-v4-pro) ---------------------
# deepseek-v4-pro menerima role:"developer" (probe 200) tapi tetap butuh
# shim, karena Codex 0.167.1 selalu mengirim `previous_response_id` pada turn
# lanjutan sementara gateway CutadAI membalas 400 11128 "Upstream error.
# Contact support if this persists." untuk parameter itu. Shim juga melepas
# gzip (bug content-encoding) dan memakai certifi (root CA lama di Windows).
CONFIG_HY4 = """\
model = "tencent/hy4-preview"
model_provider = "cutad"
model_context_window = 1000000
model_reasoning_effort = "high"

[model_providers.cutad-direct]
base_url = "https://ai.cutad.web.id/v1"
wire_api = "responses"
experimental_bearer_token = "cag_TESTTOKEN"

[model_providers.cutad]
base_url = "http://127.0.0.1:8787/v1"
wire_api = "responses"
experimental_bearer_token = "cag_TESTTOKEN"
"""


class TestTargetModel(unittest.TestCase):
    def test_default_tetap_hy4(self):
        self.assertEqual(switch.MODEL_DEFAULT, "tencent/hy4-preview")
        self.assertTrue(switch.sudah_benar(CONFIG_HY4, "tencent/hy4-preview"))

    def test_config_dari_model_lain_belum_benar(self):
        self.assertFalse(switch.sudah_benar(CONFIG_HY4, "deepseek-v4-pro"))

    def test_provider_tetap_shim_dan_model_diganti(self):
        hasil = switch.ubah_model(CONFIG_HY4, "deepseek-v4-pro")
        data = _parse(hasil)
        self.assertEqual(data["model"], "deepseek-v4-pro")
        self.assertEqual(data["model_provider"], "cutad")
        self.assertEqual(
            data["model_providers"]["cutad"]["base_url"],
            "http://127.0.0.1:8787/v1",
        )
        self.assertEqual(
            data["model_providers"]["cutad-direct"]["base_url"],
            "https://ai.cutad.web.id/v1",
        )

    def test_idempoten_untuk_target_apa_pun(self):
        sekali = switch.ubah_model(CONFIG_HY4, "deepseek-v4-pro")
        self.assertEqual(switch.ubah_model(sekali, "deepseek-v4-pro"), sekali)

    def test_bisa_kembali_ke_hy4(self):
        hasil = switch.ubah_model(
            switch.ubah_model(CONFIG_HY4, "deepseek-v4-pro"),
            switch.MODEL_DEFAULT,
        )
        self.assertTrue(switch.sudah_benar(hasil, switch.MODEL_DEFAULT))

    def test_reasoning_effort_tidak_dipaksa(self):
        # Model non-reasoning bisa menolak efisiensi reasoning yang dipaksa.
        hasil = switch.ubah_model(CONFIG_HY4, "deepseek-v4-pro")
        self.assertIn('model_reasoning_effort = "high"', hasil)


class TestTerapkanProbe(unittest.TestCase):
    """Switch model HANYA ditulis setelah probe gateway 200 (anti 11128)."""

    def setUp(self):
        self._asli = switch.probe.kirim

    def tearDown(self):
        switch.probe.kirim = self._asli

    def _tulis(self, tmp):
        path = os.path.join(tmp, "config.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(CONFIG_HY4)
        return path

    def test_probe_gagal_tidak_menyentuh_file(self):
        switch.probe.kirim = lambda *a, **k: {
            "status": 400, "kode": "11128", "teks": "11128", "ok": False
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = self._tulis(tmp)
            hasil = switch.terapkan(path, target="deepseek-v4-pro")
            self.assertEqual(hasil["status"], "probe-gagal")
            self.assertEqual(hasil["kode"], "11128")
            with open(path, encoding="utf-8") as f:
                self.assertEqual(_parse(f.read())["model"], "tencent/hy4-preview")
            self.assertEqual(
                [fn for fn in os.listdir(tmp) if ".bak-" in fn], []
            )

    def test_probe_ok_menulis_dan_backup(self):
        switch.probe.kirim = lambda *a, **k: {
            "status": 200, "kode": None, "teks": "PONG", "ok": True
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = self._tulis(tmp)
            hasil = switch.terapkan(path, target="deepseek-v4-pro")
            self.assertEqual(hasil["status"], "fixed")
            self.assertEqual(hasil["dari"], "tencent/hy4-preview")
            self.assertEqual(hasil["ke"], "deepseek-v4-pro")
            with open(path, encoding="utf-8") as f:
                self.assertEqual(_parse(f.read())["model"], "deepseek-v4-pro")
            self.assertEqual(
                len([fn for fn in os.listdir(tmp) if ".bak-" in fn]), 1
            )

    def test_target_sama_dengan_config_tidak_probe_ulang(self):
        dipanggil = []
        switch.probe.kirim = lambda *a, **k: dipanggil.append(1) or {
            "status": 200, "kode": None, "teks": "PONG", "ok": True
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = self._tulis(tmp)
            hasil = switch.terapkan(path)
            self.assertEqual(hasil["status"], "sudah-ok")
            self.assertEqual(dipanggil, [])


if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()

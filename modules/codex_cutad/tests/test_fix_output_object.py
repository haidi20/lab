"""Tests untuk modules/codex_cutad/fix_output_object.py.

Latar (2026-11-24): jawaban Codex tampil sebagai `[object Object]...` karena
`~/.codex/config.toml` menunjuk 9router (`127.0.0.1:20128`, model combo `cd`)
yang mengirim `response.output_text.delta` dengan `delta` berupa array objek
reasoning. Perbaikan sisi klien: arahkan provider ke shim lokal
(`127.0.0.1:8787`) DAN ganti `model` ke nama model asli, karena `cd` hanya ada
di 9router.

Fungsi inti murni string->string (mudah diuji); penulisan file + backup
dilakukan `terapkan`, dan model TIDAK ditulis sebelum probe 200.
"""
import importlib
import os
import tempfile
import unittest
from unittest import mock

modul = importlib.import_module("modules.codex_cutad.fix_output_object")

CONFIG_9ROUTER = '''model = "cd"
model_provider = "cutad"
model_context_window = 200000

[model_providers.cutad]
name = "Cutad AI"
base_url = "http://127.0.0.1:20128/v1"
experimental_bearer_token = "sk-rahasia"
wire_api = "responses"

[projects.'d:\\\\projects\\\\klinik-git']
trust_level = "trusted"

[windows]
sandbox = "elevated"
'''


class TestDeteksi9router(unittest.TestCase):
    def test_config_9router_terdeteksi(self) -> None:
        self.assertTrue(modul.lewat_9router(CONFIG_9ROUTER))

    def test_config_shim_tidak_terdeteksi(self) -> None:
        isi = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        self.assertFalse(modul.lewat_9router(isi))

    def test_config_tanpa_provider_tidak_terdeteksi(self) -> None:
        self.assertFalse(modul.lewat_9router('model = "gpt-5"\n'))

    def test_port_9router_lain_juga_terdeteksi(self) -> None:
        isi = CONFIG_9ROUTER.replace("20128", "20129")
        self.assertTrue(modul.lewat_9router(isi))


class TestUbahKeShim(unittest.TestCase):
    def test_base_url_diarahkan_ke_shim(self) -> None:
        baru = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        self.assertIn('base_url = "%s"' % modul.BASE_SHIM, baru)
        self.assertNotIn("20128", baru)

    def test_model_diganti_dari_combo_ke_model_asli(self) -> None:
        baru = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        self.assertIn('model = "deepseek-v4-pro"', baru)
        self.assertNotIn('model = "cd"', baru)

    def test_provider_tetap_cutad(self) -> None:
        baru = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        self.assertIn('model_provider = "cutad"', baru)

    def test_tabel_lain_dipertahankan(self) -> None:
        baru = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        self.assertIn("[projects.", baru)
        self.assertIn("[windows]", baru)
        self.assertIn('sandbox = "elevated"', baru)

    def test_token_tidak_hilang(self) -> None:
        baru = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        self.assertIn('experimental_bearer_token = "sk-rahasia"', baru)

    def test_idempoten(self) -> None:
        sekali = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        dua = modul.ubah_ke_shim(sekali, "deepseek-v4-pro")
        self.assertEqual(sekali, dua)

    def test_wire_api_tetap_responses(self) -> None:
        baru = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        self.assertIn('wire_api = "responses"', baru)

    def test_isi_asli_tidak_dimutasi(self) -> None:
        modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        self.assertIn("20128", CONFIG_9ROUTER)


class TestTerapkan(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.mkdtemp()
        self.path = os.path.join(self.folder, "config.toml")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(CONFIG_9ROUTER)

    def tearDown(self) -> None:
        for nama in os.listdir(self.folder):
            os.remove(os.path.join(self.folder, nama))
        os.rmdir(self.folder)

    @staticmethod
    def _ok(*a, **k):
        return {"ok": True, "status": 200, "teks": "OK"}

    def _bak(self):
        return [n for n in os.listdir(self.folder) if ".bak" in n]

    def test_probe_gagal_tidak_menulis_apa_pun(self) -> None:
        with mock.patch.object(modul.probe, "kirim",
                               return_value={"ok": False, "status": 400,
                                             "teks": "upstream_error"}):
            hasil = modul.terapkan(self.path, target="deepseek-v4-pro")
        self.assertEqual(hasil["status"], "probe-gagal")
        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(f.read(), CONFIG_9ROUTER)
        self.assertEqual(self._bak(), [])

    def test_probe_ok_menulis_dan_membuat_backup(self) -> None:
        with mock.patch.object(modul.probe, "kirim",
                               side_effect=self._ok):
            hasil = modul.terapkan(self.path, target="deepseek-v4-pro")
        self.assertEqual(hasil["status"], "fixed")
        with open(self.path, encoding="utf-8") as f:
            baru = f.read()
        self.assertIn(modul.BASE_SHIM, baru)
        self.assertNotIn("20128", baru)
        cadangan = self._bak()
        self.assertEqual(len(cadangan), 1)
        with open(os.path.join(self.folder, cadangan[0]),
                  encoding="utf-8") as f:
            self.assertEqual(f.read(), CONFIG_9ROUTER)

    def test_config_sudah_shim_tidak_menulis_ulang(self) -> None:
        baik = modul.ubah_ke_shim(CONFIG_9ROUTER, "deepseek-v4-pro")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(baik)
        with mock.patch.object(modul.probe, "kirim",
                               side_effect=self._ok):
            hasil = modul.terapkan(self.path, target="deepseek-v4-pro")
        self.assertEqual(hasil["status"], "sudah-ok")
        self.assertEqual(self._bak(), [])


class TestGantiToken(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = importlib.import_module(
            "modules.codex_cutad.fix_output_object")

    def test_token_di_provider_diganti(self) -> None:
        isi = self.mod.ganti_token(CONFIG_9ROUTER, "cag_baru")
        self.assertIn('experimental_bearer_token = "cag_baru"', isi)
        self.assertNotIn("sk-lama", isi)

    def test_token_di_luar_provider_tidak_disentuh(self) -> None:
        isi = (CONFIG_9ROUTER
               + '\n[model_providers.lain]\ntoken_lain = "sk-lama"\n')
        hasil = self.mod.ganti_token(isi, "cag_baru")
        self.assertIn('token_lain = "sk-lama"', hasil)
        self.assertIn('experimental_bearer_token = "cag_baru"', hasil)

    def test_tanpa_token_mengembalikan_isi_apa_adanya(self) -> None:
        self.assertEqual(self.mod.ganti_token(CONFIG_9ROUTER, ""),
                         CONFIG_9ROUTER)


class TestTerapkanTokenBaru(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = importlib.import_module(
            "modules.codex_cutad.fix_output_object")
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "config.toml")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(CONFIG_9ROUTER)

    def test_probe_memakai_token_baru(self) -> None:
        pakai = []
        with mock.patch.object(self.mod.probe, "kirim",
                               side_effect=lambda *a: pakai.append(a) or
                               {"ok": True, "teks": "{}"}), \
                mock.patch.object(self.mod.probe, "token_dari_config",
                                  return_value="sk-lama"):
            self.mod.terapkan(self.path, target="deepseek-v4-pro",
                              token_baru="cag_baru")
        self.assertEqual(pakai[0][1], "cag_baru")

    def test_token_lama_diganti_di_file(self) -> None:
        with mock.patch.object(self.mod.probe, "kirim",
                               return_value={"ok": True, "teks": "{}"}):
            hasil = self.mod.terapkan(self.path, target="deepseek-v4-pro",
                                      token_baru="cag_baru")
        self.assertEqual(hasil["status"], "fixed")
        with open(self.path, encoding="utf-8") as f:
            isi = f.read()
        self.assertIn('experimental_bearer_token = "cag_baru"', isi)
        self.assertNotIn("sk-lama", isi)

    def test_probe_gagal_tidak_mengubah_token(self) -> None:
        with mock.patch.object(self.mod.probe, "kirim",
                               return_value={"ok": False, "status": 401,
                                             "teks": "invalid_api_key"}):
            hasil = self.mod.terapkan(self.path, target="deepseek-v4-pro",
                                      token_baru="cag_baru")
        self.assertEqual(hasil["status"], "probe-gagal")
        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(f.read(), CONFIG_9ROUTER)


class TestEkspos(unittest.TestCase):
    def test_paket_mengekspos_modul(self) -> None:
        paket = importlib.import_module("modules.codex_cutad")
        self.assertIs(paket.fix_output_object, modul)


if __name__ == "__main__":
    unittest.main()

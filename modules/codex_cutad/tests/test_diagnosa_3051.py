"""Tes daftar varian diagnosa gateway CutadAI.

`VARIAN` adalah kontrak uji: setiap field yang pernah ditolak gateway harus
punya varian di sini supaya bisa diverifikasi ulang dengan satu perintah.
"""
import importlib
import unittest

diagnosa = importlib.import_module("modules.codex_cutad.diagnosa_3051")


class TestVarianDiagnosa(unittest.TestCase):
    def test_field_retensi_ada(self) -> None:
        self.assertIn("store_false", diagnosa.VARIAN)
        self.assertIn("store_true", diagnosa.VARIAN)

    def test_effort_codex_dan_gateway_ada(self) -> None:
        for nama in ("reasoning_effort_none", "reasoning_effort_medium",
                     "reasoning_effort_high"):
            self.assertIn(nama, diagnosa.VARIAN)

    def test_payload_dasar_valid(self) -> None:
        self.assertEqual(diagnosa.DASAR["model"], "deepseek-v4-pro")
        self.assertIs(diagnosa.DASAR["stream"], True)
        self.assertNotIn("store", diagnosa.DASAR)

class TestPilihVarian(unittest.TestCase):
    def test_tanpa_filter_mengembalikan_semua(self) -> None:
        hasil = diagnosa.pilih_varian(diagnosa.VARIAN, None)
        self.assertEqual(hasil, diagnosa.VARIAN)

    def test_filter_subset_dan_urutan(self) -> None:
        hasil = diagnosa.pilih_varian(
            diagnosa.VARIAN, " store_true , reasoning_effort_medium ")
        self.assertEqual(list(hasil), ["store_true", "reasoning_effort_medium"])

    def test_filter_kosong_menghasilkan_kosong(self) -> None:
        self.assertEqual(diagnosa.pilih_varian(diagnosa.VARIAN, "  "), {})

    def test_nama_tak_dikenal_ditolak(self) -> None:
        with self.assertRaises(ValueError):
            diagnosa.pilih_varian(diagnosa.VARIAN, "store_true,tidak_ada")

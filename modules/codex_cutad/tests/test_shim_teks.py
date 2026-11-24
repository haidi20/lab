"""Tests untuk `shim.ratakan_teks` — normalisasi nilai teks Responses API.

Responses API mewajibkan `delta`, `text`, dan `output_text.text` bertipe
string. 9router@0.5.119 kadang mengirim array objek reasoning di posisi itu,
yang oleh Codex di-`String()` menjadi `[object Object]`. `ratakan_teks`
mengubah nilai apa pun menjadi string yang bisa dibaca, tanpa pernah
menghasilkan `[object Object]`.
"""
import importlib
import unittest

shim = importlib.import_module("modules.codex_cutad.shim")


class TestRatakanTeks(unittest.TestCase):
    def test_string_dikembalikan_apa_adanya(self) -> None:
        self.assertEqual(shim.ratakan_teks("halo"), "halo")

    def test_none_menjadi_string_kosong(self) -> None:
        self.assertEqual(shim.ratakan_teks(None), "")

    def test_array_text_digabung(self) -> None:
        nilai = [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
        self.assertEqual(shim.ratakan_teks(nilai), "ab")

    def test_array_thinking_diambil_isi_teksnya(self) -> None:
        nilai = [{"type": "thinking",
                  "thinking": [{"type": "text", "text": "pikir"}]}]
        self.assertEqual(shim.ratakan_teks(nilai), "pikir")

    def test_array_campuran_string_dan_objek(self) -> None:
        nilai = ["a", {"text": "b"}, {"type": "thinking",
                                      "thinking": [{"text": "c"}]}]
        self.assertEqual(shim.ratakan_teks(nilai), "abc")

    def test_angka_dan_bool_tidak_produksi_object_object(self) -> None:
        for nilai in (0, 1, True, False):
            self.assertNotIn("[object Object]", shim.ratakan_teks(nilai))

    def test_dict_tanpa_teks_tidak_produksi_object_object(self) -> None:
        self.assertNotIn("[object Object]", shim.ratakan_teks({"foo": "bar"}))


class TestEksposNormalisasi(unittest.TestCase):
    def test_paket_mengekspos_normalisasi_baris_sse(self) -> None:
        paket = importlib.import_module("modules.codex_cutad")
        self.assertIs(paket.normalisasi_baris_sse, shim.normalisasi_baris_sse)

    def test_paket_mengekspos_ratakan_teks(self) -> None:
        paket = importlib.import_module("modules.codex_cutad")
        self.assertIs(paket.ratakan_teks, shim.ratakan_teks)


if __name__ == "__main__":
    unittest.main()

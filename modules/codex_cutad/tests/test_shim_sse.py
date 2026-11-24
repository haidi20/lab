"""Tests untuk normalisasi SSE Responses di `shim.py`.

Latar (bukti live 2026-11-24, 9router@0.5.119 `chunks/1297.js`):

Event `response.output_text.delta` dikirim dengan `delta` berupa **array
objek** (chunk reasoning), padahal spesifikasi Responses API mewajibkan
`delta` bertipe string. Codex (TypeScript) melakukan `String(delta)` sehingga
jawaban tampil sebagai `[object Object][object Object]...`.

Observasi mentah dari `POST /v1/responses` (combo `cd`) ke 9router:

    event: response.output_text.delta
    data: {"delta":[]}
    data: {"delta":[{"type":"thinking","thinking":[{"type":"text","text":"..."}],"closed":true}]}
    data: {"delta":"pong"}

Shim harus menormalkan itu sebelum diteruskan ke Codex, tanpa mengubah chunk
yang sudah benar (string) dan tanpa merusak event lain.
"""
import importlib
import json
import unittest

shim = importlib.import_module("modules.codex_cutad.shim")


def delta(payload, event="response.output_text.delta"):
    """Bangun satu blok SSE `event:`/`data:` dari dict payload."""
    badan = json.dumps(payload, ensure_ascii=False).encode()
    return b"event: " + event.encode() + b"\ndata: " + badan + b"\n\n"


def ambil(blok):
    """Parse satu blok SSE mentah menjadi (nama_event, dict_payload)."""
    baris = blok.decode().strip().splitlines()
    nama = baris[0].split(":", 1)[1].strip()
    badan = baris[1].split(":", 1)[1].strip()
    return nama, json.loads(badan)


class TestNormalisasiSse(unittest.TestCase):
    def test_delta_string_dibiarkan_apa_adanya(self) -> None:
        blok = delta({"type": "response.output_text.delta", "delta": "pong"})
        hasil, info = shim.normalisasi_baris_sse(blok)
        self.assertEqual(hasil, [blok])
        self.assertEqual(info["dipindah"], 0)

    def test_delta_array_objek_diubah_jadi_string(self) -> None:
        """Bug 9router: delta berupa array -> harus jadi string."""
        blok = delta({"type": "response.output_text.delta",
                      "delta": [{"type": "thinking",
                                 "thinking": [{"type": "text", "text": "Halo"}]}]})
        hasil, info = shim.normalisasi_baris_sse(blok)
        self.assertEqual(len(hasil), 1)
        _, payload = ambil(hasil[0])
        self.assertIsInstance(payload["delta"], str)
        self.assertIn("Halo", payload["delta"])

    def test_delta_array_kosong_tidak_menghasilkan_object_object(self) -> None:
        blok = delta({"type": "response.output_text.delta", "delta": []})
        hasil, info = shim.normalisasi_baris_sse(blok)
        if hasil:
            _, payload = ambil(hasil[0])
            self.assertIsInstance(payload["delta"], str)
            self.assertNotIn("[object Object]", payload["delta"])
        else:
            self.assertGreaterEqual(info["dipindah"], 1)

    def test_chunk_thinking_dialihkan_ke_reasoning_summary(self) -> None:
        """Chunk reasoning tidak boleh mengisi `output_text`."""
        blok = delta({"type": "response.output_text.delta",
                      "delta": [{"type": "thinking",
                                 "thinking": [{"type": "text", "text": "pikir"}],
                                 "closed": True}]})
        hasil, info = shim.normalisasi_baris_sse(blok)
        nama = [ambil(b)[0] for b in hasil]
        self.assertNotIn("response.output_text.delta", nama)
        self.assertIn("response.reasoning_summary_text.delta", nama)
        _, payload = ambil(
            [b for b in hasil
             if ambil(b)[0] == "response.reasoning_summary_text.delta"][0])
        self.assertEqual(payload["delta"], "pikir")


class TestNormalisasiDone(unittest.TestCase):
    def test_output_text_done_bertipe_array_dinormalkan(self) -> None:
        blok = delta({"type": "response.output_text.done",
                      "text": [{"type": "thinking",
                                "thinking": [{"type": "text", "text": "x"}]}]})
        hasil, _ = shim.normalisasi_baris_sse(blok)
        _, payload = ambil(hasil[0])
        self.assertIsInstance(payload["text"], str)

    def test_content_part_done_text_array_dinormalkan(self) -> None:
        blok = delta({"type": "response.content_part.done",
                      "part": {"type": "output_text",
                               "text": [{"type": "text", "text": "abc"}]}})
        hasil, _ = shim.normalisasi_baris_sse(blok)
        _, payload = ambil(hasil[0])
        self.assertIsInstance(payload["part"]["text"], str)

    def test_output_item_done_content_array_dinormalkan(self) -> None:
        blok = delta({"type": "response.output_item.done",
                      "item": {"type": "message", "role": "assistant",
                               "content": [{"type": "output_text",
                                            "text": [{"text": "ok"}]}]}})
        hasil, _ = shim.normalisasi_baris_sse(blok)
        _, payload = ambil(hasil[0])
        self.assertIsInstance(payload["item"]["content"][0]["text"], str)

    def test_event_lain_diteruskan_utuh(self) -> None:
        asli = delta({"type": "response.created", "response": {"id": "r1"}},
                     event="response.created")
        hasil, info = shim.normalisasi_baris_sse(asli)
        self.assertEqual(hasil, [asli])
        self.assertEqual(info["dipindah"], 0)

    def test_komentar_sse_dan_data_bukan_json_tidak_error(self) -> None:
        for mentah in (b": ping\n\n", b"event: x\ndata: bukan-json\n\n"):
            hasil, _ = shim.normalisasi_baris_sse(mentah)
            self.assertEqual(hasil, [mentah])


if __name__ == "__main__":
    unittest.main()

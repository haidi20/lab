# Kontrak payload Codex -> gateway CutadAI (2026-11-24)

## Tujuan

Mencegah error berulang "Invalid request parameters" / 422 `loc: body.<field>`
akibat mengirim parameter yang tidak dikenal provider. Setiap field yang
ditolak gateway harus dibuang atau dipetakan oleh
`modules/codex_cutad/shim.py`; daftarnya dijaga tes.

## Metode

`python -m modules.codex_cutad.diagnosa_3051` -- model `deepseek-v4-pro`,
`stream: true`, prompt "Reply exactly: OK", token dari provider `cd` di
9Router lokal (tidak dicetak).

## Hasil

| Varian | HTTP | Catatan |
| --- | --- | --- |
| `dasar` | 200 | baseline |
| `client_metadata` | 200 | diterima |
| `web_search_tool` | 400 | kode 3051 -> shim membuang tool ini |
| `tool_choice_auto` | 200 | diterima |
| `reasoning_effort_none` | 200 | diterima |
| `reasoning_effort_medium` | 400 | kode 3051 -> shim memetakan ke `high` |
| `reasoning_effort_high` | 200 | diterima |
| `reasoning_summary_only` | 200 | diterima di run ini; tetap dibuang karena 400/3051 di model lain |
| `include_encrypted` | 200 | diterima |
| `store_false` | 200 | diverifikasi ulang setelah jeda |
| `store_true` | 200 | diverifikasi ulang setelah jeda |
| `parallel_tool_calls` | 429 | belum terverifikasi (rate limit) |
| `prompt_cache_key` | 429 | belum terverifikasi (rate limit) |
| `function_tool` | 429 | belum terverifikasi (rate limit) |

Run pertama menembak 14 request beruntun dan kena 429 setelah request ke-9.
Skrip sekarang punya `--hanya` dan `--jeda` (default 6 detik, jitter 0.8x-1.2x)
supaya tidak mengulangi kesalahan itu.

## Implikasi

- `store` **diterima** di `deepseek-v4-pro`, tetapi pengguna lain tetap kena
  422 `loc: body.store` pada provider/model lain di gateway yang sama. Karena
  `previous_response_id` juga dibuang, `store` tidak punya fungsi apa pun di
  jalur ini -> aman dibuang tanpa syarat.
- `reasoning_effort: "medium"` **pasti ditolak** (400/3051), sesuai laporan
  pengguna "supported: ['none','low','high','xhigh','max']". Shim memetakan
  `medium -> high`; stopgap sisi klien: `model_reasoning_effort = "high"` di
  `~/.codex/config.toml`.
- 9Router lokal meneruskan body apa adanya (`app/src/mitm/server.js`: 0
  kemunculan `store`/`reasoning_effort`/`stream_options`), jadi perbaikan hanya
  bisa di shim atau di gateway.

## Ulangi verifikasi

```bash
python -m modules.codex_cutad.diagnosa_3051 --hanya store_false,store_true,reasoning_effort_medium --jeda 10
```

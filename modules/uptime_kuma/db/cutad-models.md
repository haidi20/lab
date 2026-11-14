# Daftar Model Cutad AI — status & kemampuan

> Snapshot hasil probe langsung ke `https://ai.cutad.web.id/v1` pada **14 November 2026 (~11:00–11:15)**.
> Status kuota/circuit-breaker **bisa berubah sewaktu-waktu**. Cara cek ulang ada di bagian akhir.

---

## 1. Ringkasan kasus: "You've hit your usage limit. Try again later."

Intuisi awal benar: **harusnya tidak ada limit Codex**, karena provider yang dipakai bukan OpenAI.

Ternyata pesan itu **bukan kuota akun ChatGPT/Codex**, melainkan **terjemahan Codex CLI** untuk respons `429` dari upstream `cutad`:

```json
{"error":{"message":"Upstream quota exceeded.",
          "type":"insufficient_quota",
          "code":"insufficient_credits",
          "top_up_url":"https://www.coralbricks.ai/organization/billing"}}
```

Binary `codex.exe` memang mengandung string `usage_limit_reached` / `usage_limit_exceeded`, yang ditampilkan sebagai teks generik di atas. Jadi pesannya menyesatkan: **limitnya ada di upstream `cutad` → CoralBricks**, bukan di langganan Codex.

Bukti pemeriksaan:

| Yang dicek | Hasil |
|---|---|
| `codex doctor` | `config.toml parse ok`, `default model provider cutad`, `wire API responses` |
| Auth | `model provider requires OpenAI auth: false` — `auth.json` (`auth_mode = chatgpt`) **tidak dipakai** |
| Env | `provider auth env var CODEX_CUTAD_API_KEY (present)` |
| `/v1/models` | `200`, 11 model terdaftar |
| `deepseek-v4-pro` langsung | `503 circuit_open` / `429 insufficient_credits` |
| `glm-5.3-flash` langsung | `200 OK` di `/v1/responses` |
| `codex exec` dengan `glm-5.3-flash` | `pong`, exit 0, **tanpa pesan limit** |

Kesimpulan: **konfigurasi tidak salah**. Yang bermasalah adalah kuota upstream untuk model tertentu.

---

## 2. Konfigurasi aktif

File: `C:\Users\nhaid\.codex\config.toml` (model tetap `deepseek-v4-pro` sesuai permintaan)

---

## 3. Daftar 11 model + metadata (dari `GET /v1/models`)

| # | Model ID | Context | Max output | Vision | Streaming | Reasoning |
|---:|---|---:|---:|:---:|:---:|:---:|
| 1 | `free-sub/deepseek-v4.1-flash-uncensored-fp8` | 1.000.000 | 10.000 | ✅ | ✅ | ✅ |
| 2 | `dots-studio/dots-3-note-preview` | 512.000 | 4.096 | — | — | — |
| 3 | `glm-5.3-flash` | 1.000.000 | 25.000 | ✅ | ✅ | ✅ |
| 4 | `deepseek-v4.1-flash` | 1.000.000 | 30.000 | ✅ | ✅ | ✅ |
| 5 | `free-sub/kimi-k3-abliterated-v1` | 1.000.000 | 20.000 | ✅ | ✅ | ✅ |
| 6 | `free-sub/glm-5.3-flash-uncensored-fp8` | 1.000.000 | 25.000 | ✅ | ✅ | ✅ |
| 7 | `tencent/hy4-preview` | 1.000.000 | 20.000 | — | — | — |
| 8 | `deepseek-v4-pro` | 1.000.000 | 15.000 | ✅ | ✅ | ✅ |
| 9 | `solar-pro4` | 1.000.000 | 20.000 | ✅ | ✅ | ✅ |
| 10 | `meituan/longcat-2.5` | 1.000.000 | 15.000 | — | — | — |
| 11 | `deepseek-v4.1-flash-uncensored` | 1.000.000 | 20.000 | — | — | — |

Kolom kosong = field `capabilities` tidak diisi oleh provider, bukan berarti pasti tidak mampu.

---

## 4. Hasil probe: bisa / tidak bisa

Diuji dengan request `ping` ke dua endpoint. **`Responses` = yang dipakai Codex.**

| Model ID | `/v1/responses` (Codex) | `/v1/chat/completions` | Keterangan |
|---|---|---|---|
| `dots-studio/dots-3-note-preview` | ✅ `200` | ✅ `200` | Bisa di Codex |
| `glm-5.3-flash` | ✅ `200` | ✅ `200` | Bisa di Codex; pernah dipakai sementara |
| `solar-pro4` | ✅ `200` | ✅ `200` | Bisa di Codex |
| `meituan/longcat-2.5` | ✅ `200` | ✅ `200` | Bisa di Codex |
| `deepseek-v4-pro` | ❌ `503 circuit_open` | ❌ `429 insufficient_credits` | **Model aktif saat ini**, kena kuota upstream |
| `deepseek-v4.1-flash` | ❌ `503 circuit_open` | ❌ `429 insufficient_credits` | Sama, kena kuota upstream |
| `tencent/hy4-preview` | ❌ `429 rate_limit` | ❌ `429 rate_limit` | Rate limit (bukan kehabisan kredit) |
| `deepseek-v4.1-flash-uncensored` | ❌ `402 paid_accounts_only` | ❌ `402 paid_accounts_only` | Butuh akun berbayar |
| `free-sub/deepseek-v4.1-flash-uncensored-fp8` | ❌ `404` | ✅ `200` | Hanya chat-completions |
| `free-sub/glm-5.3-flash-uncensored-fp8` | ❌ `404` | ✅ `200` | Hanya chat-completions |
| `free-sub/kimi-k3-abliterated-v1` | ❌ `404` | ⚠️ timeout | Tidak stabil / lambat |

### Dikelompokkan

**✅ Bisa langsung dipakai di Codex** (`wire_api = responses`):
`glm-5.3-flash`, `solar-pro4`, `meituan/longcat-2.5`, `dots-studio/dots-3-note-preview`

**❌ Tidak bisa di Codex karena kuota/akses upstream:**
`deepseek-v4-pro`, `deepseek-v4.1-flash`, `tencent/hy4-preview`, `deepseek-v4.1-flash-uncensored`

> Tidak ada perubahan config di sisi Codex yang bisa mengakali ini. Harus top-up/tunggu reset di upstream.

**⚠️ Bisa, tapi bukan lewat Codex saat ini:**
Semua model `free-sub/*` mengembalikan `404` di `/v1/responses` — endpoint Responses tidak tersedia untuk mereka. Model ini hanya jalan di `/v1/chat/completions`. Kalau ingin dipakai di Codex, `wire_api` harus diganti ke `"chat"` (dan konsekuensinya perlu dicek terhadap model lain).


```toml
model = "deepseek-v4-pro"
model_provider = "cutad"

model_context_window = 1000000
model_max_output_tokens = 15000

[model_providers.cutad]
name = "Cutad AI"
base_url = "https://ai.cutad.web.id/v1"
env_key = "CODEX_CUTAD_API_KEY"
wire_api = "responses"
```

Catatan:

- `wire_api = "responses"` → Codex memanggil **`/v1/responses`**, bukan `/v1/chat/completions`. Ini penting untuk membaca tabel status di bawah.
- Key tidak lagi ditulis literal di file (dulu `experimental_bearer_token = "cag_..."`), sekarang lewat env var `CODEX_CUTAD_API_KEY`.
- Env var `CUTAD_API_KEY` (nama tanpa `CODEX_`) ternyata **sudah revoked** → `401 invalid_api_key`. Kalau ada tools lain yang memakainya, perlu diganti.
- `auth.json` **sengaja tidak dihapus/di-logout**, karena `codex doctor` menyatakan auth OpenAI tidak diperlukan untuk provider ini.

---

## 5. Arti kode error

| HTTP / `code` | Pesan | Arti | Tindakan |
|---|---|---|---|
| `429 insufficient_credits` | `Upstream quota exceeded.` | Kredit upstream habis | Top-up di `https://www.coralbricks.ai/organization/billing` |
| `503 circuit_open` | `Upstream temporarily unavailable. Please retry in a few seconds.` | Circuit breaker aktif setelah gagal beruntun | Tunggu sebentar; sering muncul bergantian dengan `429` di atas |
| `429 rate_limit` | — | Rate limit per key/per model | Kurangi frekuensi request, tunggu jendela reset |
| `402 paid_accounts_only` | — | Model khusus akun berbayar | Upgrade akun / pakai model lain |
| `404 page not found` | — | Endpoint `/responses` tidak didukung model tsb | Pakai `/chat/completions` atau ganti `wire_api` |
| `401 invalid_api_key` | `Invalid or revoked API key` | Key tidak valid | Pakai `CODEX_CUTAD_API_KEY`, bukan `CUTAD_API_KEY` |
| `000` / `curl (28)` | timeout tanpa body | Masalah koneksi, **bukan penolakan** | Ulangi dengan `--max-time` lebih besar |

Yang memicu teks *"You've hit your usage limit. Try again later."* adalah **`429 insufficient_credits`** (dan varian `503`-nya), bukan `rate_limit`.

---

## 6. Cara cek ulang status

Satu model:

```powershell
$b = '{"model":"deepseek-v4-pro","input":"ping","stream":false,"max_output_tokens":16}'
curl.exe -sS -w "`nHTTP %{http_code}`n" -X POST https://ai.cutad.web.id/v1/responses `
  -H "Authorization: Bearer $env:CODEX_CUTAD_API_KEY" `
  -H "Content-Type: application/json" --data-binary $b
```

`200` = sudah pulih · `429` / `503` = masih kena kuota.

Daftar model terbaru:

```powershell
curl.exe -sS https://ai.cutad.web.id/v1/models -H "Authorization: Bearer $env:CODEX_CUTAD_API_KEY"
```

Verifikasi konfigurasi Codex:

```powershell
codex doctor
codex exec --skip-git-repo-check 'Balas hanya: pong'
```

Ganti model sementara tanpa mengedit file:

```powershell
codex -c model="glm-5.3-flash"
codex exec -m glm-5.3-flash 'Balas hanya: pong'
```

---

## 7. Checklist kalau pesan limit muncul lagi

1. Cek dengan `curl` di atas — kalau `429/503`, **ini upstream, bukan Codex**.
2. Cek/top-up kredit di `https://www.coralbricks.ai/organization/billing`.
3. **Restart VS Code / sesi Codex lama** (status lama sering nempel).
4. Pastikan `CODEX_CUTAD_API_KEY` masih valid; jangan pakai `CUTAD_API_KEY` (revoked).
5. `codex doctor` → harus tetap `provider auth env var CODEX_CUTAD_API_KEY (present)` dan `requires OpenAI auth false`.
6. Opsional: `codex update` (saat probe: v0.167.1, tersedia v0.169.0).

Backup config sebelum perubahan: `C:\Users\nhaid\.codex\config.toml.bak.20261114-110554-before-fix`.


# 9Router — Permasalahan & Solusi

Dokumentasi ini merangkum permasalahan yang ditemukan saat membandingkan dua
URL chat completion, proses diagnosis, dan solusi finalnya.

## Ringkasan Masalah

Dua URL yang dibandingkan lewat `ping.py`:

| # | URL | Authorization | Model | Hasil awal |
|---|-----|---------------|-------|------------|
| 1 | `https://ai.cutad.web.id/v1/chat/completions` | ✅ `Bearer cag_...` | `z-ai/glm-5.2` | ✅ 200 OK |
| 2 | `http://127.0.0.1:20128/v1/chat/completions` (9router lokal) | ❌ tanpa auth | `cd/z-ai/glm-5.2` | ❌ gagal |

Gejala yang terlihat dari sisi client:

1. Request ke 9router lokal selalu gagal:
   - Awalnya: `404` → `{"error":{"message":"No active credentials for provider: z-ai","code":"model_not_found"}}`
   - Setelah nama model diperbaiki: `503` → `[openai-compatible-responses-.../z-ai/glm-5.2] [404]: "Invalid request parameters." code=unknown_endpoint (reset after 2m)`
2. Di **Codex CLI**, error yang sama tampil jelek sebagai `[object Object]` karena
   Codex menampilkan object error apa adanya.

## Proses Diagnosis

### 1. Nama model salah (penyebab pertama)

`GET http://127.0.0.1:20128/v1/models` menunjukkan 9router **tidak punya** model
`z-ai/glm-5.2`. Nama yang terdaftar adalah `cd/z-ai/glm-5.2` (dengan prefix
provider `cd`). Payload dengan nama lama membuat 9router mencari provider
`z-ai` yang tidak ada → `No active credentials for provider: z-ai`.

**Perbaikan:** target kedua `ping.py` memakai model `cd/z-ai/glm-5.2`.

### 2. Error berubah → masalah sebenarnya terlihat

Dengan model yang benar, error berubah menjadi:

```
[openai-compatible-responses-245c3f33-1d93-47e6-aca8-b37e10580cfc/z-ai/glm-5.2]
[404]: {"error":{"message":"Invalid request parameters.","type":"invalid_request_error","code":"unknown_endpoint"}}
(reset after 2m)
```

Kata kuncinya: `openai-compatible-responses` + `unknown_endpoint` + circuit
breaker `reset after 2m`.

### 3. Melacak konfigurasi 9router

- Proses di port 20128 adalah Node.js:
  `C:\Users\nhaid\AppData\Local\nvm\v24.22.1\node_modules\9router\app\custom-server.js`
- Direktori data: `%APPDATA%\9router` (DB SQLite di `db\data.sqlite`)
- Tabel `providerNodes` berisi node custom provider:

```
id: openai-compatible-responses-245c3f33-...
name: cutad
data: {"prefix":"cd","apiType":"responses","baseUrl":"https://ai.cutad.web.id/v1"}
```

### 4. Akar masalah

Node provider **cutad** (prefix `cd`) terdaftar dengan **`apiType: "responses"`,
padahal upstream `https://ai.cutad.web.id/v1` hanya mendukung chat completions**
(terbukti: target 1 lewat `/v1/chat/completions` selalu 200 OK).

Akibatnya 9router memanggil `https://ai.cutad.web.id/v1/responses` → upstream
balas 404 `unknown_endpoint` → 9router meneruskan error sebagai 503 dan
mengunci jalur model itu ~2 menit (circuit breaker).

Bukti pendukung: model lain di 9router (mis. `ag/gemini-3.8-flash-low`) sukses
200 via `/v1/chat/completions` — servernya sehat, masalahnya spesifik di
`apiType` node cutad.

## Solusi

### 1. Ubah `apiType` node cutad: `responses` → `chat`

Dilakukan lewat **API admin resmi 9router** (bukan edit SQLite langsung,
karena server sedang berjalan):

```
PUT /api/provider-nodes/openai-compatible-responses-245c3f33-1d93-47e6-aca8-b37e10580cfc
{"name":"cutad","prefix":"cd","baseUrl":"https://ai.cutad.web.id/v1","apiType":"chat"}
```

Autentikasi CLI dihitung otomatis oleh client resmi 9router
(`src/cli/api/client.js`, header `x-9r-cli-token` dari `machine-id` +
`auth/cli-secret`).

**Backup DB sebelum diubah:**
`%APPDATA%\9router\db\backups\data-before-uitype-fix.sqlite`

### 2. Sesuaikan Codex CLI

`~/.codex/config.toml` — arahkan Codex ke 9router dan samakan wire API dengan
yang didukung upstream:

```toml
model = "cd"                # prefix provider; 9router resolve ke z-ai/glm-5.2
model_provider = "9router"

[model_providers.9router]
name = "9Router"
base_url = "http://127.0.0.1:20128/v1"
wire_api = "chat"           # sebelumnya "responses" → penyebab [object Object]

[model_providers.9router.http_headers]
Authorization = "Bearer sk_9router"
```

Kedua nama model diterima 9router (diverifikasi 200 OK): `cd` maupun
`cd/z-ai/glm-5.2`.

### 3. Tangani quirk response 9router

Setelah diperbaiki, 9router mengembalikan 200 + JSON `chat.completion` yang
valid, tetapi dengan header `content-type: text/event-stream` dan artefak
`data: [DONE]` menempel di ekor body. `kirim_chat()` di `ping.py` kini
toleran: jika `response.json()` gagal, ambil objek JSON pertama dari body
(`teks[:teks.rindex("}") + 1]`).

## Hasil Akhir

```
✅ BERHASIL | https://ai.cutad.web.id/v1/chat/completions | status=200 | ~2-3s
✅ BERHASIL | http://127.0.0.1:20128/v1/chat/completions  | status=200 | ~3s

--- Kesimpulan ---
URL BERHASIL: (kedua URL)
URL GAGAL   : tidak ada
```

Error `[object Object]` di Codex juga hilang karena upstream tidak lagi
mem-balas 404.

## Pelajaran Penting

1. **`No active credentials for provider: X`** di 9router biasanya berarti
   *nama model salah* (prefix tidak cocok), bukan benar-benar kurang kredensial.
2. **`openai-compatible-responses`** pada pesan error = `apiType` node provider.
   Jika upstream hanya mendukung chat completions, ganti `apiType` ke `chat`.
3. **`(reset after Xm)`** = circuit breaker 9router; retry cepat tidak akan
   membantu sampai lock kedaluwarsa.
4. Gunakan API admin (`PUT /api/provider-nodes/:id`) untuk mengubah konfigurasi
   9router yang sedang berjalan — jangan edit SQLite langsung.
5. Selalu **backup** `data.sqlite` sebelum mengubah konfigurasi 9router.

## File & Perintah

```powershell
# Jalankan perbandingan dua URL
python modules\9router\ping.py            # sekali
python modules\9router\ping.py --loop     # ulang tiap 30 detik

# Test
python -m unittest modules.9router.tests.test_ping
python -m unittest discover -s modules -p "test_*.py"
```

| File | Fungsi |
|------|--------|
| `ping.py` | Perbandingan dua URL chat completion (`TARGETS`, `kirim_chat`, `bandingkan`, `format_ringkasan`) |
| `__init__.py` | Ekspos modul via `importlib` (nama paket diawali digit) |
| `tests/test_ping.py` | 16 unit test (network di-mock) |

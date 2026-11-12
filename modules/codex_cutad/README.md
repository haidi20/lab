# Codex cutad — upstream_error glm5.2: Diagnosis & Fix

**Tanggal:** 6 November 2026 · **Mesin:** macOS · **Config:** `~/.codex/config.toml`

## Gejala

Codex (provider `cutad`, model `z-ai/glm-5.2`) gagal dengan error
`upstream_error` / `unsupported_parameter` sejak proxy menambah endpoint
Responses API. Monitor Uptime Kuma lama juga mencatat "upstream_error" pada
jalur `/v1/responses`.

## Akar Masalah (diverifikasi live via curl)

| Percobaan | Endpoint | Hasil |
|---|---|---|
| Request minimal (tanpa `stream`) | `/v1/responses` | ✅ 200 completed |
| + `reasoning.effort/summary`, `store:false`, `include` | `/v1/responses` | ✅ 200 completed |
| + **`"stream": true`** | `/v1/responses` | ❌ **400 `unsupported_parameter`** (semua model) |
| Payload penuh ala Codex (stream + tools + reasoning_effort) | `/v1/chat/completions` | ✅ **200 OK** sampai `data: [DONE]` |

Codex CLI/extension **selalu streaming** setiap request. Dengan
`wire_api = "responses"`, setiap turn Codex mengirim `stream: true` ke
`/v1/responses`, proxy cutad menolaknya → tampil sebagai "upstream error".
Kesimpulan: bukan masalah API key, bukan model — tapi **endpoint Responses
proxy belum mendukung streaming**.

## Fix (sudah diterapkan)

`~/.codex/config.toml`:

```diff
  [model_providers.cutad]
  name = "cutad"
  base_url = "https://ai.cutad.web.id/v1"
  env_key = "CUTAD_API_KEY"
- wire_api = "responses"
+ wire_api = "chat"
```

Backup otomatis: `~/.codex/config.toml.bak-20261106-210417`.
Setelah itu **restart Codex CLI/extension** agar config baru terbaca.

Modul pemeriksa/perbaiki: `modules/codex_cutad/fix_wire_api.py`
(TDD: `modules/codex_cutad/tests/test_fix_wire_api.py`).

> 📄 **Dokumentasi lengkap** (permasalahan → analisa → temuan → solusi,
> termasuk arsitektur final Codex→9Router→cutad setelah reinstall Codex):
> [`documents/2026-11-06-upstream-error-glm52.md`](documents/2026-11-06-upstream-error-glm52.md)

```bash
python3 -m modules.codex_cutad.fix_wire_api --cek   # hanya cek
python3 -m modules.codex_cutad.fix_wire_api          # perbaiki + backup
```

## Catatan lanjutan

- **Update 7 Nov 2026 (glm-5.2 tidak bisa di-ping):** dicek live ulang — ICMP ke
  `ai.cutad.web.id` normal (42 ms, 0% loss), tapi **`z-ai/glm-5.2` kini
  `HTTP 403 upstream_error` di SEMUA jalur** (chat/completions & responses,
  stream & non-stream, diretry). Beda dari kasus 6 Nov (400
  `unsupported_parameter` karena `stream:true`) — ini channel upstream model
  glm-5.2 di proxy cutad yang mati (model masih terdaftar di `/v1/models`
  tapi semua completion gagal). Buktinya proxy sehat: `deepseek-v4-pro` 200
  (jawab PONG) dan `glm-5.3-flash` 200 — **nama model `z-ai/glm-5.3-flash`
  sudah di-rename jadi `glm-5.3-flash`** (tanpa prefix), monitor lama yang
  masih pakai nama lama bakal 404. Jalur Codex→9Router juga benar: request
  `cd/z-ai/glm-5.2` via 9Router diteruskan dan 403-nya di-relay (503 + circuit
  breaker reset 2m). Tidak ada yang perlu (dan bisa) diperbaiki client-side;
  pilih model lain dulu (`cd/glm-5.3-flash` / `cd/deepseek-v4-pro`) atau
  tunggu operator cutad memperbaiki upstream glm-5.2.

- **Update 6 Nov 2026 (reinstall Codex):** Codex modern (0.149+ npm, termasuk
  bundel ChatGPT.app 0.167-alpha) **menolak `wire_api = "chat"`** — hanya
  menerima `responses`. Karena upstream cutad menolak `stream:true` di
  `/v1/responses`, solusi finalnya **9Router lokal sebagai jembatan**:
  Codex (`wire_api="responses"`) → 9Router → chat completions cutad.

  Arsitektur final (Mac ini):
  1. `npm install -g 9router@0.5.112` + `@openai/codex` (0.167.0).
  2. Node provider cutad di 9Router: prefix `cd`, apiType `chat`,
     baseUrl `https://ai.cutad.web.id/v1` + koneksi API key
     (`modules/9router/setup_cutad_node.js`).
  3. Gateway key 9Router buat client (nama `sk_9router`).
  4. LaunchAgent `~/Library/LaunchAgents/com.haidi.9router.plist`
     (node + cli.js, KeepAlive, RunAtLoad) → 9Router selalu jalan di :20128.
  5. `~/.codex/config.toml`:
     ```toml
     model_provider = "9router"
     model = "cd/z-ai/glm-5.2"          # NAMA MODEL WAJIB PAKAI PREFIX cd/
     [model_providers.9router]
     base_url = "http://127.0.0.1:20128/v1"
     wire_api = "responses"
     [model_providers.9router.http_headers]
     Authorization = "Bearer sk-..."    # gateway key dari dashboard 9router
     ```

  Verifikasi: `codex exec 'balas persis: hallo'` → jawab "hallo" (200),
  streaming `/v1/responses` via 9Router → `response.completed`.

- Bila someday proxy cutad mendukung streaming di `/v1/responses`,
  Codex bisa langsung `base_url = "https://ai.cutad.web.id/v1"`
  `wire_api = "responses"` tanpa 9Router.
- Alternatif lama via 9router di Windows: `cd/z-ai/glm-5.2`,
  `wire_api = "chat"`, `http://127.0.0.1:20128/v1` — lihat
  `modules/9router/README.md` (kini usang: versi Codex baru menolak chat).
- Pemantauan: 3 monitor keyword "hallo" (satu per model) via
  `/v1/chat/completions` sudah UP di Uptime Kuma
  (`modules/uptime_kuma/setup_ai_model_monitors.py`).

- **Update 12 Nov 2026 (default Codex → Tencent Hy4 preview):** model default
  `~/.codex/config.toml` di-switch dari `z-ai/glm-5.2` + `cutad-direct` ke
  `tencent/hy4-preview` + `cutad`. Bukan sekadar ganti nama model: Hy4 preview
  ditolak gateway CutadAI bila payload memuat `role:"developer"` (HTTP 400 /
  kode 11128), padahal Codex 0.167.1 (responses-only) selalu mengirimnya, jadi
  **wajib** lewat shim `~/.codex/hy4_proxy.py` di `http://127.0.0.1:8787/v1`
  yang menulis ulang `developer → system` dan membuang `previous_response_id`.
  Tabel `[model_providers.cutad-direct]` sengaja dipertahankan sebagai
  fallback, dan `glm.config.toml` tersedia via `codex --profile glm` bila shim
  mati / kuota Hy4 habis.

  Modul: `modules/codex_cutad/switch_model.py` (TDD, 14 test di
  `tests/test_switch_model.py`), idempoten + backup otomatis:

  ```bash
  python -m modules.codex_cutad.switch_model --cek   # inspeksi
  python -m modules.codex_cutad.switch_model          # terapkan + backup
  ```

  Verifikasi live: `codex exec 'balas persis ...: hallo'` → `hallo`, log shim
  `POST /v1/responses model=tencent/hy4-preview developer->system=2 -> 200`.
  Restart panel Codex/Cursor agar config baru terbaca. Rollback: salin isi
  `config.toml.bak-<stamp>` (atau jalankan `--profile glm`).

- **Update 12 Nov 2026 (default Codex → `deepseek-v4-pro`):** default
  `~/.codex/config.toml` sekarang `model = "deepseek-v4-pro"` +
  `model_provider = "cutad"` (tetap lewat shim). Hy4 preview tetap tersedia:
  `python -m modules.codex_cutad.switch_model tencent/hy4-preview`.

  Bukti probe `/v1/responses` (2026-11-12, `probe_model.py`):

  | payload | hasil |
  | --- | --- |
  | minimal (user saja) | 200 `PONG` |
  | `role:"developer"` | 200 `PONG` |
  | developer + reasoning effort | 200 `PONG` |
  | payload Codex penuh (103 KB, 18 tools, `developer`, `prompt_cache_key`) | 200 `hallo` |
  | lewat shim + `previous_response_id` (dibuang shim) | 200 `HALO` |
  | `codex exec 'jawab persis: hallo'` (CLI 0.167.1) | `hallo`, log shim `model=deepseek-v4-pro ... -> 200` |

  **Kenapa masih wajib shim walau `deepseek-v4-pro` menerima `developer`:**
  Codex mengirim `previous_response_id` pada turn lanjutan, dan gateway
  membalas 400 kode `11128` ("Upstream error. Contact support if this
  persists.") untuk parameter itu. Shim membuangnya, jadi sesi multi-turn
  aman. `gpt-6-luna` tidak bisa dipakai: `/v1/responses` membalas 404 di
  gateway ini.

  **Aturan anti upstream error (dipasang di `switch_model.py`):** nama model
  TIDAK PERNAH ditulis ke config sebelum probe 200. Kalau probe gagal, file
  dibiarkan apa adanya dan perintah keluar dengan kode 3:

  ```bash
  python -m modules.codex_cutad.probe_model deepseek-v4-pro --semua-varian  # cek gateway dulu
  python -m modules.codex_cutad.switch_model deepseek-v4-pro                # switch (probe-gated)
  python -m modules.codex_cutad.switch_model --cek                          # inspeksi
  python -m modules.codex_cutad.switch_model                                # kembali ke default Hy4
  ```

  **Dua bug lama yang ikut diperbaiki di `~/.codex/hy4_proxy.py`**
  (backup `hy4_proxy.py.bak-20261112`):

  1. Root CA Windows di mesin ini kedaluwarsa → Python 3.10 membalas
     `CERTIFICATE_VERIFY_FAILED ... certificate has expired` walau leaf
     gateway valid s/d 2027 (curl: `ssl_verify=0`). Shim (dan `probe_model`)
     sekarang memakai certifi lebih dulu.
  2. Body upstream kadang dilabeli `Content-Encoding: gzip` padahal plain →
     teks rusak di sisi Codex. Shim sekarang mendekode sendiri dan mengirim
     body polos (label gzip tidak diteruskan).


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

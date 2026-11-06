# Codex cutad — Upstream Error glm-5.2: Permasalahan, Analisa, Temuan & Solusi

**Tanggal:** 6 November 2026
**Mesin:** MacBook Air (macOS, Apple Silicon)
**Lingkup:** Codex CLI/extension + proxy AI `https://ai.cutad.web.id` + 9Router lokal
**Status:** ✅ SELESAI — Codex jalan end-to-end via 9Router

---

## 1. Permasalahan

### 1.1 Gejala awal

- Codex (extension VS Code `openai.chatgpt` + CLI) yang dikonfigurasi ke proxy
  **cutad** (`base_url = "https://ai.cutad.web.id/v1"`, model
  `z-ai/glm-5.2`, `wire_api = "responses"`) selalu gagal di setiap turn dengan
  error tampilan yang tidak informatif:

  ```
  ERROR: Reconnecting... 1/5 ... 5/5
  upstream_error / unsupported_parameter
  ```

- Monitor Uptime Kuma lama (dari `check_cutad.py`, pemeriksaan manual
  2026-11-06) juga mencatat kegagalan di jalur yang sama:

  | Monitor | Status |
  |---|---|
  | Ping jaringan ke ai.cutad.web.id | ✅ ok (47 ms, 0% loss) |
  | API key & koneksi HTTPS | ✅ ok (bukan masalah auth) |
  | z-ai/glm-5.2 via chat/completions | ❌ upstream_error |
  | z-ai/glm-5.2 via responses (jalur Codex) | ❌ upstream_error |
  | glm-5.3-flash via chat/completions | ✅ ok (jawab PONG) |
  | glm-5.3-flash / deepseek-v4-pro via Codex | ❌ unsupported_parameter |

- API key valid, HTTPS valid, DNS/IP valid (`103.125.101.169`, server nginx) —
  jadi masalah **bukan** kredensial dan **bukan** jaringan.

### 1.2 Pertanyaan yang harus dijawab

1. Kenapa model yang sama (`z-ai/glm-5.2`) kadang bisa menjawab dan kadang
   `upstream_error`?
2. Kenapa jalur `/v1/responses` khusus gagal, sementara `/v1/chat/completions`
   mulus?
3. Apakah masalah bisa diperbaiki dari sisi client, atau harus dari proxy?

---

---

## 2. Proses Analisa (kronologis, semua terverifikasi live)

> Metode: bisection payload — mulai dari request sekecil mungkin, tambahkan
> parameter satu per satu sampai error muncul. Semua uji pakai `curl` langsung
> dengan `CUTAD_API_KEY` dari `.env`.

### 2.1 Tahap 1 — verifikasi API key & endpoint minimal

```bash
curl -s https://ai.cutad.web.id/v1/responses \
  -H "Authorization: Bearer $CUTAD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"z-ai/glm-5.2","input":"balas persis tanpa mengubah huruf apapun: hallo"}'
```

**Hasil: `HTTP 200`, `status: "completed"`, output message `hallo`.**
Endpoint Responses di proxy ternyata ADA dan bekerja untuk request minimal.
Dugaan awal "endpoint /v1/responses tidak ada" (seperti kasus 9router Windows
3 Nov, lihat `modules/9router/README.md`) **terbantahkan**.

### 2.2 Tahap 2 — parameter Codex-like ditambah satu per satu

| Payload tambahan | Hasil |
|---|---|
| `"reasoning":{"effort":"high"}` | ✅ 200 completed |
| `+ "reasoning":{"summary":"auto"}` | ✅ 200 completed |
| `+ "store":false, "include":["reasoning.encrypted_content"]` | ✅ 200 completed |
| `+ "stream":true` | ❌ **400 `unsupported_parameter`** |
| input array + instructions + tools (ala Codex, tanpa stream) | ❌ 400 `unsupported_parameter` |

### 2.3 Tahap 3 — temuan kunci: `stream: true` ditolak di `/v1/responses`

```bash
curl -s https://ai.cutad.web.id/v1/responses \
  -H "Authorization: Bearer $CUTAD_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"z-ai/glm-5.2","input":"hallo","stream":true}'
# → {"error":{"message":"Upstream error. Contact support if this persists.",
#            "type":"unsupported_parameter","code":"unsupported_parameter"}}
```

- Diuji ke **semua 3 model** (`z-ai/glm-5.2`, `glm-5.3-flash`,
  `deepseek-v4-pro`) di `/v1/responses`: **semuanya 400**.
- Sementara `/v1/chat/completions` dengan payload penuh ala Codex
  (stream + tools + reasoning_effort + stream_options):

  ```
  HTTP 200 → chunk chat.completion.chunk mengalir sampai data: [DONE]
  usage: reasoning_tokens 137, total 507
  ```

**Kesimpulan tahap 3:**
- `/v1/responses` cutad **tidak mendukung `stream:true`** untuk semua model.
  Parameter lain (tools/instructions) kemungkinan juga tidak didukung, tapi
  pemicu utama yang pasti adalah `stream`.
- `/v1/chat/completions` cutad **mendukung semua** kebutuhan Codex: streaming,
  tools, reasoning, usage.
- dan **Codex CLI/extension SELALU streaming** setiap request → dengan
  `wire_api = "responses"` (menunjuk `/v1/responses`), setiap turn Codex
  pasti kena 400 → tampil sebagai "upstream error / reconnect gagal".

### 2.4 Tahap 4 — fix pertama (berhasil sementara): `wire_api = "chat"`

Config Codex diubah (`~/.codex/config.toml`):

```diff
  [model_providers.cutad]
  name = "cutad"
  base_url = "https://ai.cutad.web.id/v1"
  env_key = "CUTAD_API_KEY"
- wire_api = "responses"
+ wire_api = "chat"
```

Backup otomatis: `config.toml.bak-20261106-210417`. Diff diverifikasi — hanya
1 baris berubah. Modul pemeriksa dibuat TDD:
`modules/codex_cutad/fix_wire_api.py` (+ 8 test, semua lulus).

### 2.5 Tahap 5 — install ulang Codex → fix pertama gugur

User meminta Codex di-install ulang. `npm install -g @openai/codex@latest`
→ **codex-cli 0.167.0**. Saat dijalankan:

```
Error loading config.toml: `wire_api = "chat"` is no longer supported.
How to fix: set `wire_api = "responses"` in your provider config.
More info: https://github.com/openai/codex/discussions/7782
in `model_providers.cutad.wire_api`
```

**Probe versi** (dengan `CODEX_HOME` sandbox `/tmp/cxh`, config asli tidak
disentuh):

| Versi codex-cli | `wire_api = "chat"` |
|---|---|
| 0.167.0 (npm latest) | ❌ ditolak |
| 0.167.0-alpha.3.2 (bundel ChatGPT.app) | ❌ ditolak |
| 0.165.0 / 0.163.0 / 0.160.0 / 0.155.1 / 0.150.0 / 0.149.0 (npm) | ❌ ditolak semua |
| 0.120.0 / 0.110.0 (npm) | ⚠️ binary ENOENT — struktur paket platform berubah, tidak bisa jalan |

**Kesimpulan tahap 5:** tidak ada versi Codex yang bisa dipakai dengan
`wire_api = "chat"`. Semua Codex modern responses-only. Dengan upstream cutad
yang menolak streaming Responses, **tidak ada konfigurasi Codex langsung ke
cutad yang bisa jalan**.

### 2.6 Tahap 6 — arah solusi: jembatan lokal (9Router)

Kebutuhan: Codex (wajib Responses + stream) ↔ cutad (hanya chat + stream OK).
Pilihan:

1. Pin versi Codex jadul → terbukti mustahil (binary npm rusak; versi lebih
   lama pun sudah menolak).
2. **Jembatan lokal yang berbicara Responses API (dengan streaming) ke Codex,
   lalu menerjemahkannya ke chat completions cutad** → 9Router (sama dengan
   setup yang sudah terbukti di Windows, versi 0.5.112).

Pilihan 2 diambil.


---

## 3. Temuan (ringkasan akar masalah)

| # | Temuan | Bukti |
|---|---|---|
| 1 | Proxy cutad `/v1/responses` menolak `stream:true` → 400 `unsupported_parameter` untuk semua model (z-ai/glm-5.2, glm-5.3-flash, deepseek-v4-pro) | bisection curl live: minimal+reasoning 200, begitu +stream 400 |
| 2 | `/v1/chat/completions` cutad mendukung penuh kebutuhan Codex: stream + tools + reasoning_effort + stream_options → 200 sampai `data: [DONE]`, usage lengkap (reasoning_tokens 137) | curl live payload penuh ala Codex |
| 3 | Codex CLI/extension selalu streaming setiap request → wire `responses` langsung ke cutad mustahil jalan | temuan #1 + perilaku Codex (Reconnecting 5x lalu mati) |
| 4 | Codex modern (0.149–0.167 npm & 0.167-alpha bundled ChatGPT.app) adalah **Responses-only**; `wire_api="chat"` dihapus permanen (discussions/7782) | error `Error loading config.toml` di 7 versi yang di-probe bersih via CODEX_HOME sandbox |
| 5 | 9Router mampu jadi jembatan: menerima `/v1/responses` + stream dari Codex, keluar sebagai `/v1/chat/completions` + stream ke cutad | uji live: `response.completed`, `text: "hallo"`, usage 307 tokens |
| 6 | Nama model di 9Router **wajib pakai prefix** provider node (`cd/z-ai/glm-5.2`); tanpa prefix → 404 `No active credentials for provider: z-ai` | codex exec sebelum & sesudah pakai prefix |
| 7 | Gateway 9Router (`/v1/*`) butuh API key client sendiri → 401 `Missing API key` tanpa `Authorization: Bearer sk-...` | curl sebelum/sesudah key dibuat |
| 8 | launchd macOS tidak mewarisi PATH Homebrew → menjalankan symlink `9router` (shebang `env node`) gagal exit 127 | `/tmp/9router-launchd.log`; fix: panggil node absolut + cli.js + set PATH di plist |
| 9 | API key cutad, DNS (`103.125.101.169`), dan TLS semuanya sehat sejak awal — masalah murni kompatibilitas parameter/endpoint | curl 200 pada jalur chat sejak tes pertama |

**Satu kalimat akar masalah:**
> Codex modern hanya bisa bicara Responses (selalu streaming), sedangkan satu-satunya jalur streaming yang sehat di proxy cutad adalah chat completions — jadi dibutuhkan penerjemah protokol di lokal (9Router).



---

## 4. Solusi Lengkap (yang diterapkan)

### 4.1 Arsitektur final

```
Codex CLI/Ext (wire_api="responses", selalu stream)
        │  POST /v1/responses + stream (SSE)
        ▼
9Router lokal 127.0.0.1:20128        [LaunchAgent com.haidi.9router, KeepAlive]
        │  translate: Responses API → Chat Completions (streaming stateful)
        ▼
https://ai.cutad.web.id/v1/chat/completions   (stream chunk 200 OK)
        ▼
z-ai/glm-5.2 · glm-5.3-flash · deepseek-v4-pro
```

### 4.2 Komponen yang di-install / dibuat

1. **Codex CLI** — `npm install -g @openai/codex@latest` → versi 0.167.0
   (`/opt/homebrew/bin/codex`). Versi terbundel di ChatGPT.app
   (0.167.0-alpha.3.2) tidak diubah.
2. **9Router** — `npm install -g 9router@0.5.112` (versi yang sama dengan
   setup Windows). Catatan: download tray native Apple Silicon timeout —
   tidak masalah, server utama Node.js jalan normal.
3. **Setup node cutad** — `modules/9router/setup_cutad_node.js` (idempoten,
   memakai client admin API resmi 9router `src/cli/api/client.js` yang
   menghitung header `x-9r-cli-token` dari machine-id + cli-secret):
   - `createProviderNode({name:"cutad", prefix:"cd", apiType:"chat",
     baseUrl:"https://ai.cutad.web.id/v1", type:"openai-compatible"})`
     → node `openai-compatible-chat-7da90dd6-c97b-4b98-8448-7bfc66c3e01b`
   - `createApiKeyProvider({provider:<node.id>, name:"cutad key",
     apiKey:$CUTAD_API_KEY})` → koneksi `apikey`, `isActive:true`
   - gateway key untuk client: `createApiKey("sk_9router")`
     → `sk-b1aa3a97b486b238-exu88m-5c7db777`
   - Model aktif dengan prefix cd: `cd/z-ai/glm-5.2`, `cd/glm-5.3-flash`,
     `cd/deepseek-v4-pro`, `cd/deepseek-v4.1-flash`,
     `cd/dots-studio/dots-3-note-preview`.
4. **LaunchAgent autostart** —
   `~/Library/LaunchAgents/com.haidi.9router.plist` (`plutil -lint: OK`):

   ```xml
   <key>ProgramArguments</key>
   <array>
     <string>/opt/homebrew/bin/node</string>
     <string>/opt/homebrew/lib/node_modules/9router/cli.js</string>
     <string>--skip-update</string>
     <string>-n</string>
   </array>
   <key>RunAtLoad</key><true/>
   <key>KeepAlive</key><true/>
   <key>EnvironmentVariables</key>
   <dict>
     <key>PATH</key><string>/opt/homebrew/bin:/usr/bin:/bin</string>
   </dict>
   ```

   **PENTING:** jangan panggil symlink `/opt/homebrew/bin/9router` dari
   launchd (shebang `env node` gagal karena PATH kosong). Panggil binary
   node absolut + cli.js, dan set `PATH` di EnvironmentVariables.
   Penerapan: `launchctl bootout gui/501/com.haidi.9router` (bersihkan
   registrasi lama) → `launchctl bootstrap gui/501 <plist>`.
5. **`~/.codex/config.toml`** final (backup
   `config.toml.bak-pre9router-20261106-213347`):

   ```toml
   model_provider = "9router"
   model = "cd/z-ai/glm-5.2"          # WAJIB prefix cd/, bukan z-ai/glm-5.2
   model_reasoning_effort = "high"

   [model_providers.9router]
   name = "9Router"
   base_url = "http://127.0.0.1:20128/v1"
   wire_api = "responses"

   [model_providers.9router.http_headers]
   Authorization = "Bearer sk-b1aa3a97b486b238-exu88m-5c7db777"
   ```

   Bagian `[model_providers.cutad]` lama (base_url ai.cutad + env_key +
   wire_api chat) dilepas — tugasnya diambil node cutad di 9Router.

### 4.3 Verifikasi akhir (semua lulus)

| Uji | Hasil |
|---|---|
| `POST /v1/responses` + `stream:true` via 9Router (gateway key, model `cd/z-ai/glm-5.2`) | ✅ HTTP 200, event `response.created → in_progress → completed`, message `text:"hallo"`, usage 307 tokens |
| `codex exec --skip-git-repo-check 'balas persis tanpa mengubah huruf apapun: hallo'` | ✅ jawab `hallo` (142 tokens), tanpa reconnect error |
| `codex exec` sebelum pakai prefix | ❌ 404 `No active credentials for provider: z-ai` → diperbaiki dengan `cd/` |
| Gateway key auth | ✅ 200 setelah `sk-...` (sebelum: 401 Missing API key) |
| LaunchAgent setelah bootout+bootstrap | ✅ PID hidup (status 0), `GET /v1/models` → 200 |
| Test suite lab | ✅ **71 tests OK** (9router + codex_cutad + uptime_kuma) |

### 4.4 Error yang ditemui selama penerapan (dan penyelesaiannya)

| Error | Penyebab | Solusi |
|---|---|---|
| `wire_api = "chat"` is no longer supported | Codex modern responses-only | Codex diarahkan ke 9Router; wire tetap `responses` |
| 401 `Missing API key` di gateway 9Router | `/v1/*` 9Router memvalidasi key client | buat `sk_9router` via admin API, pakai di header Authorization |
| 404 `No active credentials for provider: z-ai` | nama model tanpa prefix node | pakai `cd/z-ai/glm-5.2` |
| launchd exit 127 `env: node: No such file or directory` | launchd tidak punya PATH Homebrew | ProgramArguments pakai `/opt/homebrew/bin/node` + cli.js + set PATH di plist |
| `launchctl bootstrap: Input/output error` | service lama masih ter-registrasi | `launchctl bootout` dulu, baru `bootstrap` |
| npm @openai/codex 0.120/0.110: ENOENT vendor binary | struktur paket platform berubah di versi lama | bukan jalur solusi; tetap di 0.167.0 |
| `zsh: unknown sort specifier` pada node -e multiline | quoting subshell rusak oleh zsh | tulis script ke file, jangan inline |

### 4.5 File & artefak

| File | Fungsi |
|---|---|
| `~/.codex/config.toml` | config Codex final (provider 9router) |
| `~/.codex/config.toml.bak-20261106-210417` | backup sebelum fix wire_api "chat" |
| `~/.codex/config.toml.bak-pre9router-20261106-213347` | backup sebelum pindah ke 9router |
| `modules/codex_cutad/fix_wire_api.py` (+tests, 8) | deteksi/fix wire_api + CLI `--cek` |
| `modules/codex_cutad/README.md` | ringkasan singkat diagnosis & fix |
| `modules/codex_cutad/documents/2026-11-06-upstream-error-glm52.md` | dokumen ini |
| `modules/9router/setup_cutad_node.js` (+tests, 5) | setup idempoten node cutad + key di 9Router |
| `~/Library/LaunchAgents/com.haidi.9router.plist` | autostart 9Router |
| `/tmp/9router-launchd.log` | log server 9Router (launchd) |

### 4.6 Perawatan & troubleshooting operasional

```bash
# Status 9Router
curl -s -m 5 http://127.0.0.1:20128/v1/models -o /dev/null -w '%{http_code}\n'
launchctl list | grep 9router
tail -f /tmp/9router-launchd.log

# Restart 9Router
launchctl kickstart -k gui/501/com.haidi.9router

# Uji cepat jalur Codex
codex exec --skip-git-repo-check 'balas persis: hallo'

# Uji streaming Responses via 9Router
curl -sN http://127.0.0.1:20128/v1/responses \
  -H "Authorization: Bearer sk-..." -H "Content-Type: application/json" \
  -d '{"model":"cd/z-ai/glm-5.2","input":"hallo","stream":true}'

# Setup ulang node cutad di 9Router (idempoten)
cd ~/projects/lab && set -a && source .env && set +a && \
  node modules/9router/setup_cutad_node.js

# Test suite
cd ~/projects/lab && python3 -m unittest \
  modules.codex_cutad.tests.test_fix_wire_api \
  modules.9router.tests.test_setup_cutad_node \
  modules.uptime_kuma.tests.test_setup_ai_model_monitors
```

- Codex error `No active credentials for provider: X` → nama model kurang
  prefix (`cd/...`), atau koneksi cutad di 9Router non-aktif.
- Codex `stream disconnected` tapi curl lancar → cek 9Router hidup; circuit
  breaker 9Router mengunci jalur ~2 menit setelah error upstream, retry cepat
  tidak membantu.
- Bila suatu saat proxy cutad mendukung streaming `/v1/responses`, Codex cukup
  diarahkan langsung: `base_url = "https://ai.cutad.web.id/v1"`,
  `wire_api = "responses"`, `env_key = "CUTAD_API_KEY"` — tanpa 9Router.
- Versi Codex berikutnya tetap responses-only; jangan berharap
  `wire_api = "chat"` kembali (discussion 7782).

---

## 5. Pelajaran Penting

1. **Bisection payload adalah cara tercepat** menemukan parameter yang ditolak
   upstream: mulai dari request minimal, tambah satu per satu. Di proxy cutad,
   "Upstream error. Contact support" = `unsupported_parameter`.
2. **"Endpoint ada" ≠ "endpoint mendukung request Codex".** `/v1/responses`
   bisa 200 untuk non-stream tapi 400 untuk stream — dan Codex selalu stream.
3. **Codex modern = Responses-only.** Jangan rencanakan `wire_api = "chat"`
   di 0.149+; solusinya menyediakan endpoint yang berbicara Responses di depan
   — di sinilah 9Router.
4. **Nama model di 9Router wajib prefix node** (`cd/...`). Error "kredensial"
   biasanya nama model salah, bukan key hilang.
5. **launchd macOS tidak mewarisi PATH shell** — untuk service Node, invoke
   binary node + script secara absolut dan set PATH di plist.
6. **Selalu backup sebelum mengubah config** dan ubah konfigurasi 9Router via
   API resmi (client.js), bukan edit SQLite langsung — sesuai aturan
   `modules/9router/README.md`.
7. **Uptime Kuma ternyata detektor pertama** masalah ini: monitor keyword pada
   `/v1/responses` gagal jauh sebelum user sadar Codex error. Monitor
   "hallo" per model di chat/completions kini jadi health-check permanen.

---

## 6. Timeline Ringkas (2026-11-06, waktu lokal)

| Jam | Peristiwa |
|---|---|
| ±20:45 | Uptime Kuma: 3 monitor AI model "hallo" selesai dibuat, semua UP |
| 20:55 | Analisa dimulai — `/v1/responses` request minimal ternyata 200 |
| 20:58–21:00 | Bisection payload → dipastikan `stream:true` ditolak di Responses; chat completions mendukung penuh |
| 21:04 | Fix `wire_api="chat"` diterapkan + backup + modul TDD (8 test) |
| 21:07 | User minta reinstall Codex → npm 0.167.0 menolak wire "chat" |
| 21:10–21:20 | Probe 7+ versi Codex: semuanya responses-only; opsi pin versi tua gugur |
| 21:21–21:30 | 9Router 0.5.112 ter-install; node cutad (apiType chat) + koneksi key + gateway key dibuat via admin API |
| 21:33 | Codex dialihkan ke 9Router; error prefix ditemukan & diperbaiki (`cd/z-ai/glm-5.2`) |
| 21:36–21:40 | LaunchAgent diperbaiki (PATH node), bootout+bootstrap sukses |
| 21:42 | Verifikasi final: `codex exec` jawab "hallo"; stream Responses 200 completed; 71 test OK |

   Bagian `[model_providers.cutad]` lama (base_url ai.cutad + env_key +
   wire_api chat) dilepas — tugasnya diambil node cutad di 9Router.

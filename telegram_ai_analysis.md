# Kurasi Analisa Chat Telegram - Informasi Teknologi Penting

> Sumber: 22.044 pesan dari 85 grup Telegram (24 Okt - 3 Nov 2026)
> Dari 530 pesan teknis yang lolos kurasi, dokumen ini merangkum hanya informasi penting.
> Diperbarui: 3 November 2026

## Ringkasan Eksekutif

1. Komunitas sudah beralih ke pola "model per tugas" - bukan langganan satu vendor. Router multi-model (9Router, Griphub, dsb.) dengan satu API key adalah workflow standar.
2. DeepSeek V4.1 Flash = default reasoning/coding; GLM 5.3 Flash = favorit frontend + tool calling; keduanya sering gratis/bansos.
3. Skill paling berharga menurut praktisi: prompt engineering + context engineering - hemat token tanpa turun kualitas.
4. Masalah teknis terbesar di ekosistem router: streaming error, pool kuota habis, dan translasi endpoint antar format API.

## 1. Model AI Terbaru yang Dibahas

| Model | Posisi di Komunitas | Catatan |
|---|---|---|
| DeepSeek V4.1 Flash | Default reasoning & coding | Versi `1017` dipatok s.d. 1 Nov; hosting pindah ke Singapura; sering `out of quota` karena laris |
| GLM 5.3 Flash | Favorit frontend + tool calling | Gratis 20M token/hari via APInex (`free/glm-5.3`); context 1M; OpenAI-compatible |
| Kimi K3.1 Pro | Sekelas Claude Opus 5.5 | "Beda tipis di benchmark" - alternatif kuat |
| Gemini 3.8 Flash | Alternatif cepat | Sering dipakai saat DeepSeek/GLM down |
| GPT 6 (Sol/Luna/Astra) | Respon tercepat | Sering error tooling; GPT-5.6 Luna belum bisa jalani subagent di OpenCode |
| Gemini 4 Carbon | Paling ditunggu | Benchmark bocor sebelum rilis; harga belum diketahui |
| Step 5 | Alternatif coding | Disebut sebagai backup DeepSeek/GLM |
| MiniMax M3.1 / Mimo v2.6 | Model gratis harian | Sering masuk paket bansos router |

## 2. Tooling & Workflow Developer

- **OpenCode vs Hermes** (pertanyaan paling sering): Hermes = agent all-rounder untuk pekerjaan sehari-hari; OpenCode = fokus coding. Pilih sesuai kebutuhan.
- **9Router** = jembatan umum: 1 API key, banyak provider; bisa colok ke OpenCode, Cursor, Claude Code, Hermes.
- **Endpoint translation**: GPT pakai `responses`, Claude pakai `messages`, lainnya `chat/completions`. Router menerjemahkan antar format - inilah sebab streaming via router sedikit lebih lambat.
- **Skill/workflow repo** (superpowers dll.) hanya worth it jika prompt/PRD sangat detail; untuk vibe coding harian justru boncos token.
- **Auto-update model list**: cron job untuk fetch `/models` dan update config OpenCode otomatis - model router sering berganti tanpa pemberitahuan.

## 3. Masalah Teknis Nyata & Solusinya

| Gejala | Penyebab Sebenarnya | Solusi |
|---|---|---|
| Error 524 di context besar | Timeout Cloudflare (>500K token per request) | Pecah context; jaga di bawah 1M token |
| `Duplicate tool response for tool_call_id` | Bug parameter 9router v0.5.55 | Update versi router |
| `out of quota` DeepSeek/GLM | Pool upstream habis | Router rotate pool; pindah model sementara |
| 3x empty completions (Claude) | Proteksi anti-abuse router | Router refuse session; tunggu atau ganti model |
| GPT makin lambat | Upstream OpenAI sedang berat | Bukan masalah lokal; tunggu atau ganti model |
| `HTTP 400 invalid parameters` (GLM) | Format request beda antar varian model | Pakai model "biasa", bukan "mod", jika error |

## 4. Infrastruktur & Hosting

- Setup standar router AI lokal: **VPS murah + domain + Cloudflare**.
- VPS 32GB RAM / 480GB storage sekitar $5/bulan (kode promo `FLY300VULTR` untuk user baru Vultr).
- **DeepSeek SG deprecated** - semua model Deepseek pindah hosting ke Singapura.
- Pelajaran bisnis: untuk project klien (apalagi pemerintah), jangan deploy di server klien sebelum lunas - deploy app di server sendiri, database tetap di kendali sendiri.

## 5. Sumber Belajar Gratis yang Dibagikan

| Sumber | Isi |
|---|---|
| `github.com/asgeirtj/system_prompts_leaks` | Koleksi system prompt bocoran - belajar struktur workflow AI yang baik |
| `prompt-motion.com` | Inspirasi prompt engineering |
| `github.com/cloudflare/security-audit-skill` | Skill audit keamanan untuk coding agent |
| APInex (`free/glm-5.3`) | GLM 5.3 gratis 20M token/hari, 1M context, OpenAI-compatible |
| Vultr `FLY300VULTR` | Kredit VPS murah untuk user baru |

## 6. Istilah Penting yang Sering Muncul

| Istilah | Arti |
|---|---|
| API key | Kunci akses + identitas billing ke layanan AI |
| Base URL | Alamat endpoint API (mis. `https://api.x.com/v1`) |
| Token | Satuan pemakaian model AI (sekitar 0,75 kata) |
| Context window | Batas teks yang bisa diproses sekali jalan (512K, 1M) |
| RPM / TPM | Rate limit: request/token per menit - penyebab error 429 |
| Upstream | Sumber asli model (OpenAI, Anthropic, dsb.) |
| Fallback / pool rotation | Server atau kuota cadangan saat upstream utama habis |
| Masking | Penipuan: dijual "Claude" tapi isinya model murah |
| Multiplier | Pengali tagihan token di router (2x = bayar dobel) |
| Vision delegation | Model tanpa kemampuan gambar "numpang" model lain |
| MCP | Standar koneksi AI ke tools (Trello, browser, DB) |
| Agent / subagent | AI yang eksekusi multi-step sendiri (baca file, edit, test) |
| VPS / RDP | Server virtual Linux / remote desktop Windows |
| Streaming | Respons model dikirim bertahap, bukan sekali jadi |

## 7. Kesimpulan Belajar

1. **Model per tugas + router multi-model** adalah pola kerja standar sekarang - tidak perlu langganan mahal satu vendor.
2. **Prompt & context engineering** adalah skill dengan ROI tertinggi menurut praktisi di chat.
3. Kalau mau membangun gateway AI sendiri, tiga tantangan utama dari pengalaman grup: **stability streaming, rotasi pool kuota, dan translasi endpoint antar format API**.
4. **Selalu cek masking & multiplier** sebelum membeli API key murah - dua keluhan terbanyak user.
5. Model gratis/bansos berumur pendek (1-3 hari) - layak diotomasi (cron + notif Telegram) untuk hemat biaya development.

## Lampiran: Kutipan Asli Terpilih

### Arsitektur Router (Griphub)

- "GPT -> responses, Claude -> messages, Mocyn/Meta/Gemini/Muse -> chat/completions... di router ada translator... proses translatenya ini yg bikin streaming agak lebih lambat" - Yudi, 28/10
- "Claude kalau ada 3x empty completions router langsung ngerefuse session itu" - Yudi, 29/10
- "Pas lagi streamingnya, poolnya kehabisan kuota. Diulangi biar pindah ke pool baru" - Yudi, 29/10
- "klo 524 itu karena cloudflare... gw sih kena begitu klo context udah gede" - NoyX, 28/10

### Tooling & Workflow

- "hermes itu lebih ke agent all rounder, buat sehari hari lebih bagus, kecuali emg fokusnya buat coding pake opencode aja" - saucysoup, 25/10
- "skill skill superpower... dipake kalau prd dan penjelasan prompt kita sedetail detailnya banget. kalau harian mending jangan" - Dhani, 27/10
- "prompt engineering ama context engineering la belajar... biar pas langganan AI frontier bisa hemat token tapi kinerja AInya masih gacor" - Kei, 25/10
- "Kimi K3.1 pro, sekelas Opus 5.5, beda tipis di benchmark" - Kei, 24/10

### Infra & Bisnis

- "biasanya projectan sama pemerintah... pastikan kalo app udah jadi dan mereka belom bayar, jangan pernah deploy di server mereka" - Dhani, 29/10
- "Deploy di server mereka. Tp databasenya [tetap di kita]" - Yudi, 29/10
- "di sebelah ada [multiplier]... make token cuma 2 juta tapi di log sampe 27 juta" - Mick Doon, 28/10

---

*Dokumen ini dikurasi dari database `telegram_data` (tabel `telegram_messages`) dan disaring dari grup jualan. Versi mentah 530 pesan telah diganti ringkasan ini; bisa diregenerate ulang dari DB bila diperlukan.*

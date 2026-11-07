# Daftar Paket AI "Unlimited Token" — Survei Chat Telegram

**Tanggal survei:** 7 November 2026
**Sumber:** `telegram_data` (MySQL lokal), sync 1 bulan terakhir (8 Okt – 7 Nov 2026) — 59.081 pesan dari 85 grup/channel
**Contoh acuan:** Cutad (`ai.cutad.web.id`) — "bayar paket, pakai tanpa hitung token"

---

## Ringkasan Cepat

| # | Penyedia | Paket Bulanan Termurah | Batas yang Diakui | Jumlah Model |
|---|---|---|---|---|
| 1 | Limo Router | **40K (30 hari)** | 512K context · 50 RPM | 9 |
| 2 | Nocta Digital | **Rp45.000/bulan** | tidak dirinci | tidak disebut |
| 3 | Cutad (Ultimate) | cek `/pricing` | slot terbatas, ditutup saat beban tinggi | **9** |
| 4 | NilovrAI (Batas Wajar) | **Rp296.000** | 4.000 request/hari · RPM 32 | 13 (kredit: 36) |
| 5 | NilovrAI (Tanpa Batas) | **Rp499.000** | tanpa batas request · RPM 42 · 10 concurrent | 13 (kredit: 36) |
| 6 | NilovrAI (Reseller) | **Rp598.800** | RPM 120 · 80 concurrent | 13 (kredit: 36) |
| 7 | Griphub Router | *bukan langganan* — Rp300/kredit | 600 RPM · 5 concurrent | ~7+ |
| 8 | Jerouter | Trial 1h / Basic 3h / Plus 7h | reseller: unlimited sesi/IP/RPM | ~17 |
| 9 | **APIGOD** | **Rp100.000 (7 hari)** — tidak ada paket 30 hari | **60 RPM · "UNLIMITED TOKEN"** | tidak dirinci |

**Rentang harga: Rp40.000 → Rp598.800 (selisih 15×).**

**Inti model bisnis:** semua menagih per **waktu**, bukan per token. Tapi semuanya memasang
plafon di **request/hari**, **RPM**, **concurrent**, atau **slot pembelian**.
→ "Unlimited" = unlimited *token*, bukan unlimited *request*.

---

## 1. Cutad — `ai.cutad.web.id` (acuan)

| Aspek | Keterangan |
|---|---|
| Nama paket | **Daily** (1 hari) → **Ultimate** (1 bulan) |
| Harga | lihat `https://ai.cutad.web.id/pricing` (tidak dipublikasi di chat) |
| Billing / renew | `https://ai.cutad.web.id/dashboard/billing` |
| Grup | `This One!`, `CutadAgent Router` (channel), `@ChatAgentx` |
| Model | `deepseek-v4-pro`, `deepseek-v4.1-flash`, `glm-5.3-flash`, `z-ai/glm-5.2`, step-5-preview, solar-pro4, meituan/longcat-2.5, reflection/beam-1.0 |
| Kredit per model | ada, mis. "Plan Deepseek V.4.1 Flash (1017)" + bonus reset NOL (Free 500M) |

**Batas nyata (dari pengumuman resmi):**

> "Plan Unlimited sudah habis ya, Close dulu! Nanti akan di Buka Kembali — Tunggu sampai
> Platform sepi (Untuk Menjaga Liquiditas)" — 4 Nov 2026

→ kuota slot terbatas; ditutup saat beban tinggi.

**Model dikunci per tier:**

> "Cutad saya knp min? Not available in your plan." — 5 Nov 2026
> "cutadpro menghilang dari lane min?" — 5 Nov 2026

---

## 2. NilovrAI — `platform.nilovr.com` / `api.nilovr.com`

Dua jalur unlimited, dibedakan jelas antara "batas wajar" dan "tanpa batas request".

### Paket ritel

| Paket | 1 hari | 3 hari | 7 hari | 14 hari | 30 hari |
|---|---|---|---|---|---|
| **Batas Wajar** — 4.000 req/hari | Rp13.000 | Rp37.000 | Rp84.000 | Rp160.000 | **Rp296.000** |
| **Tanpa Batas Request** | Rp28.000 | Rp80.000 | Rp180.000 | Rp345.000 | **Rp499.000** |

- RPM: 20 (1/3/7 hari) · 32 (14/30 hari)
- Jalur tanpa batas: RPM 32 · 42 (14/30 hari) · 10 concurrent
- Harga normal sebelum diskon: Batas Wajar 30 hari Rp320.000; Tanpa Batas 30 hari Rp599.000

### Paket kredit (sekali beli, tidak hangus)

| Kredit | Harga |
|---|---|
| 25 | Rp10.000 |
| 100 | Rp27.000 |
| 500 | Rp143.000 |
| 1.000 | Rp210.000 |

### Paket reseller (tanpa biaya pendaftaran)

| Item | Detail |
|---|---|
| Unlimited | 5 paket (1/3/7/14/30 hari) |
| Batas | RPM 120 · 80 concurrent (8× ritel) |
| Contoh harga 30 hari | **Rp598.800** |
| Kredit diskon 35% | 1.000 = Rp136.500 · 5.000 = Rp655.000 · 15.000 = Rp1.905.000 |

### Model inti

DeepSeek v4.1 flash & v4.1 flash 1017 · DeepSeek v4 flash + varian uncensored ·
**GLM 5.2** · Muse Wonder · Muse Spark · minimax-m2.7 · step-5-preview · glm-5.3-flash ·
glm-5.3-flash-uncensored · deepseek-v4-flash-0731 · deepseek-v4.1-flash-free

### Kebijakan anti-abuse (kutipan, 31 Okt 2026)

> "Dari 195 hari-pengguna dalam sepekan terakhir, hanya satu akun yang pernah lewat batas,
> dan akun itu sampai 17.289 permintaan dalam sehari dari satu API key."

→ **4.000 request/hari tanpa kecuali**, reset 00.00 WIB. Pemakai rata-rata: 368 req/hari.

Grup: `Nilovr Pemberitahuan`. Bayar QRIS, aktivasi otomatis.

---

## 3. Jerouter — Gateway V2

Volume aktivasi tertinggi di survei ini: **1.725 notifikasi aktivasi dalam 1 bulan**.
Bot aktivasi otomatis + notifikasi real-time ke channel.

| Paket | Masa aktif |
|---|---|
| **Trial** | +1 hari |
| **Basic** | +3 hari |
| **Plus** | +7 hari |

Setiap notifikasi berisi klaim seragam:

> "✨ Selamat menikmati akses unlimited semua model AI!"

**Paket Reseller** (pengumuman 13 Okt 2026):

> "Unlimited sesi, IP, RPM — Generate Gambar & LLM (no limit)"

→ satu-satunya yang eksplisit mengklaim **tanpa batas RPM** di tier reseller.

**Update teknis:**
- Context window: General 256K → **512K**; JB 512K → 512K
- Model baru: `step-3.5-flash`, `step-3.5-flash-2603`
- Jerouter web: "segera"

Grup: `jerouter`, `jerouter (notif)`.

---

## 4. Limo Router — `@LimoRouter_bot` / `t.me/limorouter`

Paling murah di survei. Dijual lewat grup `Market AI`.

| Aspek | Keterangan |
|---|---|
| Klaim | "9 Model AI **UNLIMITED** — DeepSeek, GLM, Muse" |
| Batas | Unlimited · **512K Context** · **50 RPM** |
| Fitur | AI Uncensored + Text-to-Image · AI Coding · Auto-Failover |
| Beli | `@LimoRouter_bot` |
| Channel | `t.me/limorouter` |

### Daftar paket akses

| Durasi | Harga |
|---|---|
| 1 hari | **5K** |
| 3 hari | **10K** |
| 10 hari | **20K** |
| **30 hari** | **40K** |

**Promo referral:** 5 teratas dapat akses unlimited 1 bulan.

---

## 5. Nocta Digital — `nocta-digital.web.id`

Penawaran paling agresif dari sisi harga & positioning "uncensored".

> "Stop bayar AI mahal-mahal. **Rp45.000/bulan, token AI unlimited**, DeepSeek Uncensored
> tanpa refusal. Coba Gratis dulu, chat langsung ke Telegram `@Noctadigital_bot`.
> Base URL-nya OpenAI-compatible, jadi tinggal ganti base URL, langsung jalan."

| Aspek | Keterangan |
|---|---|
| Harga | **Rp45.000 / bulan** |
| Trial | **Gratis** |
| Positioning | murah + uncensored (tanpa refusal) |
| Endpoint | OpenAI-compatible, tinggal ganti base URL |
| Bot | `@Noctadigital_bot` |
| Web | `https://nocta-digital.web.id` |
| Batas | tidak dirinci di iklan |

Sumber: paid promote di `[Notifikasi Bot Sedulur Store]`, 2 Nov 2026.

---

## 6. Griphub Router — `griphubrouter.web.id`

**Bukan langganan bulanan** — pay-per-kredit. Dimasukkan sebagai pembanding karena
sering dibandingkan dengan paket unlimited.

| Aspek | Keterangan |
|---|---|
| Model | Claude Fable 5.1 · Opus 5.5 · GPT 6 Sol · GPT 6 Astra · Kimi K3 · GLM 5.3 |
| Akses mulai | **Rp15.000** |
| Skema | **1 kredit = Rp 300**, bayar QRIS (GoPay/OVO/Dana) |
| Klaim | "100% REAL DIRECT UPSTREAM TANPA PIHAK KE-3" · refund bila model palsu |
| Fitur | Vision delegation (DeepSeek/Qwen/GLM/MiniMax tetap bisa baca gambar) |
| Installer | Claude Code · GitHub Copilot · OpenCode · Hermes Agent · **9Router** · OmniRoute |
| Status | "Gak ada langganan" |

**Batas operasional yang terpantau (6 Nov 2026):**
- Profil default sempat berubah: **$5/hari** global daily budget
- Konfigurasi: **5 concurrent · 600 RPM**
- "saat ini belum ada kebijakan suspend akibat rpm tinggi"

Grup: `Griphub Router` (5.473 pesan dalam 1 bulan).

### 6.1 APIGOD — `apigod.cloud` / `@apigodz_bot`

**Paket paling lengkap datanya** karena dikirim sebagai pesan teks murni di grup
`APIGOD - Discussion https://apigod.cloud/` (bukan gambar flyer).

| Durasi | Harga |
|---|---|
| Unlimited 6 Jam | **Rp12.000** |
| Unlimited 1 Day | **Rp17.000** |
| Unlimited 3 Day | **Rp48.000** |
| Unlimited 7 Day | **Rp100.000** |

**Klaim yang tertulis eksplisit:**

> "BISA SEMUA MODEL · **UNLIMITED TOKEN** · **60 RPM**"
> "Langsung `@apigodz_bot` · #salampecut"

→ **Satu-satunya penyedia yang menulis "UNLIMITED TOKEN" secara harfiah** plus angka RPM
di iklannya. Tidak ada paket 30 hari — paket terpanjang 7 hari.

**Promo musiman (17–20 Agustus 2026):**

| Produk | Harga |
|---|---|
| 500 Juta Token — tanpa waktu (pakai sampai habis), all model | Rp100.000 |
| 1 Billion Token — tanpa waktu, all model | Rp200.000 |
| Paket Unlimited Token 7 Hari (all model) | Rp100.000 |

**Dijual juga di marketplace pihak ketiga:**

> "!APIGOD **UNLIMITED API CLAUDE SONNET 4.5** 1 DAY — Rp17.000"
> — 3 transaksi di `[Notifikasi Bot Sedulur Store]` (11 Okt, 18 Okt, 2 Nov 2026)

Artinya ada dua jalur pembelian: bot resmi `@apigodz_bot` atau reseller marketplace.

**⚠️ Catatan data (penting):** pesan paket APIGOD di grup mereka bertanggal
**2 Okt 2026 dan lebih lama**, sehingga **di luar rentang sync 1 bulan** (8 Okt – 7 Nov).
Itu sebabnya APIGOD tidak muncul di pemindaian awal berbasis DB. Data di atas
diambil langsung dari Telegram, bukan dari `telegram_data`.

---

## 7. Produk Sejenis dari Grup Jualan (akun premium, bukan API key)


Muncul di `Grup Rich Store`, `HEAVENPREM GANK`, `TESTIMONI RUMAH PRMIUM`, `BuatPremium Channel`.
**Bukan** router API — ini penjualan akun/plan resmi dengan harga patungan.

| Produk | Harga | Catatan |
|---|---|---|
| DIGEN AI — Ultra Max Plan (1 bulan) | $4 (asli $19.99) | "UNLIMITED standard models" + 13.000 Pro credits/bulan |
| HIGGSFIELD AI Pro (1 bulan) | Rp200.000 | 600 kredit/bulan + model gambar UNLIMITED |
| KREA AI Basic (1 bulan) | Rp50.000 | 5.000 kredit generate gambar & video |
| Gemini Pro 18 bulan | Rp15.000–25.000 | Famplan via invite, 5TB storage |
| MUSE AI 1B TOKEN | Rp10.500 | produk paling sering dibeli di Sedulur Store |
| "PROMO 200JT TOKEN 21D" | Rp30.577 | lewat `BuatPremium Channel` |
| "SUPER PROMO 100JT TOKEN 21D" | Rp15.443 | idem |
| AI AGENT API KEY — GODENTOPUP | 10M=Rp4.500 · 100M=Rp37.500 · 500M=Rp137.500 | per token, bukan unlimited |
| 45 Akun GROK CLI (Grok 4.7) | Rp17.000 | "bisa tumpuk di 9Router" |
| Jailbreak All Model (9router, Antigravity) | Rp40.000 | tools, bukan langganan |

→ Ini pasar berbeda dari router API, tapi **menunjukkan harga acuan pasar**:
"unlimited" versi akun resmi jauh lebih murah (Rp10.000–45.000) karena reseller memakai
celah plan keluarga/promo, bukan menjual ulang API.

---

## 8. Perbandingan Paket 30 Hari (fokus bulanan)

| Penyedia | Harga 30 hari | Batas diumumkan | Model unggulan |
|---|---|---|---|
| **Limo Router** | **40K** | 512K context · 50 RPM | DeepSeek, GLM, Muse |
| **Nocta Digital** | **Rp45.000** | tidak dirinci | DeepSeek Uncensored |
| **Cutad (Ultimate)** | cek `/pricing` | slot terbatas, tutup saat beban tinggi | DeepSeek v4-pro, GLM 5.2/5.3, step-5 |
| **NilovrAI — Batas Wajar** | **Rp296.000** | 4.000 req/hari · RPM 32 | DeepSeek v4.1, GLM 5.2, Muse |
| **NilovrAI — Tanpa Batas** | **Rp499.000** | tanpa batas req · RPM 42 · 10 concurrent | sama |
| **NilovrAI (reseller)** | **Rp598.800** | RPM 120 · 80 concurrent | sama |
| **Griphub Router** | *Rp300/kredit, tanpa langganan* | 600 RPM · 5 concurrent · $5/hari | Claude Fable 5.1, Opus 5.5, GPT 6 |
| **Jerouter** | bertingkat (1/3/7 hari) | reseller: unlimited sesi/IP/RPM | step-3.5-flash |
| **APIGOD** | *tidak ada 30 hari* — 7 hari = Rp100.000 | **60 RPM** · "UNLIMITED TOKEN" | tidak dirinci (klaim "semua model") |

**Selisih harga 15× (Rp40.000 → Rp598.800).** Bedanya bukan cuma kualitas model,
tapi **kejujuran & kelonggaran batas**:
- Yang murah membatasi RPM ketat (50 RPM ≈ 1 request/detik — tidak nyaman untuk agent berlapis)
- Yang mahal mengumumkan kuota request harian besar + konkurensi tinggi

---

## 9. Pola yang Berulang

### 9.1 "Unlimited" = unlimited token, bukan unlimited request

| Plafon | Dipakai oleh |
|---|---|
| Request/hari | NilovrAI (4.000/hari) |
| RPM | Limo (50) · NilovrAI (20–42) · Griphub (600) · Jerouter (unlimited di reseller) |
| Concurrent | NilovrAI (10) · Griphub (5) |
| Slot pembelian | Cutad ("Plan Unlimited sudah habis") |
| Konteks per model | Limo (512K) · Jerouter (512K) |
| Budget harian $ | Griphub ($5/hari) |

→ Nilai sebenarnya sebuah paket = **kuota request tersembunyi**. Yang mengumumkan angkanya
lebih bisa dipercaya daripada yang tidak.

### 9.2 Semua OpenAI-compatible

Cutad, NilovrAI, Nocta, Griphub, Limo — semuanya sediakan endpoint `…/v1`.
Konsekuensi praktis:
- Bisa dipasang langsung di Cline, Cursor, OpenCode, Claude Code, 9Router
- Bisa jadi **fallback berlapis** (provider A 403 → ganti base URL ke B)
- Bisa diuji `curl`, seperti di `modules/codex_cutad/fix_wire_api.py`

### 9.3 Risiko yang sudah muncul di chat

- **Model hilang tanpa pemberitahuan** — `CutadAgent-Pro` "menghilang dari lane"
- **Gangguan upstream berulang** — NilovrAI (17 Okt): `deepseek-v4-flash`,
  `deepseek-v4.1-flash`, `glm-5.3-flash`, `step-5-preview` mati dari sisi provider
- **Akses per tier** — "Not available in your plan"
- **Payment maintenance** — Cutad: payment mati 00.00–07.00 WIB
- **Paket ditutup saat ramai** — Cutad: "Plan Unlimited sudah habis, Close dulu"

---

## 10. Rekomendasi

| Tujuan | Pilihan |
|---|---|
| Coding agent harian (butuh stabil) | **NilovrAI Tanpa Batas** Rp499.000/30 hari — paling transparan batasnya |
| Eksperimen murah | **Limo Router** 40K/30 hari — tapi sadari 50 RPM |
| Coba dulu sebelum bayar | **Nocta** (gratis trial) atau **Jerouter Trial** (+1 hari) |
| Model frontier (Claude/GPT terbaru) | **Griphub Router** — kredit Rp300, tanpa langganan |
| Mau ikut model acuan survei | **Cutad** Daily → Ultimate |

**Saran uji sebelum bayar:**
1. `curl` ke `/v1/models` — pastikan model yang dijanjikan benar-benar ada
2. `curl` ke `/v1/chat/completions` dengan prompt kecil — cek 200 + jawaban
3. Uji **`stream: true`** terpisah — dari pengalaman `codex_cutad`, ada provider yang
   non-stream OK tapi stream gagal 400 `unsupported_parameter`
4. Ukur latensi & error rate 24 jam pertama sebelum perpanjang

---

## 11. Keterbatasan

- Data hanya dari grup Telegram yang diikuti akun `haidinata haidi` — penyedia di luar itu tidak terpantau
- Harga & paket dapat berubah kapan saja; semua angka adalah kondisi **8 Okt – 7 Nov 2026**
- Klaim "100% direct upstream" / "garansi" **belum diverifikasi independen** — itu klaim penjual
- DB hanya menyimpan **teks**; gambar harga, flyer, dan lampiran tidak ikut sehingga detail bisa hilang
- **Grup `APIGOD - Discussion` berisi 46 pesan tapi semuanya media/kosong** — paket APIGOD
  hanya muncul di 4 pesan teks bertanggal 2 Okt 2026 ke belakang, di luar rentang sync 1 bulan.
  Penyedia yang beriklan **hanya lewat flyer gambar** berisiko tidak terdeteksi sama sekali
- Email pembeli di notifikasi sudah tersamar (`voodokinxxx@gmail.com`) — jangan direkonstruksi
- Penamaan model bisa berubah: `z-ai/glm-5.3-flash` tercatat berganti jadi `glm-5.3-flash` (7 Nov 2026)

---

## 12. Rujukan

| Dokumen | Isi |
|---|---|
| `modules/codex_cutad/README.md` | Diagnosis `upstream_error` glm-5.2 cutad + arsitektur Codex→9Router |
| `modules/codex_cutad/documents/2026-11-06-upstream-error-glm52.md` | Analisa lengkap bisection payload |
| `modules/telegram_group_reader/documents/2026-11-07-catatan-keamanan-dan-automasi.md` | Temuan keamanan & pola automasi dari grup yang sama |
| `modules/telegram_group_reader/{reader,store,sync}.py` | Modul pengambil chat Telegram → MySQL |

---

## 13. Daftar Model per Penyedia

### 13.1 Cutad — 9 model (diverifikasi live via `/v1/models`, 7 Nov 2026)

| Model ID (persis) | Keluarga | Catatan |
|---|---|---|
| `deepseek-v4-pro` | DeepSeek | ✅ terverifikasi jawab PONG |
| `deepseek-v4.1-flash` | DeepSeek | cepat & murah |
| `glm-5.3-flash` | Zhipu/Z.ai | ✅ terverifikasi jawab PONG |
| `z-ai/glm-5.2` | Zhipu/Z.ai | ❌ **403 upstream_error** (7 Nov 2026) |
| `step-5-preview` | StepFun | preview |
| `solar-pro4` | Upstage | |
| `meituan/longcat-2.5` | Meituan | |
| `dots-studio/dots-3-note-preview` | Dots | preview |
| `reflection/beam-1.0-501b-a23b` | Reflection | MoE 501B |

Model yang **berganti nama**: `z-ai/glm-5.3-flash` → `glm-5.3-flash` (tanpa prefix).
Paket kredit per model tersedia, mis. "Plan Deepseek V.4.1 Flash (1017)".

---

### 13.2 NilovrAI — 13 model di paket Unlimited

**Daftar resmi 9 model (pengumuman 27 Okt 2026, sudah diuji jalan semua):**

| Model | Keluarga |
|---|---|
| `deepseek-uncensored` | DeepSeek (tanpa refusal) |
| `deepseek-v4-flash` | DeepSeek |
| `deepseek-v4-flash-0731` | DeepSeek |
| `deepseek-v4.1-flash` | DeepSeek |
| `deepseek-v4.1-flash-free` | DeepSeek |
| `glm-5.3-flash` | Zhipu/Z.ai |
| `glm-5.3-flash-uncensored` | Zhipu/Z.ai |
| `minimax-m2.7` | MiniMax |
| `step-5-preview` | StepFun |

**Tambahan (pengumuman 2 Nov 2026):**

| Model | Keluarga |
|---|---|
| `deepseek-v4.1-flash-1017` | DeepSeek |
| `glm-5.2` | Zhipu/Z.ai |
| `muse-wonder` (+ varian) | Muse |
| `muse-spark` (+ varian) | Muse |

**Catatan penting:** paket kredit punya akses lebih luas — disebut "**36 model AI** tinggal ganti
namanya", sementara paket Unlimited hanya 13. Model yang mati di provider otomatis
dikeluarkan dari daftar.

---

### 13.3 Jerouter — Gateway V2 (~17 model)

| Model | Keterangan |
|---|---|
| `step-3.5-flash` | teks |
| `step-3.5-flash-2603` | teks |
| `deepseek-unrestricted` | tanpa guardrail |
| `deepseek-v4.1-flash` | |
| `solar-mini4` | Upstage |
| `solar-pro4` | Upstage |
| `solar-unrestricted` | Upstage tanpa guardrail |
| `glm-unrestricted` | Zhipu tanpa guardrail |
| `kimi-k3-uncensored` | Moonshot |
| `glm-5.3-uncensored` | Zhipu |
| `glm-5.3-flash-uncensored` | Zhipu |
| `minimax-m3-uncensored` | MiniMax |
| `qwen-37-27b-uncensored` | Alibaba Qwen |
| `deepseek-v4-flash-uncensored` | DeepSeek |
| `laguna` | (disebut pengguna) |
| `mimo` | Xiaomi MiMo |
| + generate gambar | "no limit" di tier reseller |

**Fokus Jerouter: varian `uncensored`/`unrestricted`** — terbanyak di survei ini.
Konteks: General 512K, JB 512K.

---

### 13.4 Limo Router — 9 model

| Keluarga | Keterangan |
|---|---|
| **DeepSeek** | beberapa varian |
| **GLM** | varian Zhipu |
| **Muse** | varian Muse |
| AI Uncensored | varian tanpa guardrail |
| Text-to-Image | generate gambar |

Klaim: "9 Model AI UNLIMITED — DeepSeek, GLM, Muse" · 512K context · 50 RPM · Auto-Failover.
**ID model tidak dipublikasikan di iklan** — harus cek `/v1/models` setelah punya key.

---

### 13.5 Griphub Router — model frontier

| Model | Catatan |
|---|---|
| Claude Fable 5.1 | frontier |
| Opus 5.5 | frontier |
| GPT 6 Sol | OpenAI |
| GPT 6 Astra | OpenAI |
| Kimi K3 | Moonshot |
| GLM 5.3 | Zhipu |
| + "Mocin lainnya" | model lain |
| **Vision delegation** | DeepSeek/Qwen/GLM/MiniMax yang tak punya vision native tetap bisa baca gambar |

Catatan: `gpt-5.6-sol`, `gpt-6-astra`, `gpt-6.1-sol` sempat berstatus **"Testing model baru"** —
artinya tidak semua model stabil setiap saat.

---

### 13.6 Nocta Digital

| Model | Catatan |
|---|---|
| DeepSeek Uncensored | positioning utama: "tanpa refusal" |

Detail daftar lengkap tidak dipublikasikan di iklan — cek `https://nocta-digital.web.id`.
Base URL OpenAI-compatible.

---

### 13.7 Penyedia lain di grup (bansos / API key satuan)

**MAZOV — `https://mazov.site/v1`** (free $10 credit user baru)

| Model |
|---|
| `deepseek-v4.1-flash` |
| `glm-5.3-flash` |

**READY API KEY MODEL V1 — `@kodexsnip_bot`** (dijual per token, bukan unlimited) — 28 model:

| Model | Vision |
|---|---|
| `auto` | — |
| `claude-sonnet-5` | ✅ |
| `claude-opus-5` | ✅ |
| `claude-fable-5-b` | ✅ |
| `gpt-5.6` | ✅ |
| `gpt-5.6-sol` | ✅ |
| `gpt-5.6-terra` | ✅ |
| `gpt-5.6-luna` | ✅ |
| `gpt-5.6-sol-xhigh` | ✅ |
| `hy3` | — |
| `glm-5.1` · `glm-5.2` · `glm-5.2-mod` · `glm-5.3` · `glm-5.3-flash` · `glm-5.3-mod` | — |
| `deepseek-v4-flash` | — |
| `deepseek-v4-flash-vision-exp` | ✅ |
| `deepseek-v4-pro` · `deepseek-v4-pro-0813` · `deepseek-v4-mod` | — |
| `kimi-k2.6` · `kimi-k2.7-code` · `kimi-k2.7-code-highspeed` · `kimi-k3` · `kimi-k3-mod` | — |
| `mimo-v2.5-pro` | — |
| `minimax-m3` | — |

**Pricelist token** (bukan unlimited): 5M(7D)=Rp5.000 · 10M(7D)=Rp10.000 ·
20M(7D)=Rp15.000 · 50M(14D)=Rp25.000 · 100M(21D)=Rp45.000 · 200M(21D)=Rp80.000 ·
500M(28D)=Rp150.000 · 1B(28D)=Rp300.000. Support 9Router & orchestrator lain.

**Muse Meta Spark API KEY** — Rp10.000 (Sedulur Store, seller Vitacimin Store)

| Model |
|---|
| `muse-spark-1.3` · `muse-spark-1.3-contributor` |
| `muse-spark-1.2` · `muse-spark-1.2-contributor` |
| `muse-wonder-1.0` |

---

### 13.8 Ringkasan: siapa punya model apa

| Keluarga Model | Cutad | NilovrAI | Jerouter | Limo | Griphub | Nocta |
|---|---|---|---|---|---|---|
| **DeepSeek v4 / v4.1** | ✅ | ✅ | ✅ | ✅ | — | ✅ (uncensored) |
| **GLM 5.2 / 5.3** | ✅ | ✅ | ✅ | ✅ | ✅ | — |
| **Claude Opus/Sonnet/Fable** | — | — | — | — | ✅ | — |
| **GPT 6 / 5.6** | — | — | — | — | ✅ | — |
| **Kimi K2.7 / K3** | — | — | ✅ | — | ✅ | — |
| **MiniMax** | — | ✅ (m2.7) | ✅ (m3) | — | ✅ | — |
| **Muse** | — | ✅ | — | ✅ | — | — |
| **Qwen** | — | — | ✅ | — | ✅ (vision) | — |
| **StepFun** | ✅ (step-5) | ✅ (step-5) | ✅ (step-3.5) | — | — | — |
| **Solar / Upstage** | ✅ (solar-pro4) | — | ✅ | — | — | — |
| **Uncensored/unrestricted** | — | ✅ | ✅ (terbanyak) | ✅ | — | ✅ |
| **Jumlah model** | **9** | **13** Unlimited / 36 kredit | **~17** | **9** | **~7+** | tidak disebut |

**Kesimpulan:**

- Butuh **Claude/GPT frontier** → **Griphub Router**
- Butuh **DeepSeek/GLM murah unlimited** → **NilovrAI / Limo / Cutad**
- Butuh **varian uncensored terbanyak** → **Jerouter**
- Butuh **paling banyak pilihan model** (28, tapi bayar per token) → `@kodexsnip_bot`

**Tidak ada satu penyedia yang punya semua model.** Ini alasan praktis untuk memakai
router berlapis (9Router) dengan beberapa provider sekaligus.






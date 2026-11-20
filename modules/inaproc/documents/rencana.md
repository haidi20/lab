# Rencana Tool Pengumpul Data TKDN INAPROC

## Tujuan

Mengumpulkan data TKDN (Jenis Produk, Merek, Tipe, Uraian Produk, Standard, Nilai)
untuk sekumpulan nomor SPT yang berurutan, tanpa mengetik nomor satu per satu di
browser. Hasil akhir bisa dilihat dan dicari di FE (filter, sorting, pagination)
serta diekspor ke CSV atau JSON. Data disimpan di database MySQL supaya
pencarian berikutnya tidak perlu request ulang ke INAPROC.

Selain TKDN, modul ini direncanakan mengintegrasikan **INAPROC API Gateway**
resmi untuk data katalog/pengadaan. Kedua jalur dipisahkan: API Gateway untuk
data katalog, dan portal penyedia untuk TKDN.

## Batas Operasi: Read-Only ke INAPROC

Aplikasi ini adalah **tool pencarian**, bukan sistem manajemen penyedia. Semua
interaksi ke INAPROC bersifat **read-only**:

| Operasi | Ke INAPROC | Keterangan |
| --- | --- | --- |
| Baca/cari data katalog | Boleh | Lewat API Gateway resmi, GET saja |
| Baca/cari nomor SPT TKDN | Boleh | Lewat halaman portal penyedia dengan Playwright |
| Membuka link detail produk | Boleh (oleh user) | Link dibuka di browser user yang sudah login |
| Insert/update/delete produk | **Tidak boleh** | Bukan Seller API; tidak ada push produk/stok/harga |
| Upload file/template | **Tidak boleh** | Di luar scope aplikasi |
| Mengubah status/verifikasi TKDN | **Tidak boleh** | Aplikasi hanya membaca hasil pencarian |

Yang boleh menulis adalah **MySQL lokal** (`tkdn_rows`, `tkdn_checks`, dan tabel
Gateway) sebagai cache hasil baca. Upsert lokal itu bukan operasi tulis ke
INAPROC dan tidak mengubah data di sana. Fokus fitur tetap sesuai `tugas.md`:
mencari produk/merek dari nomor SPT TKDN dan mencari barang di katalog.

Tujuan satu-satunya penulisan ke DB aplikasi adalah **mempercepat pencarian
berikutnya**:

```text
Pencarian pertama  -> data belum ada di DB -> baca dari INAPROC -> upsert ke DB app
Pencarian kedua    -> data sudah ada di DB -> jawab dari DB app -> INAPROC tidak disentuh
```

Upsert ke DB app **bukan** sinkronisasi dua arah dan **bukan** cara mengubah
data INAPROC. Kalau data di INAPROC berubah, DB app hanya ikut berubah saat user
menjalankan refresh/sync ulang; tidak ada push dari DB app ke INAPROC.

## Klarifikasi Istilah: Login INAPROC, Bukan Login Aplikasi

Aplikasi ini **tidak memiliki akun, registrasi, atau login pengguna sendiri**.
Tidak ada tabel user, role, atau sesi aplikasi. Form di FE bukan gerbang masuk
aplikasi; form itu hanya meneruskan email/password **akun penyedia INAPROC** ke
backend supaya backend bisa membuka sesi INAPROC.

- **Koneksi INAPROC** = proses membuka sesi penyedia INAPROC lewat Playwright.
- **Sesi INAPROC** = `storageState.json` yang menyimpan cookie/localStorage sesi
  penyedia INAPROC. Backend memakai state itu untuk membuka halaman TKDN.
- **`POST /api/login`** = nama teknis endpoint untuk membuka sesi INAPROC, bukan
  autentikasi aplikasi. Path ini dipertahankan agar kontrak API tetap sederhana.
- FE tetap bisa dibuka tanpa login aplikasi. Panel kerja menampilkan form koneksi
  INAPROC sampai sesi INAPROC berhasil terhubung.

Catatan: `POST /api/login`, `POST /api/logout`, dan `GET /api/session` adalah nama
teknis endpoint untuk siklus sesi INAPROC. Ketiganya tidak membuat, menyimpan, atau
mengelola akun pengguna aplikasi.

## Integrasi INAPROC API Gateway Resmi

INAPROC punya **dua jalur data yang tidak boleh dicampur**. API Gateway hanya
dipakai untuk **pencarian data read-only**; portal penyedia tetap dipakai untuk
TKDN dan sebagai target tautan hasil pencarian.

| Jalur | Sumber | Kegunaan di modul ini | Autentikasi |
| --- | --- | --- | --- |
| **INAPROC API Gateway** | `https://data.inaproc.id` | Data katalog/pengadaan resmi: penyedia, produk e-katalog, kategori, e-purchasing, program | `Authorization: Bearer <token>` dari Developer Portal |
| **Portal Penyedia TKDN** | `https://penyedia.inaproc.id/products/tkdn` | Pencarian nomor SPT TKDN | Cookie/localStorage sesi penyedia di `storageState.json` |

API Gateway resmi bersifat **read-only** untuk data pengadaan. Dokumentasi resmi
tidak membuka endpoint TKDN dari `penyedia.inaproc.id`, jadi pencarian TKDN tetap
memakai Playwright sesuai keputusan sebelumnya. API Gateway juga bukan Seller API:
tidak dipakai untuk push/update produk atau stok.

Hasil audit dokumentasi resmi `https://data.inaproc.id/docs/spesifikasi-api`
(2026-11-20): halaman itu memuat 76 path `/api/v1/...` untuk E-Katalog, RUP,
tender/non-tender, dan dashboard, tetapi **tidak ada satu pun kemunculan kata
`TKDN`**. Karena itu Playwright tetap diperlukan khusus untuk membaca halaman
`penyedia.inaproc.id/products/tkdn?keyword=...`.

Hasil pencarian produk dapat menyimpan `source_url` ke halaman INAPROC. User
bisa klik URL itu untuk membuka detail di portal INAPROC. Aplikasi **tidak**
melakukan login ulang, menyisipkan cookie, atau membuka halaman tersebut dengan
sesi backend; user harus sudah login ke INAPROC di browser masing-masing.

### Syarat akses API Gateway

1. Registrasi dan verifikasi akun di `https://akun.inaproc.id`.
2. Ajukan role akses melalui **Manajemen Peran**. Ikuti nama role yang benar-benar
   muncul di portal (`API Integrator` atau `Data Integrator`).
3. Siapkan surat permohonan akses ke LKPP, data instansi/perusahaan, NPWP,
   PIC teknis, dan penjelasan use case integrasi.
4. Saat membuat token di `https://data.inaproc.id/portal`, isi deskripsi token,
   spesifikasi teknis, estimasi volume request per hari, public egress IP server,
   dan pilih API yang benar-benar dipakai.
5. Tunggu persetujuan token. Dokumentasi menyebut review sekitar 1-3 hari kerja;
   verifikasi role bisa lebih lama karena bergantung LKPP.
6. Simpan token hanya sebagai environment variable backend. Token tidak pernah
   dikirim ke FE, tidak masuk log, dan tidak masuk git.

Catatan login portal: `storageState.json` tetap dipakai hanya oleh Playwright
TKDN. Ia tidak dipakai untuk mengaktifkan link yang diklik user di FE. Link
produk INAPROC dibuka langsung oleh browser user; kalau sesi portal user tidak
aktif, INAPROC akan meminta login secara normal.

### Konfigurasi API Gateway

```env
INAPROC_API_BASE_URL=https://data.inaproc.id
INAPROC_API_TOKEN=
INAPROC_API_TIMEOUT=30
INAPROC_API_MAX_RETRIES=3
INAPROC_API_ENABLED=false
```

`INAPROC_API_ENABLED=true` hanya berlaku kalau token sudah tersedia. Staging
`https://data.eproc.dev` cukup dipakai kalau token staging diberikan; production
tetap menjadi default rencana.

### Modul client baru

Tambahkan satu adapter terpisah, misalnya `modules/inaproc/gateway.py`:

- `InaprocGatewayClient` untuk GET JSON dengan `Authorization: Bearer ...`.
- Pagination cursor: baca `data`, `meta.has_more`, dan `meta.cursor`; berhenti
  saat `has_more=false` atau cursor hilang.
- Rate limit handling: baca `X-Ratelimit-Limit`, `X-Ratelimit-Remaining`, dan
  `X-Ratelimit-Reset`.
- Retry exponential backoff + jitter hanya untuk `429` dan `5xx`.
- `400`, `401`, `403`, dan `404` tidak di-retry; diterjemahkan menjadi error
  yang jelas.
- Redaksi token pada log dan exception message.
- Mapping respons standar ke model internal supaya service tidak bergantung pada
  bentuk JSON mentah.

Contoh endpoint resmi yang dipetakan:

| Endpoint Gateway | Data |
| --- | --- |
| `GET /api/v1/ekatalog/penyedia-detail` | Detail penyedia berdasarkan `kode_penyedia` |
| `GET /api/v1/ekatalog/list-produk-penyedia` | Produk penyedia; `limit` maksimum 1000 dan cursor |
| `GET /api/v1/ekatalog/list-kategori-produk` | Kategori drill-down level 1-3 |
| `GET /api/v1/ekatalog/paket-e-purchasing` | Paket e-purchasing per KLPD dan tahun |
| `GET /api/v1/ekatalog/e-purchasing-by-produk` | Transaksi/realisasi per produk |
| `GET /api/v1/master/program` | Master program |

Cakupan resmi API Gateway juga mencakup arsip E-Katalog V5, RUP/SiRUP, dan
SPSE (tender/non-tender). Modul ini memprioritaskan E-Katalog V6 dan master
program lebih dulu. RUP/SPSE masuk fase berikutnya setelah path dan parameter
resminya dikonfirmasi dari dokumentasi/token yang disetujui; jangan mengarang
path di luar dokumentasi.

### Endpoint internal aplikasi

Scope API internal disesuaikan dengan scope token yang disetujui. Rencana awal:

| Endpoint | Metode | Kegunaan |
| --- | --- | --- |
| `/api/gateway/status` | GET | Token ada/tidak, enabled/disabled, ringkasan run terakhir |
| `/api/gateway/sync/{scope}` | POST | Mulai job sync untuk `penyedia`, `produk`, `kategori`, `paket`, `transaksi`, atau `program`; balas `202 {"job": ...}` |
| `/api/gateway/sync/{scope}/status` | GET | Status job sync terakhir untuk scope tersebut |
| `/api/gateway/produk` | GET | Cari/filter/sort/paginate produk dari MySQL |
| `/api/gateway/epurchasing` | GET | Cari/filter/sort/paginate data e-purchasing dari MySQL |
| `/api/gateway/export` | GET | Ekspor CSV/JSON untuk `kind=produk|paket|transaksi` dengan filter yang sama seperti pencarian |

`GET /api/gateway/produk` mengembalikan `source_url` yang bisa diklik untuk
produk/e-katalog. Backend hanya menyimpan/mengembalikan URL resmi dari data API;
url tidak dibuka oleh backend dan tidak dipakai untuk scraping halaman detail.

Semua route sync berbentuk job berjalan di background, punya status, dan hanya
menjalankan satu job per scope. FE memakai tombol sync dengan disabled loading
state, bukan polling endpoint eksternal. Di sini "sync" berarti **menarik data
INAPROC ke cache MySQL**, bukan mengirim perubahan dari MySQL ke INAPROC.

Perilaku yang sudah berlaku:

- Request sync mengembalikan `202 Accepted` beserta objek `job`.
- Scope yang sama saat job masih berjalan menghasilkan `409 job_aktif`.
- Scope berbeda boleh berjalan paralel; masing-masing punya status sendiri.
- Scope tidak dikenal menghasilkan `422`.
- `GET /api/gateway/status` mengembalikan `produk_count`, `paket_count`,
  `transaksi_count`, daftar `scopes`, dan `last_run`. Token tidak pernah
  dikembalikan ke FE.

### Skema MySQL API Gateway

Tabel tambahan dibuat idempotent saat startup dengan komentar tabel. Kunci unik
dan upsert mengikuti ID resmi API, bukan nama/teks yang bisa berubah:

| Tabel | Fungsi | Kunci/upsert |
| --- | --- | --- |
| `inaproc_api_sync_runs` | Audit job sync: scope, parameter, status, cursor terakhir, total item, pesan error, waktu mulai/selesai | `id` |
| `inaproc_penyedia` | Master penyedia | `kode_penyedia` |
| `inaproc_produk` | Produk e-katalog dan relasi penyedia/kategori | `kd_produk` + kode penyedia/kategori resmi |
| `inaproc_kategori` | Kategori level 1-3 | kode kategori resmi per level |
| `inaproc_paket_epurchasing` | Paket e-purchasing | ID/kode paket resmi + tahun/KLPD |
| `inaproc_transaksi_epurchasing` | Realisasi/transaksi per produk | `order_id` |
| `inaproc_master_program` | Master program | kode/ID program |

Prinsip tabel:

- Kolom mentah penting disimpan apa adanya; kolom turunan seperti nama normal
  dipakai hanya untuk pencarian.
- `source_url` disimpan hanya bila tersedia dari API. Nilai ini dipakai sebagai
  link ke portal INAPROC, bukan sebagai input scraping.
- Semua tabel Gateway berada di database `INAPROC_MYSQL_DATABASE` yang sama
  dengan tabel TKDN, tetapi tidak ada foreign key lintas jalur dan tidak ada
  proses TKDN yang menulis tabel Gateway.
- Semua upsert `INSERT ... ON DUPLICATE KEY UPDATE` dan idempotent.
- `updated_at` diperbarui saat upsert, `source_updated_at` menyimpan nilai resmi
  dari API bila tersedia.
- Index mengikuti filter utama: kode penyedia, kode produk, kategori, tahun,
  KLPD, dan waktu update.
- Tidak ada fallback SQLite/file. Semua data API Gateway masuk MySQL.

Sebelum implementasi, siapkan database sekali (contoh):

```sql
CREATE DATABASE IF NOT EXISTS inaproc
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

`gateway_store.py` membuat tabel Gateway secara idempotent saat startup, sama
seperti `TkdnMysqlStore.create_schema()`. Nama tabel, kunci unik final, dan tipe
kolom mengikuti respons resmi API setelah token disetujui; yang dikunci di sini
adalah identitas bisnis dan strategi upsert, bukan tebakan nama field.

### Event upsert API resmi

Semua baris di bawah adalah penulisan ke **DB aplikasi**. Tidak ada event yang
mengirim INSERT/UPDATE/DELETE ke INAPROC.

| Event | Penulisan DB |
| --- | --- |
| Sync manual dimulai | INSERT `inaproc_api_sync_runs` status `running` |
| Setiap halaman cursor diterima | UPDATE run: cursor, jumlah halaman, `last_ok_at` |
| Upsert batch halaman | Upsert tabel scope terkait secara batch/idempotent |
| Sync halaman berhasil | UPDATE run tambah total item |
| Sync selesai | UPDATE run status `success`, cursor akhir, waktu selesai |
| Sync gagal | UPDATE run status `failed`, error code/message |
| Token expired | UPDATE run status `failed` dengan `TOKEN_EXPIRED`; tidak retry tanpa token baru |
| Rate limit | UPDATE run dengan `retry_status`, `retry_after`, `retry_attempt`; status `retrying` sebelum backoff lalu `running` |
| API 4xx/5xx | UPDATE run gagal untuk non-retryable; backoff untuk 429/5xx |
| Token belum tersedia | Tidak memanggil API dan tidak membuat baris data; status API Gateway `disabled` |
| Data duplikat diterima | Upsert baris yang sama, jumlah fisik tabel tidak bertambah |

Catatan implementasi: `paket` dan `transaksi` adalah dua scope terpisah. Sync
`paket` menulis ke `inaproc_paket_epurchasing`; sync `transaksi` menulis ke
`inaproc_transaksi_epurchasing`. Status `GET /api/gateway/status` melaporkan
`paket_count` dan `transaksi_count` secara terpisah.

### Aturan DB-first untuk API Gateway

Aturan yang sama dipakai seperti TKDN:

```text
FE mencari produk/e-purchasing -> query MySQL dulu.
Data sudah ada -> jawab dari DB, tanpa memanggil API Gateway.
Data belum ada/sync diminta -> panggil API Gateway, lalu simpan ke MySQL.
GET /api/search TKDN -> tetap hanya MySQL dan Playwright tidak dipanggil.
Hasil produk -> tampilkan source_url untuk dibuka user di INAPROC.
```

Untuk data Gateway, aplikasi memakai strategi **cache-first**: pencarian dan
filter selalu dilayani MySQL. Sync hanya dijalankan saat user memintanya atau
saat data scope tersebut belum pernah masuk. Setelah sync selesai, halaman
produk dan e-purchasing otomatis memuat ulang dari DB.

"Pencarian read-only" di sini berarti **membaca data**, bukan memanggil Gateway
setiap kali user mengetik atau klik hasil. API Gateway hanya dipanggil oleh
sync/refresh terencana supaya volume API mudah dikontrol dan hasil tetap cepat
dari DB. Link `source_url` tidak memicu request backend.

### Rencana test API Gateway

| Test | Perilaku |
| --- | --- |
| Client mengirim Bearer token | Header auth benar dan token tidak muncul di log |
| Cursor pagination | Loop berhenti saat `has_more=false` |
| Retry 429/5xx | Backoff + jitter, maksimum sesuai config |
| Tidak retry 400/401/403/404 | Error langsung dipetakan |
| Token kosong | `INAPROC_API_ENABLED` efektif false dan tidak request |
| Upsert idempotent | Data sama dua kali tidak menambah baris |
| Upsert hanya DB app | Test memastikan upsert menulis ke fake MySQL dan tidak ada request tulis ke INAPROC |
| Sync run tersimpan | Status `running`, `success`, dan `failed` tercatat |
| Duplikat halaman | Tidak menggandakan data |
| Link hasil produk | `source_url` diambil dari data resmi dan dibuka user, bukan dibuka backend |
| TKDN tetap Playwright | Alur TKDN tidak memanggil Gateway |

### Keputusan integrasi resmi

- API Gateway resmi adalah jalur untuk data katalog/pengadaan.
- API Gateway hanya untuk pencarian/read-only; produk yang cocok cukup diberi
  URL INAPROC agar dibuka user yang sudah login di portal.
- Backend tidak membuka `source_url`, tidak login ke portal lewat link, dan
  tidak memakai `storageState.json` untuk tautan FE.
- TKDN tetap lewat portal penyedia dengan Playwright karena endpointnya tidak
  ada di dokumentasi publik API Gateway.
- `INAPROC_API_TOKEN` dan `storageState.json` adalah kredensial berbeda dan
  tidak boleh saling menggantikan.
- Implementasi Gateway menunggu token disetujui; tanpa token, fitur ini tetap
  nonaktif dan tidak mengganggu fitur TKDN.

## Arsitektur Baru: FE -> BE -> INAPROC

User mencari lewat **frontend**, backend menjawab dari **MySQL** lebih dulu.
Scraping hanya dijalankan untuk **nomor SPT yang belum ada** (atau masih
`error`) di database. Sumber scraping adalah **halaman TKDN INAPROC yang
dirender di browser**: backend membuka halaman itu dengan Playwright, menunggu
tabel selesai render, lalu membaca HTML tabelnya. **Tidak memakai GraphQL dan
tidak memanggil endpoint internal INAPROC secara langsung.**

```
[FE: hubungkan sesi INAPROC sekali] --POST /api/login--> [Playwright headless -> storageState.json]
        |
[User di FE: cari produk/merek] --GET /api/search?q=acer--> [MySQL saja, tanpa scraping]
        |
[User di FE: cari satu nomor SPT] --POST /api/lookup--> [cek tkdn_checks]
        |                                                 |-- found/empty --> balas dari DB
        |                                                 |-- belum ada/error --> scraping
        v
[Backend Python (FastAPI)]
        |  startup: connect_mysql() + TkdnMysqlStore buat tabel
        |  lookup/collect selalu cek DB dulu
        |  -- nomor final (found/empty) --> langsung kembalikan hasil (tanpa INAPROC)
        |  -- nomor belum ada/error -->
        v
[Playwright + storageState sesi INAPROC]
        |  buka https://penyedia.inaproc.id/products/tkdn?keyword=<nomor SPT>
        |  tunggu tabel hasil render
        |  ambil HTML tabel -> parser.py
        |  delay + backoff
        v
[Baris TKDN] -> [simpan ke MySQL] -> [JSON response ke FE]
```

**Poin penting**

- **Koneksi INAPROC cukup 1x dari FE**, lalu `storageState.json` dipakai ulang.
  Tidak ada koneksi ulang di dalam loop request. Ini bukan login aplikasi.
- **DB-first untuk nomor SPT**: `POST /api/lookup` mengecek `tkdn_checks` lebih
  dulu. Nomor yang sudah `found`/`empty` dijawab dari MySQL tanpa membuka
  INAPROC. Scraping hanya terjadi kalau nomor belum ada atau status terakhirnya
  `error`.
- **Pencarian produk/merek tidak pernah scraping**: `GET /api/search?q=acer`
  hanya query MySQL. Halaman INAPROC mencari berdasarkan nomor SPT, bukan merek,
  jadi pencarian merek tidak bisa dijadikan alasan untuk scraping.
- **Nomor SPT punya jalur khusus**: `POST /api/lookup` untuk satu nomor,
  `POST /api/collect` untuk rentang. Keduanya cek DB dulu dan hanya men-scrape
  nomor yang belum final. `GET /api/search` tidak pernah men-scrape.
- **Collect tetap DB-first**: `POST /api/collect` melewati nomor yang sudah final
  dan hanya men-scrape nomor yang belum ada/`error`. Ini mencegah request ulang
  ke INAPROC untuk data yang sudah tersimpan.
- **MySQL wajib hidup**: backend tidak punya fallback ke SQLite/file. Kalau
  koneksi gagal saat startup, API berhenti dengan pesan konfigurasi yang jelas;
  kalau koneksi putus saat request, endpoint mengembalikan `503 db_unavailable`.
- Endpoint `POST /api/collect` dipakai untuk mengisi cache rentang nomor;
  `GET /api/search?q=...` dipakai user untuk mencari produk/merek (dari cache).
- FE hanya konsumsi API BE. FE **tidak** pernah menyimpan kredensial atau state
  sesi INAPROC.

### Konsep DB-first (wajib)

Aturan tunggal yang mengikat seluruh alur:

```
data yang dicari sudah ada di DB?
  ya  -> jawab dari DB, JANGAN scraping
  tidak -> baru scraping, lalu simpan ke DB
```

Rinciannya:

| Jenis pencarian | Endpoint | Cek DB dulu | Scraping |
| --- | --- | --- | --- |
| Produk / merek / tipe / uraian / nilai | `GET /api/search` | Selalu, langsung ke `tkdn_rows` | **Tidak pernah** |
| Satu nomor SPT | `POST /api/lookup` | Cek `tkdn_checks` nomor itu | Hanya bila belum ada / `error` |
| Rentang nomor SPT | `POST /api/collect` | Cek `tkdn_checks` per nomor | Hanya nomor yang belum ada / `error` |
| Paksa ambil ulang | `POST /api/refresh` | Hapus nomor dulu, lalu ambil ulang | Selalu (memang tujuan refresh) |

Definisi **"sudah ada di DB"**:

- Nomor dengan status `found` **dan** punya minimal satu baris di `tkdn_rows`
  -> data final, dibalas dari `tkdn_rows`.
- Nomor dengan status `found` tetapi **tidak punya baris** di `tkdn_rows`
  -> data tidak konsisten (mis. baris terhapus manual); jangan dianggap final.
  Reset status ke `error` dengan `error_msg='data_tidak_konsisten'`, lalu
  scraping ulang.
- Nomor dengan status `empty` -> hasil final "tidak ada data", dibalas tanpa
  scraping ulang. Kalau ternyata masih ada baris `tkdn_rows` untuk nomor itu,
  hapus baris yatim tersebut, lalu tetap jawab dari DB tanpa scraping ulang.
- Nomor dengan status `error` -> **belum final**, akan dicoba scraping lagi.
- Nomor tanpa baris di `tkdn_checks` -> belum pernah diproses, scraping.

Aturan konsistensi ini berlaku sama untuk `POST /api/lookup` dan
`POST /api/collect`. Tanpa aturan ini, status `found` yang kehilangan barisnya
bisa membuat nomor selamanya di-skip tanpa pernah di-scrape ulang.

#### Skenario nomor yang sama dicari dua kali

| Aksi | Isi `tkdn_checks` | Scraping? | Sumber respons |
| --- | --- | --- | --- |
| Lookup pertama | tidak ada | ya, sekali | `scrape` |
| Lookup kedua | `found` / `empty` | tidak | `db` |
| Lookup ketiga | `found` / `empty` | tidak | `db` |
| Refresh manual | dihapus lalu diisi lagi | ya, sekali | `scrape` |
| Collect `force=true` | di-UPSERT ulang | ya, sekali per nomor | `scrape` |

Jadi INAPROC hanya disentuh pada lookup pertama (atau setelah refresh/force),
bukan pada setiap pencarian.

Alur `POST /api/lookup` (satu nomor):

```
POST /api/lookup {nomor}
  |
  +-- validasi format nomor (5 bagian)          -> 422 bila salah
  +-- SELECT tkdn_checks WHERE number = ?
        |
        +-- found  -> SELECT tkdn_rows WHERE number = ?
        |              |-- ada baris -> 200 {source: "db"}
        |              +-- kosong -> UPSERT status error (data_tidak_konsisten) -> scraping
        +-- empty  -> hapus baris tkdn_rows yatim (bila ada)
        |              -> 200 {source: "db", status: "empty", items: []}
        +-- error  -> lanjut scraping (retry)
        +-- tidak ada -> lanjut scraping
        |
  +-- cek sesi INAPROC (hanya bila perlu scraping) -> 401 belum_login
  +-- Playwright buka halaman TKDN -> parser
  +-- UPSERT tkdn_rows + tkdn_checks (transaksi per nomor)
  +-- 200 {source: "scrape", status, items}
```

Efek yang diharapkan: user yang mencari nomor yang sama dua kali hanya
menyentuh INAPROC sekali. Pencarian kedua dibalas dari MySQL dan tidak menambah
beban ke INAPROC.

### File tambahan untuk arsitektur FE/BE

| File | Fungsi |
| --- | --- |
| `modules/inaproc/api/app.py` | Aplikasi FastAPI: `/api/login`, `/api/logout`, `/api/session`, `/api/search`, `/api/lookup`, `/api/collect`, `/api/collect/preview`, `/api/collect/cancel`, `/api/status`, `/api/export`, `/api/refresh` |
| `modules/inaproc/api/auth.py` | Koneksi INAPROC headless (`email`/`password`) + validasi `storageState.json`; bukan autentikasi aplikasi |
| `modules/inaproc/api/login.py` | Fallback interaktif Playwright untuk koneksi INAPROC (OTP/captcha); koneksi normal lewat `POST /api/login` |
| `modules/inaproc/api/scraper.py` | Buka halaman TKDN dengan Playwright + `storageState.json`, tunggu tabel render, kembalikan HTML/baris |
| `modules/inaproc/api/parser.py` | Parse tabel HTML hasil render menjadi baris TKDN (jalur utama, bukan fallback) |
| `modules/inaproc/api/config.py` | `InaprocDbConfig` dari env `INAPROC_MYSQL_*` (+ fallback host/user), memakai loader `.env` yang sudah ada di repo |
| `modules/inaproc/api/db.py` | `connect_mysql(config)`: `pymysql` + `DictCursor` + `charset=utf8mb4`, dipanggil saat startup API |
| `modules/inaproc/api/cache.py` | `TkdnMysqlStore`: simpan/ambil hasil ke MySQL, query by merek/produk |
| `modules/inaproc/api/gateway.py` | `InaprocGatewayClient`: GET JSON API Gateway resmi, Bearer token, cursor pagination, rate limit, retry 429/5xx, redaksi token |
| `modules/inaproc/api/gateway_store.py` | Upsert dan query MySQL untuk penyedia/produk/kategori/e-purchasing/program + audit sync run |
| `modules/inaproc/api/gateway_sync.py` | Orkestrasi sync per scope: jalan di background, cek DB-first, simpan cursor/progress |
| `modules/inaproc/api/schemas.py` | Model Pydantic untuk request/response API |
| `modules/inaproc/web/index.html` | Entry point Vite untuk aplikasi Vue 3 |
| `modules/inaproc/web/package.json` | Dependency FE: Vue 3, TypeScript, Bootstrap 5, Vite, Pinia, Vitest |
| `modules/inaproc/web/vite.config.ts` | Config Vite + proxy `/api` ke FastAPI saat development |
| `modules/inaproc/web/tsconfig.json` | Config TypeScript FE |
| `modules/inaproc/web/src/main.ts` | Bootstrap aplikasi Vue + Pinia + Bootstrap 5 |
| `modules/inaproc/web/src/App.vue` | Layout utama: form pencarian, tabel hasil, panel progres |
| `modules/inaproc/web/src/types.ts` | Tipe TS untuk request/response API dan baris TKDN |
| `modules/inaproc/web/src/api.ts` | Wrapper `fetch` ke endpoint BE (`/api/search`, `/api/lookup`, `/api/collect`, `/api/status`, `/api/refresh`) |
| `modules/inaproc/web/src/stores/tkdn.ts` | Pinia store (VM): state filter/hasil/status/chunk, action search/lookup/collect/poll/refreshNumber |
| `modules/inaproc/web/src/stores/inaprocSession.ts` | Pinia store: status sesi INAPROC, action connect/disconnect |
| `modules/inaproc/web/src/components/ConnectInaprocForm.vue` | Form email/password akun penyedia INAPROC ke `POST /api/login`, disabled + spinner saat proses |
| `modules/inaproc/web/src/components/SearchForm.vue` | Input keyword (cari di DB) + input satu nomor SPT (lookup DB-first) + tombol cari (disabled saat loading) |
| `modules/inaproc/web/src/components/ResultTable.vue` | Tabel hasil (merek, tipe, uraian, standard, nilai, nomor SPT) + tombol refresh per baris |
| `modules/inaproc/web/src/components/CollectForm.vue` | Nomor contoh + rentang pilihan user + Cek Rentang + Mulai/Batal |
| `modules/inaproc/web/src/components/PaginationBar.vue` | Info jumlah, pindah halaman, tombol ekspor |
| `modules/inaproc/web/src/components/SessionBadge.vue` | Status sesi INAPROC dari `/api/session` |
| `modules/inaproc/web/src/components/CollectProgress.vue` | Indikator progres collect dari `/api/status` |
| `modules/inaproc/web/tests/tkdn.spec.ts` | Vitest: store search/collect sukses & gagal, render komponen |
| `modules/inaproc/api/tests/test_auth.py` | Test validasi state sesi dan koneksi INAPROC headless dari state dummy |
| `modules/inaproc/api/tests/test_exporter.py` | Test CSV & JSON |
| `modules/inaproc/api/tests/test_scraper.py` | Test navigasi Playwright, deteksi redirect login, timeout, dan retry dengan fake page |
| `modules/inaproc/api/tests/test_collector.py` | Test loop rentang, skip cache, cancel, progres |
| `modules/inaproc/api/tests/test_api.py` | Test endpoint FastAPI dengan dependency/stub, termasuk lookup DB-first |
| `modules/inaproc/api/tests/test_spt.py` | Test parse dan rentang nomor SPT |
| `modules/inaproc/api/tests/test_schemas.py` | Test validasi request/response API |
| `modules/inaproc/api/tests/test_cache.py` | Test MySQL store dengan fake connection factory, filter, sort, pagination |
| `modules/inaproc/api/tests/test_db.py` | Test config env, koneksi MySQL, dan pemetaan error koneksi |
| `modules/inaproc/api/tests/test_cli.py` | Test argumen dan dispatch CLI dengan mock |
| `modules/inaproc/api/tests/test_login.py` | Test fallback koneksi INAPROC interaktif dengan Playwright fake |
| `modules/inaproc/api/tests/test_parser.py` | Test parser tabel HTML (tabel kosong, beberapa baris, nilai desimal) |
| `modules/inaproc/api/tests/test_gateway.py` | Test client API Gateway: Bearer token, cursor, retry 429/5xx, no-retry 4xx, token tidak bocor di log |
| `modules/inaproc/api/tests/test_gateway_store.py` | Test upsert idempotent dan audit `inaproc_api_sync_runs` dengan fake connection factory |
| `modules/inaproc/api/tests/test_gateway_sync.py` | Test sync per scope, DB-first, resume cursor, dan status job |
| `modules/inaproc/pyproject.toml` | Metadata modul + dependency (`fastapi`, `playwright`, `uvicorn`, `pymysql`) untuk `pip install -e modules/inaproc` |
| `.env.example` (root, update) | Tambah `INAPROC_MYSQL_DATABASE=inaproc` dan `INAPROC_API_*`; jangan mengubah `MYSQL_DATABASE` milik modul lain |
| `modules/inaproc/README.md` | Cara menjalankan BE + FE, koneksi sesi INAPROC, collect, dan catatan sesi |

### Perubahan pada file yang sudah direncanakan

- `scraper.py`: dipakai oleh `api.py` dan `collector.py`, bukan langsung oleh CLI.
- `collector.py`: hasilnya ditulis ke `cache.py` (MySQL) secara inkremental,
  bukan hanya CSV.
- `__main__.py`: bisa tetap ada untuk mode CLI (bulk awal mengisi cache), tapi
  fokus utama bergeser ke `api.py`.
- `api.py`: membuat `TkdnMysqlStore` saat startup dan menyuntikkannya ke route;
  tidak membuka koneksi global yang dipakai bersama antar-thread.
- `gateway.py`: hanya memanggil API Gateway resmi dengan token backend; tidak
  pernah dipakai oleh alur TKDN.

### Konvensi path test

Semua test modul ini berada di `modules/inaproc/api/tests/` dan diberi prefix
`modules.inaproc.api.tests`. Tabel di dokumen ini kadang menulis nama file saja
(`test_api.py`); artinya tetap `modules/inaproc/api/tests/test_api.py`. Ini mengikuti
aturan AGENTS.md: test modul disimpan di dalam modul, bukan di `tests/` root.

### Konvensi bahasa

Semua teks teknis, identifier, nama file, kontrak API, dan dokumentasi internal
ditulis dalam Bahasa Inggris. Pengecualian: teks yang terlihat oleh pengguna akhir
di UI/CLI ditulis dalam Bahasa Indonesia, dan komentar penjelasan boleh memakai
Bahasa Indonesia bila membantu menjelaskan intent.

### Urutan TDD ringkas

1. `config.py` + `db.py` + test (env MySQL, timeout, error koneksi)
2. `spt.py` + test (parsing nomor SPT)
3. `parser.py` + test (fixture HTML TKDN asli yang disanitasi)
4. `auth.py` + `login.py` + test (koneksi INAPROC headless, fake Playwright)
5. `scraper.py` + test + probe satu halaman TKDN asli
6. `cache.py` + test (fake connection factory) dan `exporter.py` + test
7. `collector.py` + test (loop, progres, cancel, retry)
8. `schemas.py` + `api.py` + test (TestClient, stub collector)
9. `gateway.py` + `gateway_store.py` + `gateway_sync.py` + test (fake HTTP dan fake DB, fixture respons API asli)
10. FE (`web/`) + Vitest store/komponen (form sesi, pencarian, tabel, ekspor, progress, link INAPROC)
11. Verifikasi real case end-to-end (MySQL, sesi INAPROC, token Gateway) + smoke test browser

### Stack keputusan (update)

- **BE: Python + FastAPI + PyMySQL** (satu bahasa dengan Playwright & cache; TDD `python -m unittest` lewat `TestClient`).
- **FE: Vue 3 + TypeScript + Bootstrap 5 + Vite + Pinia**. Bootstrap 5 untuk layout/komponen; animasi spinner memakai CSS Bootstrap/Vue transition yang menghormati `prefers-reduced-motion`.
- **Tidak memakai Emotion** di modul `inaproc` (keputusan user).
- **Sumber data TKDN**: halaman `https://penyedia.inaproc.id/products/tkdn?keyword=...` via Playwright + parser HTML. **Tanpa GraphQL.**
- **Sumber data katalog/pengadaan**: INAPROC API Gateway resmi
  `https://data.inaproc.id` (Bearer token, read-only, cursor pagination).
- Elysia/Bun tidak dipakai.

## Struktur FE (Vue 3 + TS + Pinia)

```
modules/inaproc/web/
  index.html
  package.json
  vite.config.ts
  tsconfig.json
  src/
    main.ts
    App.vue
    types.ts
    api.ts
    stores/tkdn.ts
    stores/inaprocSession.ts
    components/ConnectInaprocForm.vue
    components/SearchForm.vue
    components/CollectForm.vue
    components/ResultTable.vue
    components/PaginationBar.vue
    components/CollectProgress.vue
    components/SessionBadge.vue
  tests/
    tkdn.spec.ts
```

Alur data FE:

```
[SearchForm / CollectProgress]
        |  action Pinia
        v
[stores/tkdn.ts] --fetch--> [src/api.ts] --HTTP--> [/api/*]
        |  state: filters, rows, total, page, perPage, sort, order,
        |         session, job, chunks, activeChunk, loading, error
        v
[App.vue] -> [ConnectInaprocForm.vue] (bila sesi INAPROC belum terhubung)
          -> [SessionBadge.vue] + [SearchForm.vue] + [CollectForm.vue]
          -> [ResultTable.vue] + [PaginationBar.vue] + [CollectProgress.vue]
```

Store memegang rentang penuh pilihan user (`rangeStart`, `rangeEnd`) dan antrean
`chunks`. Action `collectRange()` memecah rentang, menjalankan chunk berurutan,
dan menghitung progres gabungan. Komponen hanya menampilkan state, tidak menyusun
request sendiri.

Tombol yang memicu request selalu `disabled` saat `loading=true` dan
menampilkan spinner. State ini ada di Pinia supaya konsisten lintas komponen.

## Spesifikasi UI (Bootstrap 5)

Dua keadaan, bukan landing page: **form koneksi INAPROC** saat sesi INAPROC belum
ada, lalu **halaman kerja** berisi input, aksi, dan tabel hasil.

### Tata letak saat sesi INAPROC belum terhubung

```
+--------------------------------------------------------------+
| TKDN INAPROC                                                  |
+--------------------------------------------------------------+
| Hubungkan akun penyedia INAPROC                               |
| Email    [____________________________]                       |
| Password [____________________________]                       |
| [Hubungkan]                                                   |
| (pesan error di sini)                                         |
+--------------------------------------------------------------+
```

### Tata letak setelah sesi INAPROC terhubung

```
+--------------------------------------------------------------+
| TKDN INAPROC   [Sesi INAPROC aktif] [Putuskan sesi INAPROC]   |
+--------------------------------------------------------------+
| Cari nomor SPT: [______________________________] [Cari Nomor] |
| (DB dulu; scraping hanya bila nomor belum ada)                |
+--------------------------------------------------------------+
| Cari: [______________]  Merek: [______]  Nilai >= [____]      |
| Urut: [Nomor v] [Naik v]   Per hal: [50 v]   [Cari]           |
+--------------------------------------------------------------+
| Nomor contoh: [11469/SJ-IND.8/E-TKDN/7/2025                   ] |
| Rentang: dari [1000] s/d [2000]  (1001 nomor, 761 diproses)   |
| [Cek Rentang] [Mulai Ambil] [Batal]     2 chunk, 25.4 menit     |
| Progres: [====------] 350/1001  found 12  empty 336  error 2  |
| Chunk 1/2: nomor 1000-1999                                    |
+--------------------------------------------------------------+
| No | Nomor SPT | Jenis | Merek | Tipe | Uraian | Std | Nilai  |
| ...                                                          |
+--------------------------------------------------------------+
| 1-50 dari 1234            [<] [1] [2] [3] [>]   [CSV] [JSON] |
+--------------------------------------------------------------+
```

### Kontrol

| Kontrol | Komponen Bootstrap | Perilaku |
| --- | --- | --- |
| Email | `input.form-control[type=email]` | wajib, validasi format |
| Password | `input.form-control[type=password]` | wajib, tidak di-prefill |
| Hubungkan | `btn btn-primary w-100` | disabled + spinner saat request |
| Nomor SPT | `input.form-control` | wajib untuk lookup, format 5 bagian divalidasi |
| Cari Nomor | `btn btn-primary` | `POST /api/lookup`; DB dulu, scraping hanya bila belum ada |
| Keyword | `input.form-control` | debounce 300 ms, kosong = tanpa filter teks |
| Merek | `input.form-control` | filter opsional |
| Nilai minimum | `input.form-control` type number | kosong = tanpa filter |
| Urut | `select.form-select` | number/brand/value/product_type |
| Arah | `select.form-select` | asc/desc |
| Per halaman | `select.form-select` | 25/50/100/200 |
| Nomor contoh | `input.form-control` | wajib, format 5 bagian divalidasi |
| Rentang dari/s/d | `input.form-control[type=number]` | bebas dipilih user, inklusif; total ditampilkan langsung |
| Cek Rentang | `btn btn-outline-secondary` | panggil `/api/collect/preview`, tampilkan total/sudah ada/chunk |
| Mulai/Batal ambil | `btn btn-primary` / `btn btn-outline-danger` | disabled saat job berjalan; Mulai menjalankan antrean chunk |
| Ekspor | `btn btn-outline-secondary` + ikon | ikut filter aktif |

Untuk hasil API Gateway, tabel produk memakai kolom tambahan `Detail INAPROC`.
Nilai kolom itu berupa link aman ke `source_url`; aplikasi tidak membuka atau
men-scrape link ini. Jika user belum login ke portal INAPROC, halaman target
yang akan meminta login secara normal.

### State wajib

| State | Tampilan |
| --- | --- |
| sesi INAPROC belum terhubung | hanya form koneksi INAPROC, tanpa tabel |
| menghubungkan INAPROC | tombol disabled + spinner |
| koneksi INAPROC gagal | `alert alert-danger` di atas tombol |
| lookup dari DB | badge `Data dari database` (tanpa spinner scraping) |
| lookup scraping | badge `Diambil dari INAPROC` + spinner selama request |
| lookup cache kosong + sesi INAPROC belum ada | pesan `401 belum_login`, arahkan ke form koneksi |
| loading cari | tombol disabled + spinner, tabel tetap tampil dengan opacity |
| cache kosong | `alert alert-info` "Belum ada data. Jalankan Ambil Data." |
| hasil kosong | `alert alert-warning` "Tidak ada hasil untuk filter ini." |
| produk Gateway | baris punya link `Detail INAPROC` bila `source_url` tersedia |
| job berjalan | progress bar + angka found/empty/error, polling 2 detik |
| rentang >1000 | tampilkan "dijalankan dalam N chunk" dari preview |
| chunk berjalan | label "chunk 2/3, nomor 2000-2500" di samping progress |
| chunk gagal | `alert alert-danger`, antrean chunk berhenti |
| job gagal | `alert alert-danger` + pesan `last_error` |
| sesi INAPROC kedaluwarsa | `alert alert-danger` + tombol kembali ke form koneksi INAPROC |
| error jaringan | `alert alert-danger` + tombol "Coba lagi" |

### Aturan tampilan

- Semua tombol yang memicu request `disabled` selama request berjalan.
- Animasi spinner memakai `spinner-border` Bootstrap; transisi opacity
  dinonaktifkan saat `prefers-reduced-motion: reduce`.
- Angka nilai TKDN tampil 2 desimal (`33.39`), `null` tampil sebagai `-`.
- Kolom nomor SPT bisa di-copy; klik nomor membuka halaman INAPROC di tab baru.
- `source_url` hasil Gateway dirender sebagai link `Detail INAPROC` dengan
  `target="_blank"` dan `rel="noopener noreferrer"`. FE tidak fetch URL itu;
  user membukanya sendiri dan harus sudah login ke portal INAPROC.
- Setiap baris punya tombol refresh (ikon) yang memanggil `POST /api/refresh`.
- Hasil `POST /api/lookup` menampilkan sumber data: `database` atau `INAPROC`.
  Sumber `database` berarti tidak ada request scraping pada aksi itu.
- Tabel responsif: `table-responsive` + `table table-sm table-hover align-middle`.
- Tanpa kartu bertumpuk, tanpa hero, tanpa ilustrasi dekoratif.

## Prinsip

- **TDD**: setiap fitur diawali test yang gagal (`python -m unittest` dari root repo), lalu implementasi minimal, lalu refactor.
- **Bahasa implementasi**: semua artefak teknis memakai Bahasa Inggris:
  nama file, class/function/variable, nama tabel/kolom, endpoint, parameter API,
  JSON key, log/error internal, nama test, dan pesan commit. Pengecualian:
  teks yang **terlihat oleh user** tetap Bahasa Indonesia, dan **komentar
  penjelasan** boleh Bahasa Indonesia supaya alasan desain mudah dibaca.
  Kode error internal tetap Inggris (misalnya `not_found`, `job_active`);
  pesan error yang ditampilkan di FE boleh Indonesia.
- **Sesi INAPROC dipakai ulang**: koneksi INAPROC cukup sekali dari FE, lalu
  `storageState.json` dipakai ulang untuk setiap halaman yang dibuka Playwright.
  Ini bukan login aplikasi.
- **Akses wajar**: delay acak + retry dengan backoff, bukan request paralel masif.
- **Tidak ada kredensial hardcode**. Password akun penyedia INAPROC hanya lewat
  form Vue -> `POST /api/login`, dipakai sekali, tidak disimpan. Sesi INAPROC
  disimpan lokal & di-gitignore.
- **DB-first**: sebelum menyentuh INAPROC, backend selalu cek MySQL. Nomor
  `found`/`empty` dibalas dari DB; INAPROC hanya disentuh untuk nomor yang belum
  ada, status `error`, collect `force`, atau refresh manual.
- **Satu job collect aktif**: mencegah dua loop paralel membebani INAPROC.
- **Data mentah tetap disimpan**: kolom `hs` dan `specification_id` ikut di-cache
  di MySQL walau belum dipakai FE.
- **Database tunggal**: MySQL, tanpa SQLite dan tanpa file cache lokal. Sesi
  INAPROC tetap berupa `storageState.json` karena itu bukan data aplikasi.
- Backend berada di `modules/inaproc/api/`, frontend di `modules/inaproc/web/`, dan test backend di `modules/inaproc/api/tests/`.
- Modul ini **tidak memakai Emotion**; styling FE pakai Bootstrap 5 (keputusan user).

## Ringkasan Eksekusi (urutan kerja nyata)

Supaya tidak bingung saat mulai, ini urutan yang akan dijalankan:

| Tahap | Pekerjaan | Hasil |
| --- | --- | --- |
| 0 | `config.py`, `db.py`, schema MySQL + test | koneksi MySQL terkonfigurasi & tabel siap |
| 1 | `spt.py` + test | parsing nomor SPT terkunci |
| 2 | `parser.py` + test dengan fixture HTML asli | tabel TKDN terbaca dari markup nyata |
| 3 | `auth.py`, `login.py` + test | sesi INAPROC headless & fallback interaktif jalan |
| 4 | `scraper.py` + test + probe halaman asli | halaman TKDN dibuka dan dirender benar |
| 5 | `cache.py`, `exporter.py` + test | upsert MySQL, query DB-first, ekspor CSV/JSON |
| 6 | `collector.py` + test | loop rentang, progres, cancel, retry |
| 7 | `schemas.py`, `api.py` + test | `/api/login` s/d `/api/refresh` |
| 8 | `gateway.py`, `gateway_store.py`, `gateway_sync.py` + test | API Gateway read-only masuk cache MySQL |
| 9 | FE Vue + Pinia + Vitest | form sesi, pencarian, tabel, ekspor, progress, link INAPROC |
| 10 | Verifikasi real case + smoke test | data nyata, MySQL nyata, sesi nyata, token nyata |

Tahap 0-8 memakai `python -m unittest` dengan fake untuk unit test, tetapi
fixture-nya diambil dari **data nyata** (HTML TKDN asli dan respons API asli yang
sudah disanitasi). Tahap 9 memakai Vitest dengan fixture respons BE asli. Tahap
10 adalah verifikasi end-to-end dengan INAPROC, MySQL, dan token sungguhan.

### Siklus TDD per tahap (real case, real data)

Setiap tahap dijalankan dengan urutan yang sama:

1. **Ambil bukti nyata**: satu halaman TKDN asli atau satu respons API asli.
   Simpan sebagai fixture setelah cookie, token, dan data pribadi dibuang.
2. **Tulis test gagal** yang mereproduksi kasus nyata itu, lalu jalankan dan
   pastikan gagal karena alasan yang benar.
3. **Implementasi minimal** sampai test hijau.
4. **Verifikasi real case**: jalankan satu kali terhadap INAPROC/MySQL nyata
   (bukan fake) untuk tahap yang memang butuh jaringan.
5. **Refactor** selama test tetap hijau, lalu lanjut tahap berikutnya.

Fixture nyata tidak boleh berisi `storageState.json`, token API, password, atau
data pribadi. Untuk Gateway, tahap 8 baru bisa diverifikasi penuh setelah token
disetujui; sebelum itu test memakai respons rekaman yang sudah disanitasi.

## Daftar File Inti yang Akan Dibuat

File pendukung (FE, test, README, `pyproject.toml`) sudah dirinci di tabel
"File tambahan untuk arsitektur FE/BE" di atas.

### 1. `modules/inaproc/__init__.py`

Menjadikan `inaproc` sebagai paket Python. Diekspos API publik:
`SptNumber`, `build_keyword`, `TkdnScraper`, `parse_rows`, `collect`.

### 2. `modules/inaproc/api/tests/__init__.py`

Menandai folder test sebagai paket (polanya mengikuti modul lain di repo).

### 3. `modules/inaproc/spt.py`

Logika pembentuk nomor & keyword, murni tanpa jaringan:

- `SptNumber(prefix, sequence, suffix)` - representasi nomor SPT.
- `build_keyword(number)` - menghasilkan string `11469/SJ-IND.8/E-TKDN/7/2025`.
- `build_url(keyword)` - URL halaman `/products/tkdn?keyword=...` untuk dibuka
  Playwright, encode dengan `urllib.parse.quote`.
- `sequence_range(start, end)` - generator angka rentang pilihan user (inklusif).

Test: `modules/inaproc/api/tests/test_spt.py` (url encoding, rentang, format nomor).

### 4. `modules/inaproc/parser.py`

Ekstraksi tabel dari HTML yang sudah dirender. Ini jalur utama pengambilan data.

- `parse_rows(html)` -> list of dict dengan 6 kolom yang dibutuhkan FE.
- Kolom wajib: jenis produk, merek, tipe, uraian, standard, nilai.
- Tabel kosong atau halaman "tidak ditemukan" -> `[]`.
- Nilai desimal diparse ke `float`; teks kosong -> `None`.
- Selector tabel disimpan sebagai konstanta yang mudah diperbarui bila markup
  INAPROC berubah.

Test: `modules/inaproc/api/tests/test_parser.py` (HTML contoh dari tugas.md, tabel kosong,
baris ganda, nilai desimal).

### 5. `modules/inaproc/scraper.py`

Navigasi browser + ekstraksi:

- `TkdnScraper(session_path, headless=True)` membuka browser Playwright dengan
  `storageState.json`.
- `fetch(keyword)` membuka `/products/tkdn?keyword=...`, menunggu tabel hasil
  render, lalu mengembalikan HTML tabel atau baris hasil parser.
- Deteksi redirect ke `/auth/signin` -> `AuthError` (sesi INAPROC kedaluwarsa).
- Deteksi halaman kosong / tidak ada hasil -> status `empty`.
- `RateLimiter`: delay acak + backoff saat halaman gagal dimuat atau INAPROC
  membalas 429/5xx.
- Timeout navigasi dan selector menghasilkan error yang bisa ditampilkan ke FE.

Test: `modules/inaproc/api/tests/test_scraper.py` dengan **fake Playwright page**
(test double), tanpa browser atau jaringan nyata.

### 6. `modules/inaproc/collector.py`

Orkestrasi:

- `collect(scraper, template, start, end, store, delay, force=False)` -> iterator hasil per nomor:
  `{number, status: found|empty|error, items: [...], error: str|None}`.
- `template` berasal dari nomor contoh pilihan user; hanya nomor urut diganti
  dengan nilai `start`..`end`.
- Simpan inkremental ke `cache.py` per nomor (bukan di akhir), supaya job bisa
  dilanjutkan walau proses berhenti.
- Nomor berstatus `found`/`empty` di `tkdn_checks` dilewati; nomor `error`
  dicoba ulang pada collect berikutnya. `force=True` memproses ulang semuanya.
- Update progres ke status job (`done`, `found`, `empty`, `error`).
- Hormati `cancel_event` agar `/api/collect/cancel` bisa menghentikan loop.

Test: `modules/inaproc/api/tests/test_collector.py` dengan scraper & parser palsu.

### 7. `modules/inaproc/config.py` dan `modules/inaproc/db.py`

Koneksi database dipisah dari store supaya mudah dites dan tidak ada kredensial
di kode:

- `InaprocDbConfig.from_env()` membaca `INAPROC_MYSQL_*`. Host/port/user/password
  boleh fallback ke `MYSQL_*` yang sudah ada di repo, tetapi **database tidak
  boleh** memakai `MYSQL_DATABASE` karena variabel itu sudah dipakai modul lain
  (mis. `telegram_data`).
- `connect_mysql(config)` membuat koneksi `pymysql` dengan `DictCursor`,
  `charset="utf8mb4"`, dan timeout pendek (`connect_timeout=5`,
  `read_timeout=10`, `write_timeout=10`) supaya API gagal cepat saat MySQL mati.
- `TkdnMysqlStore.create_schema()` idempotent: `CREATE TABLE IF NOT EXISTS`
  lalu `ALTER TABLE ... COMMENT` setiap startup, sehingga database lama ikut
  mendapat komentar tabel tanpa migrasi manual.
- `TkdnMysqlStore` menerima **connection factory**, bukan satu koneksi global.
  Setiap operasi membuka koneksi sendiri lalu menutupnya. Ini penting karena
  PyMySQL tidak thread-safe: request API dan thread collector tidak boleh
  berbagi satu koneksi.
- Saat startup, `api.py` memanggil `connect_mysql` sekali untuk memastikan DB
  hidup dan tabel dibuat. Saat shutdown, tidak ada koneksi global yang perlu
  ditutup; koneksi per operasi sudah ditutup di `finally`.
- Kegagalan koneksi (`OperationalError`/`InterfaceError`) dipetakan menjadi
  HTTP `503` dengan kode `db_unavailable`, bukan stack trace.
- Saat MySQL mati, collector menghentikan job dengan status `error` dan
  `error: "db_unavailable"`; nomor yang belum selesai tidak ditandai `found`.

Test: `modules/inaproc/api/tests/test_db.py` (config env, prefix database,
timeout, error koneksi) dan `test_cache.py` memakai fake connection factory.

### 8. `modules/inaproc/exporter.py`

- `write_csv(rows, path)` dan `write_json(rows, path)` (+ `write_jsonl` sebagai
  opsi ekspor baris, bukan penyimpanan utama).
- Kolom: `number, product_type, brand, type, description, standard, value, hs`.
- Dipakai endpoint `GET /api/export?format=csv|json` sehingga hasil ekspor
  mengikuti filter yang sedang aktif di FE.

Test: `modules/inaproc/api/tests/test_exporter.py` (headers, urutan kolom, nilai `null`, escaping koma).

### 9. `modules/inaproc/__main__.py`

CLI untuk tiga hal: koneksi INAPROC interaktif, probe satu nomor, dan collect tanpa FE.

```
python -m modules.inaproc login        # fallback interaktif (OTP/captcha)
python -m modules.inaproc probe --nomor 11469/SJ-IND.8/E-TKDN/7/2025
python -m modules.inaproc collect --nomor 11469/SJ-IND.8/E-TKDN/7/2025 --start 1000 --end 1100
```

- `login` memanggil `login.login_interaktif()`; koneksi INAPROC normal dilakukan
  dari Vue. Perintah ini hanya untuk OTP/captcha, bukan login aplikasi.
- `probe` membuka satu nomor, menunggu tabel render, lalu mencetak jumlah baris
  dan selector yang ditemukan. Dipakai untuk verifikasi DOM langsung.
- `collect` memakai nomor contoh sebagai template, mengganti nomor urut saja.
- Argumen: `--nomor`, `--start`, `--end`, `--out`, `--delay-min`, `--delay-max`,
  `--force`.
- Hasil collect disimpan ke MySQL. `--out` hanya untuk ekspor tambahan
  (`modules/inaproc/output/hasil.csv` + `hasil.json`), bukan sumber data utama.

Test: `modules/inaproc/api/tests/test_cli.py` (parse argumen + dispatch dengan mock).

### 10. `modules/inaproc/login.py`

Fallback interaktif saja (dipakai bila INAPROC minta OTP/captcha). Buka
`https://penyedia.inaproc.id/auth/signin?callbackUrl=/products/tkdn` dengan
headless=False **di mesin yang punya layar**, tunggu user menyelesaikan login
penyedia INAPROC secara manual, tunggu navigasi ke `/products/tkdn`, lalu
`context.storageState(path=...)`.

Catatan operasional: fallback ini tidak bisa dipakai bila BE berjalan di server
tanpa display. Untuk sekarang aplikasi ditargetkan lokal, jadi ini aman.

Koneksi INAPROC normal dilakukan dari Vue lewat `POST /api/login`, tidak lewat file ini.

Test: `modules/inaproc/api/tests/test_login.py` dengan Playwright fake (tanpa browser sungguhan).

### 11. `modules/inaproc/auth.py`  (inti koneksi INAPROC headless)

Koneksi INAPROC normal: `connect_inaproc(email, password, session_path)` membuka Playwright
headless, isi form signin INAPROC, submit, tunggu redirect ke `/products/tkdn`,
simpan `storageState.json`, kembalikan ringkasan. Fungsi ini tidak membuat akun
atau sesi aplikasi.


- `connect_inaproc(email, password, session_path)` -> jalankan Playwright headless, simpan state.
- `muat_storage_state(path)` -> dict (validasi struktur cookies/origins).
- `validasi_sesi(state)` -> memastikan ada cookie/localStorage sesi INAPROC yang
  bisa dipakai Playwright; tidak membaca nilai sesi.
- `AuthError` untuk state hilang/state tidak valid/kredensial salah.

Test: `modules/inaproc/api/tests/test_auth.py` memakai state dummy tanpa nilai sesi asli.

### 12. `modules/inaproc/documents/contoh_session.json.example`

Contoh struktur `storageState.json` **tanpa nilai asli** (cookie dummy), sebagai
referensi cara menyiapkan sesi. File aslinya di-gitignore.

### 13. `.gitignore` (update)

Tambahkan pola untuk menyembunyikan file sesi dan hasil ekspor:

```
modules/inaproc/*.session.json
modules/inaproc/storageState.json
modules/inaproc/output/
```

Catatan: root `.gitignore` saat ini masih punya pola lama
`modules/inaproc/data/`; pola itu dihapus saat implementasi karena tidak ada
lagi file database lokal (MySQL).

### 14. CLI tambahan untuk API Gateway

`python -m modules.inaproc gateway-status` hanya menampilkan ringkasan aman:
`enabled`, ada/tidaknya token, base URL, scope yang aktif, dan run terakhir.
Perintah ini tidak pernah mencetak token atau cookie. CLI tambahan untuk sync
hanya dipakai sebagai maintenance internal setelah route FE tersedia.

## Format Nomor SPT

Nomor SPT punya 5 bagian:

```
11469 / SJ-IND.8 / E-TKDN / 7 / 2025
  |        |          |      |     |
  |        |          |      |     +-- tahun
  |        |          |      +-------- bulan terbit
  |        |          +--------------- kode jenis dokumen
  |        +-------------------------- kode unit/instansi
  +----------------------------------- nomor urut
```

### Yang boleh di-loop

Hanya **nomor urut**. Bagian lain (`SJ-IND.8`, `E-TKDN`, bulan, tahun) harus
dipertahankan apa adanya, karena nomor urut saja yang berurutan.

Rentang nomor urut **dipilih user** di FE (field `dari` dan `s/d`). Tidak ada
default hardcode: user mengisi nomor contoh, lalu menentukan sendiri batas
bawah dan atas. BE hanya memvalidasi dan menjalankan pilihan itu.

### Risiko bulan dan tahun

`7/2025` adalah bulan terbit. Kalau rentang nomor melewati pergantian bulan atau
tahun, nomor urut yang sama bisa berada di dokumen berbeda. Karena itu:

- Form collect punya field **bulan** dan **tahun** (default dari nomor contoh
  `7` dan `2025`), bukan hardcode.
- Nomor contoh diisi sekali oleh user; script membaca bagian 1, 2, 3, 4, 5 dari
  nomor itu, lalu hanya mengganti bagian 1.
- Ada opsi **"coba bulan sebelumnya/berikutnya"** yang dicoba hanya bila hasil
  kosong berurutan (misal 20 nomor kosong berturut-turut), dengan jumlah percobaan
  maksimum 2 bulan. Ini opsional dan default mati.

### Representasi

```python
@dataclass(frozen=True)
class SptNumber:
    sequence: int      # 11469
    unit: str          # "SJ-IND.8"
    doc_type: str      # "E-TKDN"
    month: int         # 7
    year: int          # 2025

    def __str__(self) -> str: ...        # "11469/SJ-IND.8/E-TKDN/7/2025"
    @classmethod
    def parse(cls, teks: str) -> "SptNumber": ...   # validasi 5 bagian
    def with_sequence(self, n: int) -> "SptNumber": ...
```

`parse` menolak format salah dengan pesan jelas (jumlah bagian bukan 5, sequence
bukan angka, bulan di luar 1-12, tahun bukan 4 digit). `with_sequence(n)`
mengembalikan nomor baru dengan sequence diganti dan bagian lain identik.

## Koneksi Sesi INAPROC (dari Vue)

Endpoint teknisnya tetap bernama `POST /api/login` agar kontrak API tidak berubah.
Nama itu tidak berarti aplikasi punya login pengguna; ia hanya membuka sesi
penyedia INAPROC di backend.

Aplikasi ini **tidak memiliki sistem akun, registrasi, atau login pengguna
sendiri**. Form di FE hanya meneruskan kredensial **akun penyedia INAPROC** ke
backend. Python hanya backend. Playwright berjalan di server (headless) untuk
mengisi form signin INAPROC, lalu state sesi INAPROC disimpan dan dipakai ulang.

### Alur

```
[ConnectInaprocForm.vue]  email + password akun penyedia INAPROC
        |  POST /api/login  { "email": "...", "password": "..." }
        v
[api.py] -> [auth.connect_inaproc(email, password)]
        |  Playwright headless: buka /auth/signin, isi form, submit
        |  tunggu redirect ke /products/tkdn
        |  context.storageState(path="modules/inaproc/storageState.json")
        v
{ "ok": true, "session": { "configured": true, "valid": true } }
        -> FE menampilkan halaman pencarian (sesi INAPROC terhubung)
```

### Kontrak koneksi INAPROC

`POST /api/login`

```json
{ "email": "user@contoh.id", "password": "..." }
```

- Sukses `200`: `{ "ok": true, "session": { "configured": true, "valid": true } }`
- Kredensial salah `401`: `{ "error": "kredensial_salah", "message": "..." }`
- Butuh OTP/captcha `409`: `{ "error": "butuh_interaksi", "message": "..." }`
  (FE menampilkan instruksi menyelesaikan koneksi INAPROC lewat browser; fallback
  interaktif tersedia untuk OTP)

`POST /api/logout` menghapus `storageState.json` dan mengosongkan status sesi
INAPROC. Ini tidak menghapus akun apa pun, hanya memutus sesi INAPROC di backend.

### File dan fungsi

| File | Isi |
| --- | --- |
| `modules/inaproc/api/auth.py` | `connect_inaproc(email, password, session_path)` -> dict state |
| `modules/inaproc/api/auth.py` | `muat_storage_state(path)`, `validasi_sesi(state)` |
| `modules/inaproc/api/login.py` | Hanya fallback koneksi INAPROC interaktif (OTP/captcha), headless=False |
| `modules/inaproc/web/src/stores/inaprocSession.ts` | Pinia: `status`, `connect()`, `disconnect()`, `checkSession()` |

### Aturan

- Password **tidak pernah** disimpan, tidak di-log, tidak masuk cache. Hanya dipakai
  sekali di dalam request lalu dibuang.
- `storageState.json` wajib di-gitignore. Isi state sesi tidak pernah dikirim ke FE.
- FE hanya tahu `configured`/`valid`, bukan nilai cookie/localStorage.
- Kalau sesi INAPROC kedaluwarsa (halaman di-redirect ke signin), FE menampilkan
  form koneksi INAPROC lagi.
- Koneksi INAPROC cukup sekali; setelah itu semua request memakai state tersimpan.
  Tidak ada login aplikasi yang perlu diulang.

### Penanganan error

| Kondisi | Perilaku |
| --- | --- |
| Form kosong | FE validasi, tombol disabled |
| Kredensial INAPROC salah | `401`, pesan di form, tidak menyimpan state |
| Butuh OTP/captcha | `409`, FE arahkan ke fallback interaktif |
| Playwright timeout | `504`, pesan "INAPROC tidak merespons" |
| `storageState.json` hilang | `configured: false`, FE tampilkan form koneksi INAPROC |
| Redirect ke `/auth/signin` | `AuthError`, FE tampilkan form koneksi INAPROC |

## Kontrak API

Semua endpoint di bawah prefix `/api`. Error selalu berbentuk
`{"error": "<kode>", "message": "<penjelasan>"}`.
Kode yang dipakai: `belum_login` (401), `kredensial_salah` (401),
`butuh_interaksi` (409), `job_aktif` (409), `request_tidak_valid` (422),
`nomor_tidak_valid` (422), `rentang_terlalu_besar` (422), `db_unavailable` (503),
`upstream_timeout` (504), dan `upstream_error` (502).
Status collect memakai `done = found + empty + errors`; `skipped` dihitung
terpisah. Job state juga membawa `job_id`, `processed`, `current_number`,
`started_at`, dan `finished_at`.

### Ringkasan endpoint

| Method | Path | Fungsi |
| --- | --- | --- |
| `POST` | `/api/login` | Buka sesi INAPROC via Playwright headless, simpan `storageState.json` (bukan login aplikasi) |
| `POST` | `/api/logout` | Hapus sesi tersimpan |
| `GET` | `/api/session` | Status sesi INAPROC tanpa membocorkan isi state |
| `GET` | `/api/search` | Cari di database MySQL (filter, sort, pagination), tanpa scraping |
| `POST` | `/api/lookup` | Cari **satu nomor SPT**: DB dulu, scraping hanya bila belum ada/`error` |
| `POST` | `/api/collect/preview` | Hitung dampak rentang sebelum dijalankan |
| `POST` | `/api/collect` | Mulai job collect untuk satu rentang (maks 1000 nomor) |
| `GET` | `/api/status` | Progres job aktif/terakhir |
| `POST` | `/api/collect/cancel` | Minta job aktif berhenti |
| `GET` | `/api/export` | Unduh hasil filter aktif sebagai CSV atau JSON |
| `POST` | `/api/refresh` | Ambil ulang satu nomor (hapus cache nomor itu) |

Catatan umum:

- `POST /api/collect` menerima **satu rentang**, bukan daftar nomor lepas.
  Rentang dipilih user lewat `start`/`end` (inklusif) dengan `nomor` sebagai
  template.
- Backend tidak pernah memilih rentang sendiri; tidak ada default 1..N.
- `/api/collect` memerlukan sesi INAPROC valid (`401 belum_login`).
- `/api/collect/preview` tidak butuh sesi; hanya menghitung dari cache.
- `/api/search` dan `/api/export` murni membaca MySQL tanpa sesi.
- `/api/lookup` hanya butuh sesi INAPROC **bila** nomor belum final atau data
  tidak konsisten di DB.
- Semua endpoint yang menyentuh data mengembalikan `503 db_unavailable` bila
  MySQL tidak bisa dihubungi; detail koneksi tidak dibocorkan ke FE.
- `/api/status` dan `/api/collect/cancel` hanya membaca/mengubah job di memori.
- `/api/lookup` hanya butuh sesi INAPROC bila status DB `error`, tidak
  ditemukan, atau `found` tanpa baris `tkdn_rows` (data tidak konsisten).

### `POST /api/lookup`

Endpoint untuk satu nomor SPT. Ini jalur utama konsep DB-first: nomor yang sudah
pernah di-scrape tidak di-scrape lagi.

Body:

```json
{ "nomor": "11469/SJ-IND.8/E-TKDN/7/2025" }
```

Alur:

1. Validasi format nomor (5 bagian, bulan/tahun valid).
2. `SELECT status FROM tkdn_checks WHERE number = ?`.
3. `found` -> `SELECT` baris dari `tkdn_rows`:
   - ada baris -> balas `source: "db"`.
   - tidak ada baris -> UPSERT status `error` dengan
     `error_msg='data_tidak_konsisten'`, lalu lanjut ke scraping.
4. `empty` -> hapus baris `tkdn_rows` yatim bila ada, balas `source: "db"`,
   `items: []`.
5. `error`, tidak ada, atau `found` tidak konsisten -> cek sesi INAPROC,
   scraping, lalu UPSERT.

Response `200`:

```json
{
  "number": "11469/SJ-IND.8/E-TKDN/7/2025",
  "status": "found",
  "source": "db",
  "items": [
    {
      "product_type": "Monitor",
      "brand": "acer",
      "type": "V",
      "description": "23.8 Inchi",
      "standard": null,
      "value": 33.39,
      "hs": null
    }
  ]
}
```

| Kondisi | Respons |
| --- | --- |
| Nomor `found` di DB dan ada baris `tkdn_rows` | `200`, `source: "db"`, item dari MySQL |
| Nomor `empty` di DB | `200`, `source: "db"`, `items: []` |
| Nomor belum ada, scraping sukses | `200`, `source: "scrape"` |
| Nomor `error`, scraping sukses | `200`, `source: "scrape"`, status baru |
| Nomor `found` tapi tanpa baris `tkdn_rows` | dianggap tidak konsisten, scraping ulang |
| Nomor belum ada + sesi INAPROC kosong | `401 belum_login` |
| Format nomor salah | `422 nomor_tidak_valid` |
| MySQL mati | `503 db_unavailable` |

Catatan:

- Request ke INAPROC hanya terjadi pada cabang `error`/belum ada.
- Nomor `found` tanpa baris `tkdn_rows` juga masuk cabang scraping, karena
  status saja tidak cukup untuk menjawab data.
- Kalau dua user melakukan lookup nomor yang sama bersamaan, keduanya bisa
  sama-sama scraping; hasil akhir tetap aman karena UPSERT idempotent. Lock
  per nomor di luar lingkup versi pertama.
- `source` dipakai FE untuk menampilkan badge "database" vs "INAPROC".

### `GET /api/search`

Query params: `q` (opsional, default kosong = semua baris), `brand` (opsional),
`min_value` (opsional, float), `page` (default 1), `per_page` (default 50, maks
200), `sort` (`number|brand|value|product_type`, default `number`), `order`
(`asc|desc`).

```json
{
  "items": [
    {
      "number": "11469/SJ-IND.8/E-TKDN/7/2025",
      "product_type": "Monitor",
      "brand": "acer",
      "type": "V",
      "description": "23.8 Inchi",
      "standard": null,
      "value": 33.39,
      "hs": null
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

Pencarian hanya ke MySQL (tidak memanggil INAPROC). `q` mencocokkan semua
kolom teks (nomor, jenis, merek, tipe, uraian, standard) secara case-insensitive.
Tanpa `q`, endpoint tetap mengembalikan baris cache yang cocok dengan filter lain.

Kalau `q` berisi nomor SPT yang belum ada di DB, endpoint ini **tidak**
men-scrape. FE harus memakai `POST /api/lookup` (satu nomor) atau
`POST /api/collect` (rentang). Dengan begitu, pencarian teks selalu murah dan
scraping selalu eksplisit.

### `POST /api/collect/preview`

Menghitung dampak rentang sebelum dijalankan, supaya user tahu berapa nomor yang
akan diproses dan berapa yang dilewati karena sudah ada di cache.

Contoh panggilan:

```json
{
  template: 11469/SJ-IND.8/E-TKDN/7/2025,
  start: 1000,
  end: 2000
}
```

Endpoint ini **tidak** memanggil INAPROC dan tidak memerlukan sesi INAPROC; ia
hanya membaca `tkdn_checks` untuk menghitung `sudah_ada`.

Body memakai `template` (nomor contoh lengkap), `start`, dan `end`.
`delay_min` dan `delay_max` bisa dikirim di body juga; bila dikosongkan,
server memakai default `1.0` dan `3.0`.

Aturan:

- `start` dan `end` adalah nomor urut inklusif, bebas dipilih user.
- `total` = `end - start + 1`.
- `chunks` = `ceil(total / 1000)`; preview boleh menghitung rentang berapa pun
  tanpa menjalankannya.
- `sudah_ada` dihitung dari `tkdn_checks` berstatus `found` atau `empty` saja
  (hasil final). Nomor berstatus `error` tidak dihitung, karena akan dicoba ulang.
- `estimasi_menit` memakai delay tengah (`(delay_min + delay_max) / 2`) kali
  `akan_diproses`, dibagi 60. Delay divalidasi sama seperti `POST /api/collect`.
  Contoh: 761 x 2 detik / 60 = 25.4 menit.
- Endpoint ini tidak memerlukan job dan tidak mengubah cache.

```json
{
  "template": "11469/SJ-IND.8/E-TKDN/7/2025",
  "start": 1000,
  "end": 2000,
  "total": 1001,
  "sudah_ada": 240,
  "akan_diproses": 761,
  "estimasi_menit": 25.4,
  "chunks": 2
}
```

`sudah_ada` (240) hanya menghitung nomor berstatus `found`/`empty`. Nomor yang
pernah `error` ikut dihitung di `akan_diproses` karena akan dicoba ulang.

### `POST /api/collect`

Rentang nomor **dipilih user di FE**, tidak hardcode. Body:

```json
{
  "nomor": "11469/SJ-IND.8/E-TKDN/7/2025",
  "start": 1000,
  "end": 1999,
  "delay_min": 1.0,
  "delay_max": 3.0,
  "force": false
}
```

- `nomor` adalah template; hanya bagian nomor urut yang diganti (`start`..`end`).
- `start` dan `end` bebas dipilih user, minimal 1 nomor.
- `force: true` memproses ulang nomor yang sudah ada di cache.
- Tanpa `force`, setiap nomor dicek ke `tkdn_checks` lebih dulu: status
  `found`/`empty` dilewati tanpa request INAPROC; hanya nomor yang belum ada
  atau `error` yang di-scrape.
- Satu request hanya boleh mencakup maksimal 1000 nomor. Rentang lebih besar
  dipecah oleh FE, bukan oleh backend (lihat bagian chunk di bawah).
- `delay_min`/`delay_max` opsional; bila kosong pakai default server
  (`1.0`/`3.0`) dan divalidasi `0 < delay_min <= delay_max <= 30`.

Validasi:

| Kondisi | Respons |
| --- | --- |
| `start > end` | `422`, `error: "rentang_tidak_valid"` |
| `nomor` bukan format 5 bagian | `422`, `error: "nomor_tidak_valid"` |
| `end - start + 1 > 1000` | `422`, `error: "rentang_terlalu_besar"` |
| `delay_min <= 0` atau `delay_max < delay_min` | `422`, `error: "delay_tidak_valid"` |
| Job lain sedang berjalan | `409`, sertakan `job_id` aktif |
| Sesi INAPROC belum terhubung | `401`, `error: "belum_login"` |

Response `202`:

```json
{
  "job_id": "20261120-101500",
  "total": 1000,
  "sudah_ada": 240,
  "akan_diproses": 760,
  "status": "running"
}
```

Contoh di atas mencakup tepat 1000 nomor (`1000..1999`). Response collect tidak
memuat `chunks`: jumlah chunk adalah urusan FE, dan satu request selalu satu chunk.

### Chunking rentang besar (tanggung jawab FE)

Bila user memilih lebih dari 1000 nomor, FE memecah rentang menjadi potongan
inklusif maksimal 1000 nomor, lalu menjalankannya **berurutan**:

```
rentang user 1000..2500 (1501 nomor)
  chunk 1: 1000..1999 (1000 nomor) -> POST /api/collect
  chunk 2: 2000..2500 ( 501 nomor) -> POST /api/collect setelah chunk 1 selesai
```

- FE menunggu `GET /api/status` berstatus `done` sebelum mengirim chunk
  berikutnya, karena backend hanya mengizinkan satu job aktif.
- Progres gabungan dihitung FE: jumlah `done` semua chunk selesai + `done`
  chunk aktif, dibagi total nomor seluruh rentang.
- Bila satu chunk gagal, FE berhenti dan menampilkan chunk mana yang gagal;
  chunk berikutnya tidak dikirim otomatis.
- Tombol Batal membatalkan chunk yang sedang berjalan dan menghentikan antrean
  chunk berikutnya.
- Backend tetap menolak satu request >1000 nomor (`422 rentang_terlalu_besar`)
  supaya tidak ada job raksasa yang sulit dibatalkan.

Hanya satu job aktif pada satu waktu.

### `GET /api/status`

Status job aktif, atau job terakhir bila sedang tidak ada job. Saat belum pernah
ada job, balas `{"status": "idle"}` tanpa field lain.

Contoh panggilan: `GET /api/status` (tanpa parameter).

```json
{
  "job_id": "20261120-101500",
  "status": "running",
  "nomor": "11469/SJ-IND.8/E-TKDN/7/2025",
  "start": 1000,
  "end": 1999,
  "total": 1000,
  "done": 350,
  "found": 12,
  "empty": 336,
  "error": 2,
  "current_number": "11469/SJ-IND.8/E-TKDN/7/2025",
  "started_at": "2026-11-20T10:15:00+08:00",
  "finished_at": null,
  "last_error": null
}
```

`nomor`/`start`/`end` mengembalikan rentang **chunk yang sedang berjalan**, bukan
seluruh rentang pilihan user. FE yang memegang rentang penuh dan menyusun progres
gabungan antar chunk.

`status`: `idle|running|done|failed|cancelled`.

Invariant: `done = found + empty + error` setelah job selesai.

### `POST /api/login`

Body `{"email": "...", "password": "..."}`. Sukses `200`:
`{"ok": true, "session": {"configured": true, "valid": true}}`.
Gagal `401` kredensial salah, `409` butuh OTP/captcha, `504` timeout INAPROC.

Endpoint ini membuka **sesi penyedia INAPROC**, bukan sesi aplikasi. Password
akun INAPROC tidak disimpan dan tidak di-log.

### `POST /api/logout`

Hapus `storageState.json`, balas `{"ok": true}`. Dipakai tombol "Putuskan sesi
INAPROC" di FE. Tidak ada akun aplikasi yang dihapus.

### `GET /api/session`

Cek status sesi INAPROC tanpa membocorkan isi `storageState.json`.

```json
{ "configured": true, "valid": true, "checked_at": "2026-11-20T10:20:00+08:00" }
```

- `configured`: file `storageState.json` ada dan berisi cookie/localStorage sesi
  INAPROC yang valid.
- `valid`: hasil cek ringan dengan membuka halaman TKDN (boleh `null` bila belum
  pernah dicek).
- FE memakai endpoint ini untuk menampilkan badge "Sesi INAPROC aktif / belum
  terhubung". Status ini tidak berkaitan dengan akun aplikasi.

### `POST /api/collect/cancel`

Menghentikan job aktif setelah nomor yang sedang diproses selesai. Response
`{"status": "cancelling"}` atau `409` bila tidak ada job.

### `GET /api/export`

Query params: `format` (`csv|json`), plus filter yang sama dengan `/api/search`.
Response berupa file unduhan (`text/csv` atau `application/json`) dengan header
`Content-Disposition: attachment`.

Contoh: `GET /api/export?format=csv&q=acer&brand=acer&min_value=30`.

- Export selalu mengekspor **seluruh baris yang cocok dengan filter**, bukan hanya
  halaman yang sedang tampil. `page`/`per_page` diabaikan bila dikirim.
- `format` selain `csv|json` -> `422`, `error: "format_tidak_valid"`.
- `sort`/`order` tetap dihormati agar urutan file sama dengan tabel.
- Nama file: `tkdn-YYYYMMDD-HHMMSS.csv` atau `.json` (zona waktu server).

### `POST /api/refresh`

Memaksa ambil ulang **satu nomor** yang sudah ada di cache (tombol refresh per
baris). Body `{"nomor": "11469/SJ-IND.8/E-TKDN/7/2025"}`.

- Menghapus baris nomor itu dari `tkdn_rows` dan `tkdn_checks`.
- Data lama hanya dihapus setelah fetch INAPROC sukses; bila sesi kedaluwarsa,
  cache tetap dipertahankan dan API mengembalikan `401`.
- Mengambil ulang dengan membuka halaman TKDN memakai sesi INAPROC aktif (bukan
  job collect).
- Sukses `200`: `{"number": "...", "status": "found|empty", "items": 3}`.
- `409 job_aktif` bila job collect sedang berjalan (hindari tulis bersamaan).
- `404 nomor_tidak_ditemukan` bila nomor belum ada di cache; pakai collect, bukan refresh.
- `401 belum_login`, `422 nomor_tidak_valid`, `502 upstream_error`.

Tanpa endpoint ini, keputusan "refresh manual per nomor" tidak punya jalur API.

### Ringkasan kode error

| Kode | HTTP | Kapan |
| --- | --- | --- |
| `kredensial_salah` | 401 | Kredensial penyedia INAPROC ditolak |
| `belum_login` | 401 | State sesi INAPROC tidak ada/kedaluwarsa saat collect |
| `butuh_interaksi` | 409 | INAPROC minta OTP/captcha |
| `job_aktif` | 409 | Sudah ada job collect berjalan |
| `tidak_ada_job` | 409 | Cancel saat tidak ada job |
| `rentang_tidak_valid` | 422 | `start > end` |
| `rentang_terlalu_besar` | 422 | Satu request >1000 nomor |
| `nomor_tidak_valid` | 422 | Template bukan 5 bagian valid |
| `delay_tidak_valid` | 422 | Delay di luar batas |
| `format_tidak_valid` | 422 | Export selain csv/json |
| `nomor_tidak_ditemukan` | 404 | Refresh nomor tidak ada di cache |
| `db_unavailable` | 503 | MySQL tidak bisa dihubungi / koneksi terputus |
| `upstream_timeout` | 504 | INAPROC tidak merespons |
| `upstream_error` | 502 | Halaman INAPROC gagal dimuat atau markup tak dikenali |

## Skema Database MySQL

Cache utama disimpan di MySQL, mengikuti pola modul lain di repo ini:
`pymysql` + `DictCursor`, class `TkdnMysqlStore`, schema dibuat saat init.

Konfigurasi lewat `.env`. Variabel khusus modul ini memakai prefix `INAPROC_`
supaya tidak bertabrakan dengan database modul lain:

```
INAPROC_MYSQL_HOST=127.0.0.1
INAPROC_MYSQL_PORT=3306
INAPROC_MYSQL_USER=root
INAPROC_MYSQL_PASSWORD=
INAPROC_MYSQL_DATABASE=inaproc
```

`INAPROC_MYSQL_HOST`/`PORT`/`USER`/`PASSWORD` boleh fallback ke `MYSQL_*` yang
sudah ada. `INAPROC_MYSQL_DATABASE` **wajib** diisi dan tidak fallback ke
`MYSQL_DATABASE`, karena nilai itu milik modul lain.

Tidak ada file database di repo. Database dan user dibuat manual sekali
(mis. lewat Laragon atau `mysql -e`), lalu store membuat tabelnya sendiri.
Kolom komentar tabel wajib ada supaya tujuan tiap tabel terbaca dari schema:

```sql
CREATE TABLE IF NOT EXISTS tkdn_rows (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    number           VARCHAR(128) NOT NULL,
    specification_id VARCHAR(128) NULL,
    product_type     VARCHAR(255) NULL,
    brand            VARCHAR(255) NULL,
    type             VARCHAR(255) NULL,
    description      VARCHAR(512) NULL,
    standard         VARCHAR(255) NULL,
    value            DOUBLE NULL,
    hs               VARCHAR(64) NULL,
    fetched_at       DATETIME NOT NULL,
    row_hash         CHAR(64) NOT NULL,
    UNIQUE KEY uq_tkdn_row (row_hash),
    KEY idx_tkdn_brand (brand),
    KEY idx_tkdn_number (number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Baris hasil scraping TKDN per nomor SPT; cache utama pencarian';

CREATE TABLE IF NOT EXISTS tkdn_checks (
    number     VARCHAR(128) PRIMARY KEY,
    status     VARCHAR(16) NOT NULL,   -- found | empty | error
    checked_at DATETIME NOT NULL,
    error_msg  TEXT NULL,
    KEY idx_tkdn_checks_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='Status pengecekan per nomor SPT (found/empty/error) untuk skip collect';
```

Catatan penting MySQL:

- `row_hash` = SHA-256 dari `number|specification_id|brand|type|description`
  yang sudah dinormalisasi (`None` -> `''`). Ini menghindari batas panjang index
  MySQL (3072 byte) yang akan terlampaui bila lima kolom teks dijadikan satu
  unique key utf8mb4.
- Upsert memakai `INSERT ... ON DUPLICATE KEY UPDATE` dan memperbarui
  `value`, `standard`, `hs`, serta `fetched_at` dari `VALUES(...)`. `row_hash`
  ikut dikirim setiap insert, jadi tidak perlu kolom generated. Dengan begitu
  refresh/force collect bisa memperbaiki nilai tanpa membuat baris duplikat.
- `LIKE` untuk pencarian teks memakai `COLLATE utf8mb4_unicode_ci` agar
  case-insensitive tanpa bergantung pada collation server.
- Sort dan pagination memakai `ORDER BY` + `LIMIT %s OFFSET %s`; kolom sort
  dipilih dari whitelist di kode, tidak pernah dari input mentah.
- Store menerima **connection factory** di constructor, jadi test memakai fake
  factory tanpa MySQL asli.
- `CREATE TABLE IF NOT EXISTS` tidak memperbarui komentar tabel yang sudah ada.
  Saat implementasi, jalankan `ALTER TABLE ... COMMENT='...'` yang idempotent
  setelah `CREATE TABLE` (atau drop tabel dev lama) supaya komentar benar-benar
  terpasang pada database yang sudah pernah dibuat.

`tkdn_checks` menyimpan status per nomor supaya nomor kosong tidak di-request
ulang saat collect diulang. Baris `error` tetap disimpan untuk diagnosa, tetapi
collect berikutnya mencoba ulang nomor itu. Refresh manual menghapus baris nomor
tersebut dari kedua tabel.

## Event Tulis ke Database (Upsert)

Bagian ini mengunci **apa yang ditulis ke MySQL lokal** dan **event apa yang
memicunya** untuk jalur TKDN. Tujuannya hanya cache: hasil baca dari INAPROC
disimpan supaya pencarian berikutnya cepat. Jalur API Gateway punya tabel dan
event sendiri di bagian "Event upsert API resmi"; kedua jalur tidak saling
menulis tabel dan tidak menulis balik ke INAPROC.

### Rencana singkat penulisan DB

| Data | Tempat | Kapan ditulis |
| --- | --- | --- |
| Baris hasil TKDN per nomor SPT | `tkdn_rows` | Hanya saat scraping menghasilkan data (`found`), setelah nomor diproses |
| Status pengecekan nomor SPT | `tkdn_checks` | Setiap nomor selesai: `found`, `empty`, atau `error` |
| Schema dan komentar tabel | DDL MySQL | Saat startup API, idempotent |

Aturan pentingnya:

- `POST /api/lookup` dan `POST /api/collect` selalu baca status/nomor dari
  MySQL dulu. Playwright hanya dipanggil untuk nomor baru, `error`, atau
  `found` yang kehilangan baris datanya.
- Penulisan data selalu commit per nomor, bukan setelah seluruh rentang
  selesai, supaya job bisa dilanjutkan bila berhenti di tengah.
- `tkdn_rows` memakai `row_hash` unik; upsert nomor sama tidak boleh
  menggandakan baris.
- `force=true` dan refresh manual menghapus baris lama milik nomor itu dulu,
  lalu scrape ulang, supaya baris yang sudah hilang di INAPROC tidak tertinggal
  di DB.

### Peran tiap tabel

| Tabel | Isi | Kunci unik | Kapan baris hidup |
| --- | --- | --- | --- |
| `tkdn_rows` | Baris hasil TKDN: nomor SPT, jenis produk, merek, tipe, uraian, standard, nilai, hs | `row_hash` | Hanya saat nomor berstatus `found` |
| `tkdn_checks` | Satu baris per nomor SPT: status + waktu cek + pesan error | `number` (PK) | Selalu, selama nomor pernah diproses |

### Matriks event tulis

| # | Event | Dipicu oleh | Operasi DB | Tabel |
| --- | --- | --- | --- | --- |
| 1 | Startup API | `TkdnMysqlStore.create_schema()` | `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ... COMMENT` | schema |
| 2 | Nomor selesai, ada data (`found`) | Parser mengembalikan >=1 baris | UPSERT baris (batch per nomor) + UPSERT status `found` | `tkdn_rows` + `tkdn_checks` |
| 3 | Nomor selesai, kosong (`empty`) | Parser mengembalikan 0 baris | DELETE baris nomor itu bila ada + UPSERT status `empty` | `tkdn_rows` + `tkdn_checks` |
| 4 | Nomor gagal diproses (`error`) | Timeout, 429 habis retry, markup tak dikenali | UPSERT status `error` + `error_msg` | `tkdn_checks` |
| 5 | Nomor `error` dicoba ulang | Collect berikutnya (error tidak di-skip) | Sama seperti event 2/3/4; `error_msg` jadi `NULL` bila berhasil | kedua tabel |
| 6 | Data tidak konsisten ditemukan | `found` tanpa baris `tkdn_rows`; `empty` dengan baris yatim | `found`: reset ke `error` lalu scrape ulang; `empty`: hapus baris yatim dan tetap jawab DB | kedua tabel |
| 7 | `force=true` | User minta proses ulang | Sama seperti event 2/3; nilai baris `found` ikut diperbarui | kedua tabel |
| 8 | Refresh satu nomor | `POST /api/refresh` | DELETE nomor dari kedua tabel -> scrape -> UPSERT hasil baru | kedua tabel |
| 9 | Sesi INAPROC kedaluwarsa saat collect | Redirect ke `/auth/signin` | UPSERT nomor aktif `error` (`error_msg=belum_login`), job stop | `tkdn_checks` |
| 10 | MySQL mati saat menulis | `OperationalError`/`InterfaceError` | `rollback()`, tidak ada commit, job stop `db_unavailable` | - |

Alur ringkas per nomor:

```
collect nomor N:
  belum ada/error -> scrape
    found -> UPSERT tkdn_rows (semua baris) + UPSERT tkdn_checks status=found
    empty -> DELETE tkdn_rows WHERE number=N  + UPSERT tkdn_checks status=empty
    error -> UPSERT tkdn_checks status=error (tkdn_rows tidak diubah)

sebelum memproses N:
  checks=found + rows kosong  -> UPSERT status error data_tidak_konsisten -> scrape
  checks=empty + rows ada     -> DELETE rows yatim, status tetap empty -> jawab DB

refresh nomor N:
  DELETE tkdn_rows WHERE number=N + DELETE tkdn_checks WHERE number=N  (1 transaksi)
  -> scrape -> UPSERT sesuai hasil found/empty/error
```

### Detail UPSERT `tkdn_rows`

Dijalankan per nomor, sekali per baris hasil parse. Idempotent: `row_hash` yang
sama tidak pernah menambah baris baru.

```sql
INSERT INTO tkdn_rows
    (number, specification_id, product_type, brand, type, description,
     standard, value, hs, fetched_at, row_hash)
VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    product_type = VALUES(product_type),
    value        = VALUES(value),
    standard     = VALUES(standard),
    hs           = VALUES(hs),
    fetched_at   = VALUES(fetched_at)
```

- `number`, `specification_id`, `brand`, `type`, `description` tidak ikut
  di-update karena kelimanya pembentuk `row_hash`; kalau salah satu berubah,
  hash-nya beda dan baris baru memang wajar dibuat.
- `product_type` ikut di-update karena tidak ikut masuk `row_hash`.
- `fetched_at` diisi waktu server saat baris ditulis; dipakai untuk
  melacak kapan baris terakhir diperbarui.
- `row_hash` = SHA-256 dari `number|specification_id|brand|type|description`
  dengan `None` dinormalisasi ke `''`.
- Tidak ada baris `tkdn_rows` untuk nomor berstatus `empty` atau `error`.

### Detail UPSERT `tkdn_checks`

Dijalankan setiap sebuah nomor selesai diproses, apa pun hasilnya.

```sql
INSERT INTO tkdn_checks (number, status, checked_at, error_msg)
VALUES (%s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    status     = VALUES(status),
    checked_at = VALUES(checked_at),
    error_msg  = VALUES(error_msg)
```

- `status` hanya `found` | `empty` | `error`.
- `error_msg` berisi ringkasan error (tanpa cookie/kredensial); `NULL` untuk
  `found`/`empty`.
- Status `error` bukan final: nomor error akan diproses lagi pada collect
  berikutnya, dan saat berhasil `error_msg` di-set `NULL`.
- Status `found`/`empty` di-skip pada collect berikutnya; hanya `force=true`
  atau `POST /api/refresh` yang memproses ulang.

### Operasi DELETE

| Operasi | Kapan | SQL |
| --- | --- | --- |
| Hapus hasil satu nomor | Nomor berubah jadi `empty`; refresh manual | `DELETE FROM tkdn_rows WHERE number = %s` |
| Hapus status satu nomor | Refresh manual (sebelum ambil ulang) | `DELETE FROM tkdn_checks WHERE number = %s` |
| Hapus total satu nomor | Refresh manual | Dua DELETE di atas dalam satu transaksi |

### Event yang TIDAK menulis ke DB

| Endpoint / aksi | Alasan |
| --- | --- |
| `GET /api/search` | Read-only, query `tkdn_rows` |
| `GET /api/export` | Read-only, query `tkdn_rows` |
| `GET /api/collect/preview` | Hanya menghitung dari `tkdn_checks` |
| `GET /api/status` | State job ada di memori |
| `POST /api/collect/cancel` | Hanya mengubah flag di memori |
| `POST /api/login` / `POST /api/logout` | Hanya mengelola `storageState.json`, bukan data aplikasi |

### Aturan transaksi & idempotensi

- Commit dilakukan **per nomor**, bukan per 1000 nomor. Job yang berhenti di
  tengah tidak kehilangan nomor yang sudah selesai.
- Satu event nomor = satu transaksi: DELETE (bila perlu) -> UPSERT
  `tkdn_rows` -> UPSERT `tkdn_checks` -> `commit()`. Gagal di tengah ->
  `rollback()`.
- Karena `row_hash` dan `number` unik, mengulang event yang sama tidak
  menggandakan data.
- Kalau `commit()` gagal karena koneksi DB putus, collector berhenti dengan
  `error: db_unavailable`; tidak ada status `found` palsu.

### Method store per event (rencana)

| Method | Event | Operasi |
| --- | --- | --- |
| `create_schema()` | Startup | CREATE + ALTER COMMENT |
| `upsert_rows(number, rows, fetched_at)` | Found, force, refresh | `INSERT ... ON DUPLICATE KEY UPDATE` |
| `delete_rows_for_number(number)` | Empty, refresh | DELETE baris |
| `upsert_check(number, status, error_msg, checked_at)` | Semua nomor selesai | `INSERT ... ON DUPLICATE KEY UPDATE` |
| `delete_number(number)` | Refresh | DELETE dari kedua tabel, satu transaksi |
| `get_check(number)` | Skip collect, validasi refresh | SELECT |
| `get_checks(numbers)` | Skip massal, preview | SELECT |

## Catatan Keputusan yang Sudah Ditutup

- **Stack**: Python + FastAPI + PyMySQL (BE) dan Vue 3 + TS + Bootstrap 5 + Vite + Pinia (FE). Bukan Elysia/Bun.
- **Koneksi INAPROC**: dari form Vue (`POST /api/login`), BE Playwright headless,
  simpan `storageState.json`, lalu buka halaman TKDN dengan state itu. Ini bukan
  login aplikasi. Fallback interaktif hanya untuk OTP/captcha.
- **Sumber data**: halaman `penyedia.inaproc.id/products/tkdn?keyword=...` via
  Playwright + parser HTML. **Tanpa GraphQL dan tanpa endpoint internal.**
- **API Gateway resmi**: jalur terpisah untuk data katalog/pengadaan
  (`data.inaproc.id`), read-only, Bearer token backend, dan tidak dipakai untuk
  TKDN.
- **Database**: MySQL wajib, tanpa fallback SQLite/file. Nama database memakai
  `INAPROC_MYSQL_DATABASE` agar tidak bertabrakan dengan `MYSQL_DATABASE` modul lain.
- **Styling**: Bootstrap 5, tanpa Emotion (keputusan user khusus modul `inaproc`).

## Keputusan (final)

1. **Styling FE**: Vue 3 + TS + Bootstrap 5 + Vite + Pinia. **Tidak pakai Emotion**, sesuai keputusan user untuk modul `inaproc`. Animasi loading pakai CSS Bootstrap/Vue transition yang hormati `prefers-reduced-motion`.
2. **Cara serve FE development**: **dev server Vite** (`npm run dev`) dengan proxy `/api` ke FastAPI. Produksi: build FE di lokal sebelum commit sebagai verifikasi, lalu CI build ulang & deploy. FastAPI = framework Python untuk API backend (terima request FE, jalankan scraping/query cache, balas JSON).
3. **API base URL/proxy**: `/api` satu origin via proxy Vite saat development; FastAPI serve static build di produksi.
4. **Semantik pencarian**: keyword (opsional) cocok ke semua kolom (nomor SPT, merek, tipe, jenis, uraian, standard) + filter opsional merek dan nilai minimum.
5. **Collect rentang**: **user memilih rentang sendiri** di FE (nomor contoh + start + end), maksimal 1000 nomor per request; rentang lebih besar dipecah otomatis per 1000. Delay acak 1-3 detik, retry backoff saat 429/5xx.
6. **Long-running collect**: background job + polling `GET /api/status` tiap 2 detik dari Pinia store (bukan WebSocket).
7. **Cache expiry**: tanpa expiry otomatis; ada tombol refresh manual per nomor.
8. **Akses FE/BE**: lokal saja. Aplikasi tidak memiliki login/akun sendiri.
   Satu-satunya kredensial adalah akun penyedia INAPROC, dimasukkan lewat form di
   Vue (`POST /api/login`) untuk membuka sesi INAPROC di backend.
9. **Database**: **MySQL**. `INAPROC_MYSQL_DATABASE` wajib diisi (tanpa fallback
   ke `MYSQL_DATABASE`). Tabel dibuat otomatis saat startup, dengan komentar
   tabel di schema. Tidak ada SQLite atau file database lokal.
10. **Ekspor & fitur tabel**: **semua** disetujui: export CSV, export JSON, filtering, sorting, dan pagination.
11. **Sumber data TKDN**: **HTML scrape via Playwright**. Endpoint GraphQL yang
    pernah ditemukan **tidak dipakai**, sesuai keputusan user. Backend membuka
    halaman TKDN, menunggu tabel render, lalu mem-parse HTML-nya.
12. **Sumber data katalog/pengadaan**: **INAPROC API Gateway resmi**
    (`data.inaproc.id`), read-only dan memakai Bearer token yang disimpan hanya
    di backend. Fitur nonaktif sampai token disetujui. API hanya dipakai untuk
    pencarian; hasil yang cocok menampilkan `source_url` agar user membuka
    detail di INAPROC setelah login di portal.
13. **Bahasa**: artefak teknis berbahasa Inggris. Pengecualian hanya untuk teks
    yang terlihat oleh user (Bahasa Indonesia) dan komentar penjelasan.
14. **Pesan error FE**: kode error dari API dipetakan menjadi pesan Indonesia di
    `web/src/api.ts`. Detail teknis tidak diteruskan langsung ke layar; pesan
    job dan sinkronisasi Gateway memakai mapping khusus agar tetap aman dibaca.
14. **Mulai implementasi TDD**: menyusul setelah rencana ini final.

## Sisa yang perlu diverifikasi (bukan keputusan desain)

Desain sudah final. Item di bawah adalah verifikasi teknis terhadap INAPROC
yang butuh sesi INAPROC aktif, bukan pertanyaan terbuka untuk user.

- [ ] **Verifikasi sesi live**: jalankan Runbook Langkah 1-2. Pastikan halaman TKDN
  terbuka tanpa redirect ke signin.
- [ ] **Selector tabel**: Runbook Langkah 3. Catat selector baris/kolom yang stabil
  untuk parser.
- [ ] **Bentuk halaman kosong**: Runbook Langkah 4. Bedakan "tidak ada hasil" dari
  error render.
- [ ] **Rate limit halaman**: Runbook Langkah 5 (429 + `Retry-After`), lalu kunci
  `delay_min`/`delay_max`/`max_retry`.
- [ ] **Mulai coding TDD**: setelah poin verifikasi di atas terisi, mulai dari
  `spt.py` + test, lalu `parser.py` dan `scraper.py`.

Catatan: poin verifikasi di atas butuh sesi INAPROC aktif dari FE. Tanpa itu, rencana
tetap bisa dibaca, TDD dengan fake Playwright page tetap bisa dimulai dari `spt.py`,
dan hanya nilai delay/backoff yang sementara memakai default.

## Matriks Test (TDD)

Setiap baris adalah satu test yang harus **gagal dulu** sebelum implementasi.

| File | Test | Perilaku yang dikunci |
| --- | --- | --- |
| `test_spt.py` | `test_parse_valid` | `"11469/SJ-IND.8/E-TKDN/7/2025"` -> 5 field benar |
| `test_spt.py` | `test_parse_bagian_kurang` | 4 bagian -> `ValueError` |
| `test_spt.py` | `test_parse_bulan_invalid` | bulan `13` -> `ValueError` |
| `test_spt.py` | `test_parse_tahun_bukan_4_digit` | `25` -> `ValueError` |
| `test_spt.py` | `test_parse_sequence_bukan_angka` | `x/SJ/...` -> `ValueError` |
| `test_spt.py` | `test_with_sequence` | field lain tetap, sequence berubah |
| `test_spt.py` | `test_str_roundtrip` | `parse(str(n)) == n` |
| `test_spt.py` | `test_sequence_range_inclusive` | `(1000,1003)` -> 4 angka |
| `test_spt.py` | `test_sequence_range_terbalik` | `(10,5)` -> `ValueError` |
| `test_auth.py` | `test_state_valid` | state berisi cookie/localStorage diterima |
| `test_auth.py` | `test_state_tanpa_cookie` | state kosong -> `AuthError` |
| `test_auth.py` | `test_state_tidak_valid` | struktur salah -> `AuthError`, pesan sebut file sesi INAPROC |
| `test_auth.py` | `test_state_hilang` | path tidak ada -> `AuthError` |
| `test_auth.py` | `test_connect_inaproc_simpan_state` | Playwright fake -> file state tertulis |
| `test_auth.py` | `test_connect_inaproc_kredensial_salah` | `AuthError` tanpa menulis state |
| `test_auth.py` | `test_connect_inaproc_timeout` | `AuthError` tanpa state parsial |
| `test_auth.py` | `test_password_tidak_dilog` | logger tidak menerima password |
| `test_parser.py` | `test_parse_tabel` | HTML tabel -> 6 kolom per baris |
| `test_parser.py` | `test_tabel_kosong` | tabel kosong -> `[]` |
| `test_parser.py` | `test_nilai_desimal` | `33.39` -> float, teks kosong -> `None` |
| `test_parser.py` | `test_baris_ganda` | dua baris data -> dua dict |
| `test_parser.py` | `test_markup_berubah` | selector tidak ketemu -> error jelas |
| `test_scraper.py` | `test_buka_url_keyword` | URL `/products/tkdn?keyword=...` dibuka |
| `test_scraper.py` | `test_pakai_storage_state` | context dibuat dengan `storageState.json` |
| `test_scraper.py` | `test_tunggu_tabel_render` | menunggu selector tabel sebelum parse |
| `test_scraper.py` | `test_redirect_signin` | redirect ke `/auth/signin` -> `AuthError` |
| `test_scraper.py` | `test_halaman_kosong` | tidak ada baris -> status `empty` |
| `test_scraper.py` | `test_timeout_selector` | selector timeout -> error yang bisa ditampilkan |
| `test_scraper.py` | `test_retry_429` | halaman 429 -> retry dengan backoff |
| `test_db.py` | `test_config_dari_env` | prefix `INAPROC_MYSQL_*` terbaca |
| `test_db.py` | `test_database_tidak_fallback` | `INAPROC_MYSQL_DATABASE` kosong -> error jelas, tidak memakai `MYSQL_DATABASE` |
| `test_db.py` | `test_connect_timeout` | opsi timeout diteruskan ke `pymysql.connect` |
| `test_db.py` | `test_koneksi_gagal` | `OperationalError` -> `DbUnavailableError` |
| `test_db.py` | `test_charset_utf8mb4` | `connect_mysql` mengirim `charset="utf8mb4"` |
| `test_cache.py` | `test_creates_schema_on_init` | init membuat dua tabel + `ALTER TABLE ... COMMENT` |
| `test_cache.py` | `test_simpan_dan_baca` | insert lalu query balik |
| `test_cache.py` | `test_upsert_tanpa_duplikat` | insert sama 2x -> 1 baris, `fetched_at` ter-update |
| `test_cache.py` | `test_upsert_perbarui_nilai` | nilai/standard berubah -> baris yang sama ikut ter-update |
| `test_cache.py` | `test_row_hash_stabil` | input sama -> hash sama; `None` dan `''` setara |
| `test_cache.py` | `test_filter_brand` | filter merek case-insensitive |
| `test_cache.py` | `test_filter_nilai_minimum` | `value >= 30` |
| `test_cache.py` | `test_filter_kombinasi` | `q` + `brand` + `min_value` digabung dengan `AND` |
| `test_cache.py` | `test_sort_dan_pagination_whitelist` | sort + limit/offset; kolom sort di luar whitelist ditolak |
| `test_cache.py` | `test_cek_status_nomor` | `tkdn_checks` found/empty/error; status error dianggap belum final |
| `test_cache.py` | `test_cek_status_tidak_konsisten` | `found` tanpa `tkdn_rows` -> perlu scraping; `empty` dengan baris yatim -> bersihkan dulu |
| `test_cache.py` | `test_refresh_hapus_nomor` | refresh menghapus baris nomor itu |
| `test_cache.py` | `test_koneksi_ditutup` | connection ditutup walau query gagal |
| `test_cache.py` | `test_utf8mb4` | merek/deskripsi non-ASCII tersimpan dan terbaca |
| `test_cache.py` | `test_event_empty_hapus_baris` | nomor berubah `empty` -> baris `tkdn_rows` lama terhapus |
| `test_cache.py` | `test_event_error_simpan_pesan` | status `error` menyimpan `error_msg` di `tkdn_checks` |
| `test_cache.py` | `test_event_error_retry_bersihkan_pesan` | error lalu sukses -> `error_msg` jadi `NULL` |
| `test_cache.py` | `test_delete_number_satu_transaksi` | refresh menghapus kedua tabel lalu commit sekali |
| `test_cache.py` | `test_rollback_saat_gagal` | gagal di tengah -> `rollback()`, tidak ada commit |
| `test_collector.py` | `test_loop_rentang` | 1000-1002 -> 3 nomor diproses |
| `test_collector.py` | `test_template_user` | template dari user dipakai apa adanya |
| `test_collector.py` | `test_rentang_tidak_hardcode` | start/end 5-7 memakai nilai user |
| `test_collector.py` | `test_skip_found_empty` | nomor found/empty dilewati |
| `test_collector.py` | `test_skip_tanpa_scrape` | nomor final di DB tidak memanggil scraper sama sekali |
| `test_collector.py` | `test_retry_error` | nomor error tidak dilewati, diproses lagi |
| `test_collector.py` | `test_force_ulang` | `force=True` memproses ulang |
| `test_collector.py` | `test_cancel_event` | cancel berhenti setelah nomor aktif |
| `test_collector.py` | `test_progres_terupdate` | hitungan done/found/empty/error |
| `test_collector.py` | `test_db_mati_stop_job` | MySQL putus -> status job `error: db_unavailable` |
| `test_api.py` | `test_search_dari_cache` | tidak memanggil scraper |
| `test_api.py` | `test_db_unavailable` | MySQL mati -> `503 db_unavailable` |
| `test_api.py` | `test_lookup_dari_db_tanpa_scrape` | nomor `found` -> `source: "db"`, scraper tidak dipanggil |
| `test_api.py` | `test_lookup_empty_tanpa_scrape` | nomor `empty` -> `items: []`, scraper tidak dipanggil |
| `test_api.py` | `test_lookup_belum_ada_scrape` | nomor baru -> scraper dipanggil, hasil di-UPSERT |
| `test_api.py` | `test_lookup_error_scrape_ulang` | status `error` -> scraping ulang |
| `test_api.py` | `test_lookup_tanpa_sesi_saat_perlu_scrape` | nomor baru + sesi kosong -> `401 belum_login` |
| `test_api.py` | `test_lookup_nomor_invalid` | format salah -> `422 nomor_tidak_valid` |
| `test_api.py` | `test_search_tidak_pernah_scrape` | `q` nomor yang belum ada -> hasil kosong, scraper tidak dipanggil |
| `test_api.py` | `test_search_tanpa_q` | tanpa `q` -> semua baris cache |
| `test_api.py` | `test_collect_validasi_rentang` | >1000 nomor -> 422 `rentang_terlalu_besar` |
| `test_api.py` | `test_collect_tepat_1000` | 1000 nomor -> 202, diterima |
| `test_api.py` | `test_preview_chunks` | 1001 nomor -> `chunks: 2` |
| `test_api.py` | `test_export_tanpa_pagination` | `page`/`per_page` diabaikan, semua baris diekspor |
| `test_api.py` | `test_collect_rentang_terbalik` | `start > end` -> 422 |
| `test_api.py` | `test_collect_nomor_invalid` | template bukan 5 bagian -> 422 |
| `test_api.py` | `test_collect_preview` | hitung total/sudah_ada/akan_diproses |
| `test_api.py` | `test_collect_butuh_sesi_inaproc` | sesi INAPROC kosong -> 401 |
| `test_api.py` | `test_collect_job_aktif` | request kedua -> 409 |
| `test_api.py` | `test_status_idle` | tanpa job -> status `idle` |
| `test_api.py` | `test_status_memuat_rentang` | status berisi nomor/start/end chunk aktif |
| `test_api.py` | `test_session_tanpa_file` | `configured: false`, tidak bocor isi state |
| `test_api.py` | `test_connect_inaproc_sukses` | 200 + session configured (auth di-stub) |
| `test_api.py` | `test_connect_inaproc_kredensial_salah` | 401, state tidak dibuat |
| `test_api.py` | `test_connect_inaproc_butuh_otp` | 409 dengan kode `butuh_interaksi` |
| `test_api.py` | `test_logout_hapus_state` | file state terhapus |
| `test_api.py` | `test_export_csv` | header `text/csv` + isi sesuai filter |
| `test_api.py` | `test_export_json` | JSON valid, jumlah baris sesuai |
| `test_api.py` | `test_refresh_hapus_dan_ambil_ulang` | baris lama dihapus, data baru masuk cache |
| `test_api.py` | `test_refresh_saat_job_aktif` | `409 job_aktif` |
| `test_api.py` | `test_refresh_nomor_belum_ada` | `404 nomor_tidak_ditemukan` |
| `test_api.py` | `test_refresh_nomor_tidak_valid` | `422 nomor_tidak_valid` |
| `test_exporter.py` | `test_header_csv` | urutan kolom tetap |
| `test_exporter.py` | `test_nilai_null` | `None` -> string kosong |
| `test_exporter.py` | `test_escape_koma` | deskripsi berkoma tetap 1 sel |
| `test_exporter.py` | `test_json_struktur` | list of object dengan key snake_case |
| `web/tests/tkdn.spec.ts` | `test_search_action` | action memanggil `/api/search` |
| `web/tests/tkdn.spec.ts` | `test_loading_disabled` | tombol disabled saat loading |
| `web/tests/tkdn.spec.ts` | `test_poll_status` | polling berhenti saat status `done` |
| `web/tests/tkdn.spec.ts` | `test_error_state` | error tersimpan di store |
| `web/tests/tkdn.spec.ts` | `test_export_url` | URL ekspor ikut filter aktif |
| `web/tests/tkdn.spec.ts` | `test_session_badge` | badge sesi INAPROC dari `/api/session` |
| `web/tests/tkdn.spec.ts` | `test_connect_inaproc_action` | action `connect()` di store sesi memanggil `/api/login` |
| `web/tests/tkdn.spec.ts` | `test_connect_inaproc_error` | 401 menampilkan pesan koneksi INAPROC gagal |
| `web/tests/tkdn.spec.ts` | `test_range_pilihan_user` | start/end dari input dikirim apa adanya |
| `web/tests/tkdn.spec.ts` | `test_chunk_rentang_besar` | 1000..2500 -> 2 request: 1000..1999, 2000..2500 |
| `web/tests/tkdn.spec.ts` | `test_chunk_berurutan` | chunk 2 baru dikirim setelah status chunk 1 `done` |
| `web/tests/tkdn.spec.ts` | `test_progres_gabungan` | progres = total done semua chunk / total rentang |
| `web/tests/tkdn.spec.ts` | `test_cancel_hentikan_antrean` | Batal tidak mengirim chunk berikutnya |
| `web/tests/tkdn.spec.ts` | `test_chunk_gagal_stop` | chunk gagal -> antrean berhenti + pesan chunk |
| `web/tests/tkdn.spec.ts` | `test_preview_rentang` | tombol Cek Rentang memanggil preview |
| `web/tests/tkdn.spec.ts` | `test_refresh_nomor` | action refresh memanggil `/api/refresh` lalu search ulang |

## Estimasi

| Bagian | Perkiraan |
| --- | --- |
| Tahap 0: Database (`config`, `db`) + test | 45-60 menit |
| Tahap 1-2: `spt`, `parser` + fixture HTML asli | 1-1.5 jam |
| Tahap 3-4: `auth`, `login`, `scraper` + probe asli | 2-3 jam (tergantung OTP/captcha) |
| Tahap 5: `cache`, `exporter` + test | 1-1.5 jam |
| Tahap 6-7: `collector`, `schemas`, `api` + test | 2-3 jam |
| Tahap 8: API Gateway + test | 2-3 jam (setelah token disetujui) |
| Tahap 9: Frontend + Vitest | 3-4 jam |
| Tahap 10: Verifikasi real case + smoke test | 1-2 jam |
| **Total** | **2-3 hari kerja** (12-18 jam efektif) |

Biaya waktu collect: 1000 nomor dengan delay 1-3 detik = 25-50 menit per job.
Nomor yang sudah pernah dicek tidak diulang, jadi job berikutnya jauh lebih cepat.

## Definisi Selesai (Definition of Done)

Modul dianggap selesai bila semua ini terpenuhi.

**Backend**

- [ ] `python -m unittest` dari root repo hijau, termasuk test modul ini.
- [ ] Database `inaproc` sudah dibuat manual dan `INAPROC_MYSQL_DATABASE` terisi;
  API tidak diam-diam memakai database modul lain.
- [ ] `SHOW TABLES` menampilkan `tkdn_rows` dan `tkdn_checks`, keduanya punya
  komentar tabel yang menjelaskan tujuannya.
- [ ] Upsert nomor yang sama 2x tidak membuat baris duplikat.
- [ ] MySQL dimatikan saat API jalan -> endpoint mengembalikan `503 db_unavailable`
  dengan pesan jelas, bukan crash atau stack trace.
- [ ] Koneksi INAPROC dari FE (`POST /api/login`) menghasilkan
  `storageState.json` yang valid. Tidak ada akun aplikasi yang dibuat.
- [ ] Fallback `python -m modules.inaproc login` tetap jalan untuk OTP/captcha.
- [ ] `scraper.py` berhasil membuka halaman nomor `11469/...` dan `parser.py`
  menghasilkan baris TKDN setelah sesi INAPROC terhubung dari FE.
- [ ] Nomor tidak ada tercatat `empty`, bukan `error`.
- [ ] Sesi INAPROC kedaluwarsa (redirect ke signin) menghasilkan pesan jelas,
  bukan crash.
- [ ] Collect 10 nomor berurutan berjalan dan progres ter-update.
- [ ] Rentang >1000 nomor dipecah FE dan dijalankan berurutan tanpa `409`.
- [ ] Cancel job berhenti rapi (tidak ada thread menggantung).
- [ ] `POST /api/refresh` memperbarui satu nomor tanpa mengganggu job lain.
- [ ] `POST /api/lookup` untuk nomor yang sudah `found`/`empty` **tidak**
  memanggil Playwright; respons berisi `source: "db"`.
- [ ] `POST /api/lookup` untuk nomor baru memanggil Playwright sekali, lalu
  lookup berikutnya dibalas dari DB (`source: "db"`).
- [ ] `GET /api/search` tidak pernah memanggil Playwright, termasuk saat `q`
  berisi nomor yang belum ada.
- [ ] Cache tidak menyimpan duplikat saat nomor yang sama diambil ulang.
- [ ] Database menggunakan `utf8mb4`; pencarian merek/deskripsi tidak gagal
  karena karakter non-ASCII.
- [ ] Export CSV terbuka benar di Excel (delimiter, encoding UTF-8).
- [ ] Tidak ada isi `storageState.json`/kredensial di file yang di-track git.
- [ ] Token API Gateway tidak pernah muncul di response FE, log, atau file git.
- [ ] Tidak ada request tulis ke INAPROC (POST/PUT/PATCH/DELETE ke domain
  INAPROC) di kode aplikasi; semua panggilan eksternal hanya GET.
- [ ] Saat `INAPROC_API_TOKEN` kosong, fitur Gateway nonaktif dan TKDN tetap jalan.
- [ ] Sync Gateway idempotent: halaman yang sama dua kali tidak menambah baris.
- [ ] Upsert Gateway hanya menulis ke DB app; tidak ada request tulis ke INAPROC.
- [ ] Sync Gateway berhenti benar saat `meta.has_more=false`.
- [ ] `429`/`5xx` di-retry dengan backoff; `400`/`401`/`403`/`404` tidak di-retry.
- [ ] Setiap sync tercatat di `inaproc_api_sync_runs` dengan status akhir.
- [ ] Pencarian produk/e-purchasing dari FE hanya query MySQL, tidak memanggil
  API Gateway saat request user.

**Frontend**

- [ ] `npm run build` di `web/` sukses.
- [ ] `npm run test` (Vitest) hijau.
- [ ] Form koneksi INAPROC muncul saat sesi INAPROC belum ada dan berhasil
  mengarahkan ke halaman pencarian.
- [ ] Pencarian dari cache menampilkan tabel dengan filter, sorting, pagination.
- [ ] Tombol disabled + spinner saat request berjalan.
- [ ] Progres collect terlihat dan berhenti saat selesai.
- [ ] Progres gabungan antar chunk akurat dan label chunk tampil.
- [ ] Ekspor CSV/JSON mengikuti filter aktif.
- [ ] Tombol refresh per nomor memperbarui baris tanpa reload halaman.
- [ ] Panel API Gateway menampilkan status token dan tombol sync dengan disabled
  loading state; pesan jelas saat token belum disetujui.
- [ ] Badge sumber data membedakan `API Gateway`, `Portal TKDN`, dan `Database`.
- [ ] Baris produk Gateway menampilkan link `Detail INAPROC` bila `source_url`
  tersedia; klik link membuka tab baru dan tidak memicu request backend.
- [ ] User yang belum login ke portal INAPROC mendapat halaman login normal saat
  membuka link, tanpa aplikasi mencoba meneruskan sesi backend.
- [ ] Tampilan tetap rapi di lebar 360 px dan 1440 px.
- [ ] `prefers-reduced-motion: reduce` mematikan animasi.

**Dokumentasi**

- [ ] `rencana.md` dan `tugas.md` tidak saling bertentangan.
- [ ] Perintah menjalankan BE dan FE tertulis di README modul.

## Runbook Verifikasi (setelah sesi INAPROC terhubung)

Dijalankan setelah FE + `POST /api/login` berfungsi. Tidak perlu tool tambahan,
cukup aplikasi yang sudah jalan.

### Langkah 0: siapkan MySQL

```powershell
mysql -u root -e "CREATE DATABASE IF NOT EXISTS inaproc CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -e "SHOW TABLES;" inaproc
```

Isi `.env` minimal:

```
INAPROC_MYSQL_DATABASE=inaproc
```

Host/port/user/password boleh memakai fallback `MYSQL_*`, tetapi database
**wajib** lewat `INAPROC_MYSQL_DATABASE`. Setelah API start, `SHOW TABLES` harus
menampilkan `tkdn_rows` dan `tkdn_checks`. Kalau MySQL mati, jalankan
`GET /api/search` dan pastikan responsnya `503 db_unavailable`.

### Langkah 1: hubungkan sesi INAPROC dari FE

Buka FE di browser, isi email/password **akun penyedia INAPROC** di form koneksi
INAPROC, lalu submit. Ini bukan login aplikasi. Cek:

```powershell
Test-Path modules/inaproc/storageState.json
```

Kalau INAPROC minta OTP/captcha, pakai fallback:

```powershell
python -m modules.inaproc login
```

### Langkah 2: validasi `storageState.json`

State sesi harus berisi cookie/localStorage INAPROC. Cek struktur tanpa
mencetak nilai cookie:

```powershell
python -c 'from modules.inaproc.auth import muat_storage_state, validasi_sesi; s=muat_storage_state("modules/inaproc/storageState.json"); print(len(s.get("cookies", [])), len(s.get("origins", []))); validasi_sesi(s); print("state valid")'
```

Jangan pernah mencetak nilai cookie atau isi localStorage.

### Langkah 3: buka halaman TKDN dengan Playwright

Jalankan probe satu nomor. Probe membuka URL, menunggu tabel render, lalu
mencetak jumlah baris dan selector yang dipakai parser:

```powershell
python -m modules.inaproc probe --nomor 11469/SJ-IND.8/E-TKDN/7/2025
```

Yang dicatat dari hasil ini:

| Yang dicek | Ekspektasi |
| --- | --- |
| URL akhir | tetap `/products/tkdn?keyword=...`, bukan `/auth/signin` |
| Selector tabel | ketemu dan stabil |
| Jumlah baris | minimal 1 untuk nomor contoh |
| Merek baris pertama | `acer` |
| Nilai baris pertama | `33.39` (hasil parse float) |
| Standard kosong | `None` atau `-` |

Kalau probe belum tersedia, verifikasi setara bisa dilakukan lewat collect satu
nomor lalu periksa hasil di `GET /api/search`.

### Langkah 4: probe nomor yang tidak ada

Ulangi langkah 3 dengan nomor `999999/SJ-IND.8/E-TKDN/7/2025`.

| Kemungkinan hasil | Tindakan |
| --- | --- |
| Tabel kosong / teks tidak ditemukan | Nomor kosong = `empty`, aman |
| Tabel ada tapi 0 baris data | Nomor kosong = `empty` |
| Halaman error atau markup asing | Perlakukan sebagai `error`, catat selector |
| Redirect ke `/auth/signin` | Sesi kedaluwarsa = `AuthError` |

### Langkah 5: probe rate limit halaman

Buka 10 nomor berurutan dengan jeda 1-3 detik memakai probe atau collect kecil.
Catat bila muncul halaman 429, captcha, atau blokir sementara. Sesuaikan
`delay_min`/`delay_max` dan `max_retry` di `scraper.py`.

### Langkah 6: putuskan final

Setelah 5 langkah di atas, item di bagian "Sisa yang perlu diverifikasi" bisa
dicentang, lalu TDD `parser.py` + `scraper.py` dimulai.

### Langkah 7: verifikasi akses API Gateway (setelah token disetujui)

Jangan isi `INAPROC_API_TOKEN` dalam contoh, chat, atau file yang di-track.
Verifikasi berikut cukup menampilkan status yang sudah disamarkan:

```powershell
$env:INAPROC_API_TOKEN="<token-dari-portal>"; python -m modules.inaproc gateway-status
```

Yang dicek:

| Yang dicek | Ekspektasi |
| --- | --- |
| Status Gateway | `enabled=true` dan response JSON standar terbaca |
| Log/error | Token tidak muncul sama sekali |
| Endpoint disetujui | Hanya scope yang dipilih di portal dipanggil |
| Sync kecil | Satu halaman pertama masuk ke tabel Gateway tanpa duplikat |
| Rate limit | Header limit/remaining/reset dicatat secara aman |

Kalau endpoint `gateway-status` belum ada pada tahap implementasi awal, gunakan
unit test dengan fake HTTP; jangan uji token langsung lewat curl di dokumentasi.

## .gitignore untuk modul ini

Tambahkan (tanpa menyentuh aturan modul lain):

```
modules/inaproc/storageState.json
modules/inaproc/*.session.json
modules/inaproc/output/
```

Alasan: `storageState.json` berisi cookie/localStorage sesi INAPROC aktif;
`output/` berisi ekspor CSV/JSON. Cache utama ada di MySQL, bukan file lokal.

## Investigasi HTML/DOM Halaman TKDN

Investigasi ini menentukan selector dan perilaku halaman, bukan endpoint API.
Semua pengambilan data dilakukan dengan membuka halaman TKDN memakai Playwright.

### Cara investigasi

1. Hubungkan sesi penyedia INAPROC lebih dulu.
2. Buka `https://penyedia.inaproc.id/products/tkdn?keyword=11469%2FSJ-IND.8%2FE-TKDN%2F7%2F2025`.
3. Tunggu sampai tabel hasil selesai dirender.
4. Buka DevTools -> **Elements**, bukan tab Network.
5. Catat selector tabel, baris data, header kolom, dan elemen status kosong.
6. Ulangi dengan nomor yang tidak ada untuk melihat bentuk halaman kosong.

### Temuan halaman

- Halaman TKDN dilindungi sesi penyedia INAPROC. Tanpa sesi, halaman
  di-redirect ke `/auth/signin`.
- Tabel hasil berisi kolom: Jenis Produk, Merek, Tipe, Uraian Produk,
  Standard, dan Nilai.
- Satu nomor SPT dapat menghasilkan lebih dari satu baris TKDN.
- Data baru muncul setelah JavaScript merender halaman, sehingga scraper harus
  menunggu selector tabel dan baris data, bukan hanya event `load`.
- Nomor yang tidak ada harus dibedakan dari kegagalan render: cek teks status
  kosong dan jumlah baris data.

### Selector yang perlu dikunci saat implementasi

Selector belum ditetapkan sebagai konstanta final karena harus diverifikasi
terhadap halaman live. Yang perlu dicatat:

| Kebutuhan | Yang dicari |
| --- | --- |
| Tabel hasil | elemen tabel utama di area hasil pencarian |
| Baris data | `tbody tr` yang berisi 6 kolom |
| Header kolom | urutan header untuk memastikan mapping kolom |
| Status kosong | teks "tidak ditemukan" atau empty state sejenis |
| Indikator error | alert/error state dari halaman |
| Form signin | penanda redirect ke `/auth/signin` |

Semua selector disimpan sebagai konstanta di `parser.py`/`scraper.py` agar mudah
diperbarui bila markup INAPROC berubah.

### Perilaku yang harus ditangani

| Kondisi | Perilaku scraper |
| --- | --- |
| Sesi valid | tabel ditemukan, baris diparse |
| Sesi kedaluwarsa | URL akhir `/auth/signin` -> `AuthError` |
| Nomor tidak ada | tabel kosong/empty state -> status `empty` |
| Markup berubah | selector tidak ditemukan -> error jelas |
| Timeout render | error yang bisa ditampilkan ke FE |
| HTTP 429/blokir | backoff, delay acak, retry terbatas |

### Batasan investigasi

- Selector final wajib diverifikasi dengan sesi INAPROC aktif.
- Bentuk empty state dan perilaku rate limit belum bisa dianggap final sebelum
  probe live dijalankan.
- Tidak perlu screenshot untuk pengambilan data; cukup HTML/DOM yang sudah
  dirender.

### Checklist verifikasi

- [ ] `storageState.json` valid dan halaman TKDN tidak redirect ke signin.
- [ ] Selector tabel dan baris data ditemukan.
- [ ] Enam kolom terpetakan dengan urutan benar.
- [ ] Nomor tidak ada menghasilkan `empty`, bukan `error`.
- [ ] Timeout dan markup berubah menghasilkan pesan error yang jelas.
- [ ] Rate limit/429 ditangani dengan backoff dan delay acak.

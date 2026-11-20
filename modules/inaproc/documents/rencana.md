# Rencana Tool Pengumpul Data TKDN INAPROC

## Tujuan

Mengumpulkan data TKDN (Jenis Produk, Merek, Tipe, Uraian Produk, Standard, Nilai)
untuk sekumpulan nomor SPT yang berurutan, tanpa mengetik nomor satu per satu di
browser. Hasil akhir bisa dilihat dan dicari di FE (filter, sorting, pagination)
serta diekspor ke CSV atau JSON. Data disimpan di cache SQLite lokal supaya
pencarian berikutnya tidak perlu request ulang ke INAPROC.

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

## Arsitektur Baru: FE -> BE -> INAPROC

User mencari lewat **frontend**, backend yang mengambil data dari INAPROC,
lalu hasilnya ditampilkan kembali ke frontend. Sumber data adalah **halaman TKDN
INAPROC yang dirender di browser**. Backend membuka halaman itu dengan Playwright,
menunggu tabel selesai render, lalu membaca HTML tabelnya. **Tidak memakai GraphQL
dan tidak memanggil endpoint internal INAPROC secara langsung.**

```
[FE: hubungkan sesi INAPROC sekali] --POST /api/login--> [Playwright headless -> storageState.json]
        |
[User di FE: input keyword / pilih rentang nomor]
        |  GET /api/search?q=acer  atau  POST /api/collect {nomor, start, end}
        v
[Backend Python (FastAPI)]
        |  cek cache dulu (SQLite lokal)
        |  -- cache ada --> langsung kembalikan hasil (cepat)
        |  -- cache kosong -->
        v
[Playwright + storageState sesi INAPROC]
        |  buka https://penyedia.inaproc.id/products/tkdn?keyword=<nomor SPT>
        |  tunggu tabel hasil render
        |  ambil HTML tabel -> parser.py
        |  delay + backoff
        v
[Baris TKDN] -> [simpan ke cache] -> [JSON response ke FE]
```

**Poin penting**

- **Koneksi INAPROC cukup 1x dari FE**, lalu `storageState.json` dipakai ulang.
  Tidak ada koneksi ulang di dalam loop request. Ini bukan login aplikasi.
- **Cache wajib**: hasil scraping disimpan sekali, pencarian berikutnya
  (misal cari merek `acer`) murni query lokal. Ini mencegah request berulang ke
  INAPROC dan menjawab keluhan "lambat kalau 1-1".
- Endpoint `POST /api/collect` dipakai untuk mengisi cache rentang nomor;
  `GET /api/search?q=...` dipakai user untuk mencari produk/merek (dari cache).
- FE hanya konsumsi API BE. FE **tidak** pernah menyimpan kredensial atau state
  sesi INAPROC.

### File tambahan untuk arsitektur FE/BE

| File | Fungsi |
| --- | --- |
| `modules/inaproc/api.py` | Aplikasi FastAPI: `/api/login`, `/api/logout`, `/api/session`, `/api/search`, `/api/collect`, `/api/collect/preview`, `/api/collect/cancel`, `/api/status`, `/api/export`, `/api/refresh` |
| `modules/inaproc/auth.py` | Koneksi INAPROC headless (`email`/`password`) + validasi `storageState.json`; bukan autentikasi aplikasi |
| `modules/inaproc/login.py` | Fallback interaktif Playwright untuk koneksi INAPROC (OTP/captcha); koneksi normal lewat `POST /api/login` |
| `modules/inaproc/scraper.py` | Buka halaman TKDN dengan Playwright + `storageState.json`, tunggu tabel render, kembalikan HTML/baris |
| `modules/inaproc/parser.py` | Parse tabel HTML hasil render menjadi baris TKDN (jalur utama, bukan fallback) |
| `modules/inaproc/cache.py` | Simpan/ambil hasil ke SQLite lokal (`tkdn.db`), query by merek/produk |
| `modules/inaproc/schemas.py` | Model Pydantic untuk request/response API |
| `modules/inaproc/web/index.html` | Entry point Vite untuk aplikasi Vue 3 |
| `modules/inaproc/web/package.json` | Dependency FE: Vue 3, TypeScript, Bootstrap 5, Vite, Pinia, Vitest |
| `modules/inaproc/web/vite.config.ts` | Config Vite + proxy `/api` ke FastAPI saat development |
| `modules/inaproc/web/tsconfig.json` | Config TypeScript FE |
| `modules/inaproc/web/src/main.ts` | Bootstrap aplikasi Vue + Pinia + Bootstrap 5 |
| `modules/inaproc/web/src/App.vue` | Layout utama: form pencarian, tabel hasil, panel progres |
| `modules/inaproc/web/src/types.ts` | Tipe TS untuk request/response API dan baris TKDN |
| `modules/inaproc/web/src/api.ts` | Wrapper `fetch` ke endpoint BE (`/api/search`, `/api/collect`, `/api/status`, `/api/refresh`) |
| `modules/inaproc/web/src/stores/tkdn.ts` | Pinia store (VM): state filter/hasil/status/chunk, action search/collect/poll/refreshNumber |
| `modules/inaproc/web/src/stores/inaprocSession.ts` | Pinia store: status sesi INAPROC, action connect/disconnect |
| `modules/inaproc/web/src/components/ConnectInaprocForm.vue` | Form email/password akun penyedia INAPROC ke `POST /api/login`, disabled + spinner saat proses |
| `modules/inaproc/web/src/components/SearchForm.vue` | Input keyword + rentang nomor + tombol cari/collect (disabled saat loading) |
| `modules/inaproc/web/src/components/ResultTable.vue` | Tabel hasil (merek, tipe, uraian, standard, nilai, nomor SPT) + tombol refresh per baris |
| `modules/inaproc/web/src/components/CollectForm.vue` | Nomor contoh + rentang pilihan user + Cek Rentang + Mulai/Batal |
| `modules/inaproc/web/src/components/PaginationBar.vue` | Info jumlah, pindah halaman, tombol ekspor |
| `modules/inaproc/web/src/components/SessionBadge.vue` | Status sesi INAPROC dari `/api/session` |
| `modules/inaproc/web/src/components/CollectProgress.vue` | Indikator progres collect dari `/api/status` |
| `modules/inaproc/web/tests/tkdn.spec.ts` | Vitest: store search/collect sukses & gagal, render komponen |
| `modules/inaproc/tests/test_auth.py` | Test validasi state sesi dan koneksi INAPROC headless dari state dummy |
| `modules/inaproc/tests/test_exporter.py` | Test CSV & JSON |
| `modules/inaproc/tests/test_scraper.py` | Test navigasi Playwright, deteksi redirect login, timeout, dan retry dengan fake page |
| `modules/inaproc/tests/test_collector.py` | Test loop rentang, skip cache, cancel, progres |
| `modules/inaproc/tests/test_api.py` | Test endpoint FastAPI dengan dependency/stub |
| `modules/inaproc/tests/test_spt.py` | Test parse dan rentang nomor SPT |
| `modules/inaproc/tests/test_schemas.py` | Test validasi request/response API |
| `modules/inaproc/tests/test_cache.py` | Test SQLite cache, filter, sort, pagination |
| `modules/inaproc/tests/test_cli.py` | Test argumen dan dispatch CLI dengan mock |
| `modules/inaproc/tests/test_login.py` | Test fallback koneksi INAPROC interaktif dengan Playwright fake |
| `modules/inaproc/tests/test_parser.py` | Test parser tabel HTML (tabel kosong, beberapa baris, nilai desimal) |
| `modules/inaproc/pyproject.toml` | Metadata modul + dependency (`fastapi`, `playwright`, `uvicorn`) untuk `pip install -e modules/inaproc` |
| `modules/inaproc/README.md` | Cara menjalankan BE + FE, koneksi sesi INAPROC, collect, dan catatan sesi |

### Perubahan pada file yang sudah direncanakan

- `scraper.py`: dipakai oleh `api.py` dan `collector.py`, bukan langsung oleh CLI.
- `collector.py`: hasilnya ditulis ke `cache.py`, bukan hanya CSV.
- `__main__.py`: bisa tetap ada untuk mode CLI (bulk awal mengisi cache), tapi
  fokus utama bergeser ke `api.py`.

### Konvensi path test

Semua test modul ini berada di `modules/inaproc/tests/` dan diberi prefix
`modules.inaproc.tests`. Tabel di dokumen ini kadang menulis nama file saja
(`test_api.py`); artinya tetap `modules/inaproc/tests/test_api.py`. Ini mengikuti
aturan AGENTS.md: test modul disimpan di dalam modul, bukan di `tests/` root.

### Urutan TDD ringkas

1. `auth.py` + test (koneksi INAPROC headless, fake Playwright)
2. `spt.py` + test
3. `parser.py` + `scraper.py` + test (HTML tabel, fake Playwright page)
4. `cache.py` + test
5. `schemas.py` + test
6. `collector.py` + test
7. `api.py` + test (TestClient, stub collector)
8. `exporter.py` + test (CSV + JSON)
9. FE (`web/`) + Vitest store/komponen (termasuk form koneksi INAPROC) + smoke test browser

### Stack keputusan (update)

- **BE: Python + FastAPI** (satu bahasa dengan Playwright & cache; TDD `python -m unittest` lewat `TestClient`).
- **FE: Vue 3 + TypeScript + Bootstrap 5 + Vite + Pinia**. Bootstrap 5 untuk layout/komponen; animasi spinner memakai CSS Bootstrap/Vue transition yang menghormati `prefers-reduced-motion`.
- **Tidak memakai Emotion** di modul `inaproc` (keputusan user).
- **Sumber data: halaman TKDN INAPROC** `https://penyedia.inaproc.id/products/tkdn?keyword=...` via Playwright + parser HTML. **Tanpa GraphQL.**
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

### State wajib

| State | Tampilan |
| --- | --- |
| sesi INAPROC belum terhubung | hanya form koneksi INAPROC, tanpa tabel |
| menghubungkan INAPROC | tombol disabled + spinner |
| koneksi INAPROC gagal | `alert alert-danger` di atas tombol |
| loading cari | tombol disabled + spinner, tabel tetap tampil dengan opacity |
| cache kosong | `alert alert-info` "Belum ada data. Jalankan Ambil Data." |
| hasil kosong | `alert alert-warning` "Tidak ada hasil untuk filter ini." |
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
- Setiap baris punya tombol refresh (ikon) yang memanggil `POST /api/refresh`.
- Tabel responsif: `table-responsive` + `table table-sm table-hover align-middle`.
- Tanpa kartu bertumpuk, tanpa hero, tanpa ilustrasi dekoratif.

## Prinsip

- **TDD**: setiap fitur diawali test yang gagal (`python -m unittest` dari root repo), lalu implementasi minimal, lalu refactor.
- **Sesi INAPROC dipakai ulang**: koneksi INAPROC cukup sekali dari FE, lalu
  `storageState.json` dipakai ulang untuk setiap halaman yang dibuka Playwright.
  Ini bukan login aplikasi.
- **Akses wajar**: delay acak + retry dengan backoff, bukan request paralel masif.
- **Tidak ada kredensial hardcode**. Password akun penyedia INAPROC hanya lewat
  form Vue -> `POST /api/login`, dipakai sekali, tidak disimpan. Sesi INAPROC
  disimpan lokal & di-gitignore.
- **Cache-first**: FE selalu baca cache; INAPROC hanya disentuh saat collect/refresh.
- **Satu job collect aktif**: mencegah dua loop paralel membebani INAPROC.
- **Data mentah tetap disimpan**: kolom `hs` dan `specification_id` ikut di-cache walau belum dipakai FE.
- Modul berada di `modules/inaproc/`, test di `modules/inaproc/tests/`.
- Modul ini **tidak memakai Emotion**; styling FE pakai Bootstrap 5 (keputusan user).

## Ringkasan Eksekusi (urutan kerja nyata)

Supaya tidak bingung saat mulai, ini urutan yang akan dijalankan:

| Tahap | Pekerjaan | Hasil |
| --- | --- | --- |
| 0 | `auth.py` koneksi INAPROC headless + test | koneksi INAPROC dari BE jalan |
| 1 | `spt.py` + test | parsing nomor terkunci |
| 2 | `parser.py` + `scraper.py` + test | baca tabel HTML dari halaman yang dirender |
| 3 | `cache.py`, `exporter.py` + test | simpan & ekspor data |
| 4 | `collector.py` + test | loop rentang, progres, cancel |
| 5 | `api.py`, `schemas.py` + test | `/api/login` s/d `/api/refresh` |
| 6 | FE Vue + Pinia + Vitest | form koneksi INAPROC, pencarian, tabel, ekspor, chunk rentang |
| 7 | Verifikasi live | sesi valid, bentuk `empty`, selector tabel, rate limit |
| 8 | Smoke test | koneksi INAPROC via FE, collect 10 nomor, cari, ekspor |

Tahap 0-5 murni `python -m unittest` tanpa jaringan (Playwright di-fake).
Tahap 7 baru menyentuh INAPROC sungguhan, setelah FE dan BE siap.

## Daftar File Inti yang Akan Dibuat

File pendukung (FE, test, README, `pyproject.toml`) sudah dirinci di tabel
"File tambahan untuk arsitektur FE/BE" di atas.

### 1. `modules/inaproc/__init__.py`

Menjadikan `inaproc` sebagai paket Python. Diekspos API publik:
`SptNumber`, `build_keyword`, `TkdnScraper`, `parse_rows`, `collect`.

### 2. `modules/inaproc/tests/__init__.py`

Menandai folder test sebagai paket (polanya mengikuti modul lain di repo).

### 3. `modules/inaproc/spt.py`

Logika pembentuk nomor & keyword, murni tanpa jaringan:

- `SptNumber(prefix, sequence, suffix)` - representasi nomor SPT.
- `build_keyword(number)` - menghasilkan string `11469/SJ-IND.8/E-TKDN/7/2025`.
- `build_url(keyword)` - URL halaman `/products/tkdn?keyword=...` untuk dibuka
  Playwright, encode dengan `urllib.parse.quote`.
- `sequence_range(start, end)` - generator angka rentang pilihan user (inklusif).

Test: `modules/inaproc/tests/test_spt.py` (url encoding, rentang, format nomor).

### 4. `modules/inaproc/parser.py`

Ekstraksi tabel dari HTML yang sudah dirender. Ini jalur utama pengambilan data.

- `parse_rows(html)` -> list of dict dengan 6 kolom yang dibutuhkan FE.
- Kolom wajib: jenis produk, merek, tipe, uraian, standard, nilai.
- Tabel kosong atau halaman "tidak ditemukan" -> `[]`.
- Nilai desimal diparse ke `float`; teks kosong -> `None`.
- Selector tabel disimpan sebagai konstanta yang mudah diperbarui bila markup
  INAPROC berubah.

Test: `modules/inaproc/tests/test_parser.py` (HTML contoh dari tugas.md, tabel kosong,
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

Test: `modules/inaproc/tests/test_scraper.py` dengan **fake Playwright page**
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

Test: `modules/inaproc/tests/test_collector.py` dengan scraper & parser palsu.

### 7. `modules/inaproc/exporter.py`

- `write_csv(rows, path)` dan `write_json(rows, path)` (+ `write_jsonl` untuk
  arsip baris).
- Kolom: `number, product_type, brand, type, description, standard, value, hs`.
- Dipakai endpoint `GET /api/export?format=csv|json` sehingga hasil ekspor
  mengikuti filter yang sedang aktif di FE.

Test: `modules/inaproc/tests/test_exporter.py` (headers, urutan kolom, nilai `null`, escaping koma).

### 8. `modules/inaproc/__main__.py`

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
- Output default: `modules/inaproc/output/hasil.csv` + `hasil.json`.

Test: `modules/inaproc/tests/test_cli.py` (parse argumen + dispatch dengan mock).

### 9. `modules/inaproc/login.py`

Fallback interaktif saja (dipakai bila INAPROC minta OTP/captcha). Buka
`https://penyedia.inaproc.id/auth/signin?callbackUrl=/products/tkdn` dengan
headless=False **di mesin yang punya layar**, tunggu user menyelesaikan login
penyedia INAPROC secara manual, tunggu navigasi ke `/products/tkdn`, lalu
`context.storageState(path=...)`.

Catatan operasional: fallback ini tidak bisa dipakai bila BE berjalan di server
tanpa display. Untuk sekarang aplikasi ditargetkan lokal, jadi ini aman.

Koneksi INAPROC normal dilakukan dari Vue lewat `POST /api/login`, tidak lewat file ini.

Test: `modules/inaproc/tests/test_login.py` dengan Playwright fake (tanpa browser sungguhan).

### 10. `modules/inaproc/auth.py`  (inti koneksi INAPROC headless)

Koneksi INAPROC normal: `connect_inaproc(email, password, session_path)` membuka Playwright
headless, isi form signin INAPROC, submit, tunggu redirect ke `/products/tkdn`,
simpan `storageState.json`, kembalikan ringkasan. Fungsi ini tidak membuat akun
atau sesi aplikasi.


- `connect_inaproc(email, password, session_path)` -> jalankan Playwright headless, simpan state.
- `muat_storage_state(path)` -> dict (validasi struktur cookies/origins).
- `validasi_sesi(state)` -> memastikan ada cookie/localStorage sesi INAPROC yang
  bisa dipakai Playwright; tidak membaca nilai sesi.
- `AuthError` untuk state hilang/state tidak valid/kredensial salah.

Test: `modules/inaproc/tests/test_auth.py` memakai state dummy tanpa nilai sesi asli.

### 11. `modules/inaproc/documents/contoh_session.json.example`

Contoh struktur `storageState.json` **tanpa nilai asli** (cookie dummy), sebagai
referensi cara menyiapkan sesi. File aslinya di-gitignore.

### 12. `.gitignore` (update)

Tambahkan pola untuk menyembunyikan file sesi, cache, dan hasil:

```
modules/inaproc/*.session.json
modules/inaproc/storageState.json
modules/inaproc/data/
modules/inaproc/output/
```

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
| `modules/inaproc/auth.py` | `connect_inaproc(email, password, session_path)` -> dict state |
| `modules/inaproc/auth.py` | `muat_storage_state(path)`, `validasi_sesi(state)` |
| `modules/inaproc/login.py` | Hanya fallback koneksi INAPROC interaktif (OTP/captcha), headless=False |
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

### Ringkasan endpoint

| Method | Path | Fungsi |
| --- | --- | --- |
| `POST` | `/api/login` | Buka sesi INAPROC via Playwright headless, simpan `storageState.json` (bukan login aplikasi) |
| `POST` | `/api/logout` | Hapus sesi tersimpan |
| `GET` | `/api/session` | Status sesi INAPROC tanpa membocorkan isi state |
| `GET` | `/api/search` | Cari di cache lokal (filter, sort, pagination) |
| `GET` | `/api/collect/preview` | Hitung dampak rentang sebelum dijalankan |
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
- `/api/search` dan `/api/export` murni membaca cache lokal tanpa sesi.
- `/api/status` dan `/api/collect/cancel` hanya membaca/mengubah job di memori.

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

Pencarian hanya ke cache lokal (tidak memanggil INAPROC). `q` mencocokkan semua
kolom teks (nomor, jenis, merek, tipe, uraian, standard) secara case-insensitive.
Tanpa `q`, endpoint tetap mengembalikan baris cache yang cocok dengan filter lain.

### `GET /api/collect/preview`

Menghitung dampak rentang sebelum dijalankan, supaya user tahu berapa nomor yang
akan diproses dan berapa yang dilewati karena sudah ada di cache.

Contoh panggilan:

```
GET /api/collect/preview?nomor=11469%2FSJ-IND.8%2FE-TKDN%2F7%2F2025&start=1000&end=2000
```

Endpoint ini **tidak** memanggil INAPROC dan tidak memerlukan sesi INAPROC; ia
hanya membaca `tkdn_checks` untuk menghitung `sudah_ada`.

Query params: `nomor` (nomor contoh lengkap), `start`, `end`, `delay_min`
(opsional, default `1.0`), `delay_max` (opsional, default `3.0`).

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
| `upstream_timeout` | 504 | INAPROC tidak merespons |
| `upstream_error` | 502 | Halaman INAPROC gagal dimuat atau markup tak dikenali |

## Skema Cache SQLite

File: `modules/inaproc/data/tkdn.db` (di-gitignore).

```sql
CREATE TABLE IF NOT EXISTS tkdn_rows (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    number          TEXT    NOT NULL,
    specification_id TEXT,
    product_type    TEXT,
    brand           TEXT,
    type            TEXT,
    description     TEXT,
    standard        TEXT,
    value           REAL,
    hs              TEXT,
    fetched_at      TEXT    NOT NULL,
    UNIQUE(number, specification_id, brand, type, description)
);

CREATE INDEX IF NOT EXISTS idx_tkdn_brand  ON tkdn_rows(brand);
CREATE INDEX IF NOT EXISTS idx_tkdn_number ON tkdn_rows(number);

CREATE TABLE IF NOT EXISTS tkdn_checks (
    number      TEXT PRIMARY KEY,
    status      TEXT NOT NULL,          -- found | empty | error
    checked_at  TEXT NOT NULL,
    error_msg   TEXT
);
```

`tkdn_checks` menyimpan status per nomor supaya nomor kosong tidak di-request
ulang saat collect diulang. Baris `error` tetap disimpan untuk diagnosa, tetapi
collect berikutnya mencoba ulang nomor itu. Refresh manual menghapus baris nomor
tersebut dari kedua tabel.

## Catatan Keputusan yang Sudah Ditutup

- **Stack**: Python + FastAPI (BE) dan Vue 3 + TS + Bootstrap 5 + Vite + Pinia (FE). Bukan Elysia/Bun.
- **Koneksi INAPROC**: dari form Vue (`POST /api/login`), BE Playwright headless,
  simpan `storageState.json`, lalu buka halaman TKDN dengan state itu. Ini bukan
  login aplikasi. Fallback interaktif hanya untuk OTP/captcha.
- **Sumber data**: halaman `penyedia.inaproc.id/products/tkdn?keyword=...` via
  Playwright + parser HTML. **Tanpa GraphQL dan tanpa endpoint internal.**
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
9. **Ekspor & fitur tabel**: **semua** disetujui: export CSV, export JSON, filtering, sorting, dan pagination.
10. **Sumber data final**: **HTML scrape via Playwright**. Endpoint GraphQL yang
    pernah ditemukan **tidak dipakai**, sesuai keputusan user. Backend membuka
    halaman TKDN, menunggu tabel render, lalu mem-parse HTML-nya.
11. **Mulai implementasi TDD**: menyusul setelah rencana ini final.

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
| `test_cache.py` | `test_simpan_dan_baca` | insert lalu query balik |
| `test_cache.py` | `test_dedup_baris` | insert sama 2x -> 1 baris |
| `test_cache.py` | `test_filter_brand` | filter merek case-insensitive |
| `test_cache.py` | `test_filter_nilai_minimum` | `value >= 30` |
| `test_cache.py` | `test_sort_dan_pagination` | sort + limit/offset |
| `test_cache.py` | `test_cek_status_nomor` | `tkdn_checks` found/empty/error; status error dianggap belum final |
| `test_cache.py` | `test_refresh_hapus_nomor` | refresh menghapus baris nomor itu |
| `test_collector.py` | `test_loop_rentang` | 1000-1002 -> 3 nomor diproses |
| `test_collector.py` | `test_template_user` | template dari user dipakai apa adanya |
| `test_collector.py` | `test_rentang_tidak_hardcode` | start/end 5-7 memakai nilai user |
| `test_collector.py` | `test_skip_found_empty` | nomor found/empty dilewati |
| `test_collector.py` | `test_retry_error` | nomor error tidak dilewati, diproses lagi |
| `test_collector.py` | `test_force_ulang` | `force=True` memproses ulang |
| `test_collector.py` | `test_cancel_event` | cancel berhenti setelah nomor aktif |
| `test_collector.py` | `test_progres_terupdate` | hitungan done/found/empty/error |
| `test_api.py` | `test_search_dari_cache` | tidak memanggil scraper |
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
| Koneksi INAPROC headless (`auth.py`) | 1 jam (termasuk handling error) |
| Backend inti (`spt`, `auth`, `client`, `cache`, `exporter`) | 1 sesi |
| Backend orkestrasi (`collector`, `api`, `schemas`) | 1 sesi |
| Frontend (Vue + Pinia + Vitest) | 1 sesi |
| Smoke test + perbaikan | 30-60 menit |
| **Total** | **2-3 sesi kerja** |

Biaya waktu collect: 1000 nomor dengan delay 1-3 detik = 25-50 menit per job.
Nomor yang sudah pernah dicek tidak diulang, jadi job berikutnya jauh lebih cepat.

## Definisi Selesai (Definition of Done)

Modul dianggap selesai bila semua ini terpenuhi.

**Backend**

- [ ] `python -m unittest` dari root repo hijau, termasuk test modul ini.
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
- [ ] Cache tidak menyimpan duplikat saat nomor yang sama diambil ulang.
- [ ] Export CSV terbuka benar di Excel (delimiter, encoding UTF-8).
- [ ] Tidak ada isi `storageState.json`/kredensial di file yang di-track git.

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
- [ ] Tampilan tetap rapi di lebar 360 px dan 1440 px.
- [ ] `prefers-reduced-motion: reduce` mematikan animasi.

**Dokumentasi**

- [ ] `rencana.md` dan `tugas.md` tidak saling bertentangan.
- [ ] Perintah menjalankan BE dan FE tertulis di README modul.

## Runbook Verifikasi (setelah sesi INAPROC terhubung)

Dijalankan setelah FE + `POST /api/login` berfungsi. Tidak perlu tool tambahan,
cukup aplikasi yang sudah jalan.

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

## .gitignore untuk modul ini

Tambahkan (tanpa menyentuh aturan modul lain):

```
modules/inaproc/storageState.json
modules/inaproc/*.session.json
modules/inaproc/data/
modules/inaproc/output/
```

Alasan: `storageState.json` berisi cookie/localStorage sesi INAPROC aktif;
`data/` berisi cache SQLite hasil scraping; `output/` berisi ekspor CSV/JSON.

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

> **Status dokumen:** ini catatan tugas awal (analisa + ide solusi). Rencana
> final yang dipakai untuk implementasi ada di `rencana.md`: DB dicek lebih
> dulu, dan Playwright hanya dipakai untuk nomor SPT yang belum ada di DB.
> Tabel HTML di-parse, GraphQL tidak dipakai. Hasil disimpan ke **MySQL**,
> sedangkan CSV/JSON hanya untuk ekspor.
>
> **API resmi:** INAPROC API Gateway (`data.inaproc.id`) direncanakan sebagai
> jalur terpisah untuk data katalog/pengadaan (read-only, Bearer token). API ini
> **bukan** sumber TKDN; pencarian nomor SPT TKDN tetap lewat Playwright ke
> portal penyedia. Detail ada di `rencana.md` bagian "Integrasi INAPROC API
> Gateway Resmi".
>
> **Batas operasi:** aplikasi ini hanya membaca data INAPROC. Tidak ada
> insert/update/delete produk, stok, harga, atau data penyedia ke INAPROC.
> Penulisan hanya terjadi di MySQL lokal sebagai cache hasil pencarian.
>
> **Istilah:** semua kata "login" di dokumen ini merujuk ke **login akun penyedia
> INAPROC**, bukan login/akun aplikasi yang kita buat. Aplikasi ini tidak punya
> sistem user sendiri.

saya punya data nomor surat spt ini : 11469/SJ-IND.8/E-TKDN/7/2025

jika di buka pake login penyedia di web inaproc maka akan lookup ke data seperti sy screenshoot,
saya dapat jenis produk, merek, tipe, uraian produk, standard dan nilai.

jika saya mencoba nomor berurutan
11469/SJ-IND.8/E-TKDN/7/2025
11468/SJ-IND.8/E-TKDN/7/2025
11467/SJ-IND.8/E-TKDN/7/2025

maka akan tampil 1-1

nah akan lambat kan kalau 1-1, bisa nggak kita buat tools sederhana untuk mendapatkan semua data yang kita butuhkan.. untuk mencari produk tertentu.. misal dari nomor 1000-2000 itu produk dan merek apa aja..

contoh url : https://penyedia.inaproc.id/products/tkdn?keyword=11469%2FSJ-IND.8%2FE-TKDN%2F7%2F2025

isi dari foto
**URL**
`penyedia.inaproc.id/products/tkdn?keyword=11469%2FSJ-IND.8%2FE-TKDN%2F7%2F2025`

**Keyword (Bagian yang Disorot)**

* **Format URL:** `11469%2FSJ-IND.8%2FE-TKDN%2F7%2F2025`

* **Format Teks (Decoded):** `11469/SJ-IND.8/E-TKDN/7/2025`

**Header**
INAPROC - Manajemen Penyedia
TKDN

**Tabel Data**

| Jenis Produk | Merek | Tipe | Uraian Produk | Standard | Nilai |
| --- | --- | --- | --- | --- | --- |
| Monitor | acer | V | 23.8 Inchi | - | 33.39 |

## analisa dan solusi

### 1. Analisa

**Apa yang sebenarnya terjadi**

- Data TKDN di INAPROC tidak bisa diakses publik: halaman `penyedia.inaproc.id/products/tkdn?keyword=...` hanya bisa dibuka setelah login sebagai penyedia. Jadi setiap request harus membawa sesi penyedia INAPROC (cookie) yang masih aktif.
- Endpoint tersebut adalah **pencarian by keyword**, bukan endpoint detail per nomor SPT. Nomor `11469/SJ-IND.8/E-TKDN/7/2025` dipakai sebagai `keyword`, lalu server mencocokkan data SPT/TKDN yang terkait dan mengembalikan hasil dalam bentuk tabel.
- Format nomor bersifat **berurutan** (`11468`, `11467`, ...). Artinya bisa di-loop dengan mengubah satu komponen angka saja. Ini peluang otomasi: kita tidak perlu tahu nomor dari sumber lain, cukup rentang angka.
- Kalau dicek satu per satu lewat browser, setiap nomor butuh: buka URL -> tunggu render -> baca tabel -> catat manual. Untuk 1000 nomor (1000-2000) ini sangat lambat dan rawan salah catat.

**Masalah yang harus dipecahkan**

1. **Sesi penyedia INAPROC**: login ke INAPROC sekali, lalu pakai cookie/session yang sama untuk seluruh request. Tidak boleh login ulang tiap nomor. Ini bukan login aplikasi.
2. **Bukan semua nomor ada**: dari rentang 1000-2000, sebagian besar kemungkinan kosong atau bukan milik kita. Tool harus bisa membedakan "tidak ada data" vs "gagal request".
3. **Rate limit / perilaku bot**: INAPROC bisa membatasi request berulang terlalu cepat. Akses harus berirama manusia (delay + jitter), bukan serial cepat.
4. **Struktur respons**: halaman adalah HTML dinamis (Vue/JS). Data tabel bisa jadi:
   - sudah ada di HTML saat load (server-rendered), atau
   - baru muncul setelah JavaScript selesai merender tabel.
   Keduanya beda cara ekstraksinya.
5. **Validasi data**: kolom yang diminati: Jenis Produk, Merek, Tipe, Uraian Produk, Standard, Nilai. Perlu dipastikan tabel yang terbaca benar-benar hasil pencarian, bukan tabel kosong/placeholder.

### 2. Solusi

**Bentuk tool: skrip pengumpul berbasis sesi (bukan scraper buta)**

Alur kerja yang diusulkan:

```
[login INAPROC sekali, simpan storageState.json]
        |
        v
[user cari nomor SPT] -> [cek tkdn_checks di MySQL]
   |-- sudah found/empty -> jawab dari DB (tanpa scraping)
   |-- belum ada/error  -> scraping
        |
        v
[loop nomor pilihan user yang belum ada di DB]
   |-- GET /products/tkdn?keyword=<nomor>
   |-- delay acak 1-3 detik
   |-- parse HTML tabel yang sudah dirender
   |-- jika ada tabel -> ambil 6 kolom -> simpan ke MySQL
   |-- jika kosong -> tandai "tidak ada data" di MySQL
        |
        v
[FE: cari, filter, sort, pagination dari MySQL]
        |
        v
[export CSV/JSON bila perlu]
```

**Tahap implementasi**

1. **Dapatkan sesi penyedia INAPROC**
   - Login ke akun penyedia INAPROC manual lewat browser sekali, lalu ekspor cookie (atau simpan storage state) ke file lokal yang **tidak di-commit**. Ini bukan login aplikasi.
   - Skrip membaca file sesi ini dan memakai cookie yang sama untuk semua request.
   - Alternatif lebih rapi: pakai Playwright dengan `storageState.json` (`browser.newContext({ storageState })`), sehingga tetap terlihat seperti browser asli.

2. **Deteksi sumber data (penting, lakukan dulu sebelum loop besar)**
   - Buka 1 nomor contoh dengan DevTools -> tab Elements.
   - Tunggu tabel render, lalu catat selector tabel, baris data, dan header kolom.
   - Jalur yang dipakai adalah parse HTML tabel yang sudah dirender; endpoint internal tidak dipakai.
   - Contoh selector awal: `table` dengan header `Jenis Produk | Merek | Tipe | ...`.

3. **Loop rentang nomor dengan aman**
   - Bangun nomor: `<n>/SJ-IND.8/E-TKDN/7/2025`, dengan `n` dari rentang yang dipilih user.
   - Encode keyword dengan `encodeURIComponent` (slash jadi `%2F`) persis seperti contoh URL.
   - **Tambahkan delay acak** (mis. 1-3 detik) dan batasi retry dengan backoff bila dapat 429/5xx. Jangan parallel request banyak-banyak; ini memicu block.
   - Simpan hasil per nomor seketika ke MySQL, jadi kalau proses berhenti di tengah bisa dilanjutkan.
   - Nomor yang sudah final (`found`/`empty`) di `tkdn_checks` dilewati; hanya nomor baru atau `error` yang di-scrape.

4. **Ekstrak & simpan**
   - Kolom yang diambil: `Jenis Produk`, `Merek`, `Tipe`, `Uraian Produk`, `Standard`, `Nilai`.
   - Simpan ke MySQL (`tkdn_rows` + `tkdn_checks`), dengan `status` = `found` / `empty` / `error` supaya mudah difilter dan nomor yang sudah dicek tidak diulang.
   - CSV/JSON tidak dipakai sebagai penyimpanan utama; keduanya hanya format ekspor.

5. **Cari produk tertentu**
   - Setelah data masuk MySQL, pencarian produk/merek cukup query database (mis. cari merek `acer`, atau `Nilai > 30`), jauh lebih cepat daripada query server berulang.

### 3. Catatan penting

- **Jangan hardcode kredensial** di skrip/dokumentasi. Kredensial yang dimaksud adalah akun penyedia INAPROC. Sesi INAPROC cukup disimpan lokal dan di-gitignore.
- **Patuhi batas wajar**: rentang 1000 nomor dengan delay ~2 detik sekitar 30-50 menit. Itu masih jauh lebih cepat daripada manual dan tidak membebani server.
- **Hanya untuk data yang boleh diakses akun Anda.** Tool ini memakai hak akses penyedia yang sah, bukan bypass.
- **Validasi kecil dulu**: jalankan untuk 10 nomor pertama, cek isi MySQL benar, baru jalankan rentang penuh.
- **MySQL wajib**: backend memakai `pymysql`; tidak ada fallback ke SQLite atau file database lokal. Bila database mati, API memberi error `503 db_unavailable`.
- **DB-first**: nomor SPT yang sudah ada di DB tidak di-scrape lagi. Scraping hanya untuk data yang belum ada atau status `error`.

### 4. Rekomendasi singkat

Mulai dengan **investigasi DOM** untuk 1 nomor guna mengunci selector tabel. Setelah itu bangun alur: cek DB dulu -> scraping hanya bila nomor belum ada -> parse HTML -> simpan ke MySQL -> FE mencari dari database. Pencarian kedua untuk nomor yang sama tidak menyentuh INAPROC lagi. Dengan begitu, mencari "produk dan merek apa saja di rentang 1000-2000" cukup lewat satu pencarian di FE, bukan mengetik 1000 kali di browser.

### Tindakan API resmi yang perlu diurus

- Daftar/verifikasi akun di `akun.inaproc.id`.
- Ajukan role integrator melalui **Manajemen Peran** sesuai pilihan yang muncul
  di portal.
- Siapkan surat permohonan, NPWP, PIC teknis, use case, dan public egress IP.
- Buat token hanya untuk scope E-Katalog V6 dan master program yang benar-benar
  dipakai; estimasi request harian diisi realistis.
- Setelah disetujui, simpan token di environment variable backend saja dan aktifkan
  `INAPROC_API_ENABLED` secara bertahap.

# Accurate Human Automation

## Tujuan

Skill ini dipakai setiap kali agent menjalankan otomasi Accurate.
Tujuannya adalah membuat interaksi berjalan seperti manusia biasa:
terbaca, berjeda, dan tidak terlihat seperti aksi bot.

## Prinsip Wajib

- Analisa Accurate WAJIB menggunakan MCP REA atau CLI REA
  `capture-browser-scenario` untuk observasi berbasis browser.
- Gunakan browser headless bila memungkinkan, tetapi jangan mempercepat
  interaksi karena berjalan di background.
- Jangan menjalankan aksi beruntun tanpa jeda.
- Jangan langsung mengisi form sebelum halaman stabil.
- Jangan retry cepat. Batasi maksimal tiga percobaan dan beri jeda acak.
- Jangan menulis email atau password asli ke skenario, log, capture,
  skill, atau dokumentasi.
- Ambil kredensial hanya dari `ACCURATE_EMAIL` dan `ACCURATE_PASSWORD`.
- Capture hanya data yang dibutuhkan. Hindari DOM/network besar tanpa alasan.

## Konfigurasi Dasar

Gunakan Chrome yang terpasang dan mode headless. Viewport 1440x900,
locale `id-ID`, dan timezone `Asia/Makassar`.

## Alur Human-Paced

1. Buka URL Accurate.
2. Tunggu form login stabil 2-5 detik.
3. Isi email, lalu beri jeda 500-1.500 ms.
4. Isi password, lalu beri jeda 800-2.000 ms.
5. Klik tombol `Masuk`.
6. Tunggu halaman `/manage` stabil 5-10 detik.
7. Jika dialog 2FA muncul, tunggu 1-3 detik, lalu klik `Nanti Saja`.
8. Diamkan daftar perusahaan 3-8 detik.
9. Klik kartu perusahaan yang dituju.
10. Tunggu tab atau jendela perusahaan terbuka.
11. Buka halaman tujuan setelah sesi perusahaan aktif.

## Selector Teruji

| Elemen | Selector |
| --- | --- |
| Email | `getByRole('textbox', { name: 'Email atau No Handphone Akun Accurate Anda' })` |
| Password | `#password` |
| Tombol Masuk | `getByRole('button', { name: 'Masuk' })` |
| Dialog 2FA | `getByRole('button', { name: 'Nanti Saja' })` |
| Kartu perusahaan | `div.cursor-pointer:has(h3:text-is('cy'))` |

Jangan memakai locator role `Password` karena Playwright menemukan dua
elemen: `#password` untuk login dan `#registerPassword` untuk registrasi.

## Penanganan Dialog 2FA

Dialog 2FA tidak selalu muncul. Jangan menjadikan tombol `Nanti Saja`
sebagai satu-satunya kondisi tunggu.

1. Tunggu 5-10 detik setelah login.
2. Tekan `Escape` pada `body`.
3. Tunggu kartu perusahaan muncul.
4. Klik `Nanti Saja` hanya bila dialog masih terlihat.

## Membuka Perusahaan

Kartu perusahaan memakai handler Knockout
`click:$root.selectOpenedDatabase`. Handler dapat memanggil `window.open`,
sehingga URL root bisa tetap di `/manage`. Jangan anggap gagal hanya karena
URL root tidak berubah. Tunggu popup, tab baru, atau gunakan URL langsung
hasil data perusahaan.

Ambil ulang ID perusahaan dari halaman `/manage` saat otomasi dijalankan.
Jangan mengandalkan ID dari dokumentasi.

## Pola Jeda

Jangan memakai delay tetap untuk semua run. Variasikan jeda manusia:

| Aksi | Jeda |
| --- | --- |
| Sebelum mengisi email | 1-3 detik |
| Setelah mengisi email | 500-1.500 ms |
| Setelah mengisi password | 800-2.000 ms |
| Sebelum klik `Masuk` | 300-1.000 ms |
| Setelah login | 5-10 detik |
| Sebelum klik perusahaan | 3-8 detik |
| Sebelum retry | 10-30 detik |

## Interaksi Natural

Untuk input yang perlu terlihat seperti diketik manusia:

- Gunakan `pressSequentially` pada Playwright dengan delay acak 75-180 ms
  per karakter.
- Gunakan `fill` hanya untuk password atau ketika runner tidak mendukung
  pengetikan per karakter.
- Jangan memakai shortcut DOM atau injeksi nilai langsung untuk
  menghindari alur aplikasi.

## Checklist Sebelum Menjalankan

- [ ] Kredensial dibaca dari `.env`.
- [ ] Browser headless.
- [ ] Tidak ada delay nol antar aksi.
- [ ] Retry maksimal tiga kali.
- [ ] Dialog 2FA tidak dianggap wajib muncul.
- [ ] Popup atau tab baru ditunggu dengan benar.
- [ ] Tidak ada kredensial pada hasil capture atau log.
- [ ] Skenario hanya menyimpan data yang benar-benar diperlukan.

## Ekstraksi Data Tabel ke `data.json`

Setiap menu Accurate yang punya tabel/grid data harus diekstrak dan
disimpan sebagai `data.json` di folder dokumentasi menu tersebut
(`modules/accurate/<menu>/data.json`). Data ini adalah data aktual yang tampil di
tabel, bukan definisi kolom atau struktur form.

### Pola Grid Accurate

Accurate memakai SlickGrid yang merender baris secara virtual. Artinya
DOM hanya berisi baris yang terlihat di viewport. Untuk mendapat semua
baris, lakukan scroll bertahap dan kumpulkan baris yang terlihat di
setiap iterasi.

### Langkah Ekstraksi

1. Login dan buka perusahaan sesuai alur human-paced.
2. Navigasi ke hash menu target, contoh:
   `#accurate__general-ledger__glaccount`.
3. Tunggu konten module selesai dimuat minimal 15-30 detik.
4. Klik tombol `btnToggleList` dan `btnRefresh` bila perlu untuk memicu
   load data.
5. Scroll grid secara bertahap menggunakan Playwright:

```javascript
await page.evaluate(() => {
  const canvas = document.querySelector('.grid-canvas');
  if (canvas) {
    const viewport = canvas.closest('.slick-viewport');
    if (viewport) viewport.scrollTop += 500;
  }
});
```

6. Setiap iterasi scroll, kumpulkan baris yang terlihat:

```javascript
const rows = await page.evaluate(() => {
  const result = [];
  document.querySelectorAll('.slick-row').forEach(row => {
    const cells = [];
    row.querySelectorAll('.slick-cell').forEach(cell => {
      cells.push(cell.textContent.trim());
    });
    if (cells.length > 0 && cells.some(c => c)) {
      result.push(cells);
    }
  });
  return result;
});
```

7. Deduplikasi baris berdasarkan kolom pertama (kode/ID) karena scroll
   dapat menghasilkan baris yang sama muncul lebih dari sekali.
8. Stop scroll ketika jumlah baris unik tidak bertambah lagi.
9. Simpan hasil ke `modules/accurate/<menu>/data.json` dengan struktur:

```json
{
  "menu": "Nama Menu",
  "module": "#accurate__module__name",
  "captured_at": "ISO-8601 timestamp",
  "company": "nama perusahaan",
  "database_id": 1234567,
  "table": {
    "columns": ["Kolom 1", "Kolom 2"],
    "record_count": 95,
    "records": [
      {"kolom_1": "nilai", "kolom_2": "nilai"}
    ]
  },
  "status": "loaded"
}
```

### Menentukan Kolom Tabel

Kolom tabel asli bisa ditemukan dari script module dengan mencari
`columnDef` di DOM. Contoh untuk Akun Perkiraan:

```javascript
self._init({
  columnDef: [
    {"key":"noWithIndent","label":"Kode Perkiraan","visible":true,...},
    {"key":"nameWithIndent","label":"Nama","visible":true,...},
    {"key":"accountTypeName","label":"Tipe Akun","visible":true,...},
    {"key":"balance","label":"Saldo","visible":true,...}
  ]
});
```

Gunakan hanya kolom dengan `"visible": true` untuk `data.json`.

### Jika Tabel Kosong

Bila grid menampilkan "Belum ada data" atau jumlah baris 0, tetap buat
`data.json` dengan `record_count: 0` dan `records: []`. Jangan mengisi
dengan data dari sumber lain atau asumsi.

### Contoh Script Playwright

```python
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def extract_table_data(page, output_path):
    all_rows = []
    seen_codes = set()
    prev_count = 0

    for scroll_iter in range(30):
        rows = await page.evaluate("""
            () => {
                const result = [];
                document.querySelectorAll('.slick-row').forEach(row => {
                    const cells = [];
                    row.querySelectorAll('.slick-cell').forEach(cell => {
                        cells.push(cell.textContent.trim());
                    });
                    if (cells.length > 0 && cells.some(c => c)) {
                        result.push(cells);
                    }
                });
                return result;
            }
        """)

        for r in rows:
            code = r[0].strip() if r else ''
            if code and code not in seen_codes:
                seen_codes.add(code)
                all_rows.append(r)

        if len(all_rows) == prev_count and scroll_iter > 0:
            break
        prev_count = len(all_rows)

        await page.evaluate("""
            () => {
                const canvas = document.querySelector('.grid-canvas');
                if (canvas) {
                    const viewport = canvas.closest('.slick-viewport');
                    if (viewport) viewport.scrollTop += 500;
                }
            }
        """)
        await asyncio.sleep(1)

    output_path.write_text(
        json.dumps(all_rows, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return all_rows
```

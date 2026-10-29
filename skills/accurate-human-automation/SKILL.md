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
tabel — **bukan** tempat untuk informasi kolom, filter, atau struktur form.

### Isi `data.json`

`data.json` hanya berisi record aktual yang tampil di tabel:

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

Aturan:

- `columns` hanya sebagai penanda urutan kolom di `records`, bukan
  dokumentasi struktur.
- `records` berisi baris data aktual. Jika tabel kosong, `record_count: 0`
  dan `records: []`.
- Informasi kolom, filter, form, dan tombol **dilarang** masuk
  `data.json`. Semua itu milik `<menu>.json` dan `<menu>.md`.
- Jangan menulis `filters`, `inputs`, `buttons`, atau `columns` sebagai
  dokumentasi terpisah di dalam `data.json`.

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
9. Simpan hasil ke `modules/accurate/<menu>/data.json` dengan struktur di atas.

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

### Menentukan Kolom Tabel (untuk urutan kolom di `records`)

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

Gunakan hanya kolom dengan `"visible": true` sebagai urutan kolom di
`records`. Definisi lengkapnya tetap disimpan di `<menu>.json`.

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

## Analisa Form Input Data (Data Baru)

Setiap menu Accurate yang punya tombol **Data Baru** harus dianalisa juga
form inputnya, bukan hanya daftar dan filter. Markup form **sudah ada di
DOM** meskipun form belum dibuka, sehingga bisa diekstrak dari capture
tanpa klik tambahan.

### Pola Capture Modul dan Form

- Gunakan `capture-browser-scenario` mode `connect` saat login manual sudah
  aktif di Chrome debugging.
- Ambil ulang `target_id` dari endpoint `/json` sebelum setiap batch.
- Buka grup menu, klik submenu, lalu klik tab `#module-<module-key>` bila
  modul belum aktif.
- Modul transaksi umumnya langsung membuka form Data Baru; jangan menganggap
  capture gagal hanya karena `button[name='btnAdd']` berada di daftar belakang
  dan tidak dapat diklik.
- Scope selector tombol ke modul aktif:
  `#module-<module-key> button[name='btnAdd']`.
- Tutup modul sebelumnya lewat `a.aol-main-tab-close` pada tab terkait agar
  tidak ada dua modul menumpuk.
- Untuk form, cukup capture DOM setelah modul stabil 8-12 detik. Jangan
  memakai screenshot sebagai bukti analisa.
- Jika modul berbasis iframe (misalnya Accurate Store), iframe biasanya tidak
  muncul sebagai CDP target terpisah. Ambil URL iframe dari atribut `src`,
  lalu buka URL tersebut langsung sebagai `start_url` pada skenario REA.

### Struktur DOM Form

```text
div.module-form.tabbing-module
├── div.module-tab                    ← daftar tab form (Data Baru, dll)
└── div.general-tab-content           ← 1 frame per tab
    ├── div.span12                    ← judul section (Data Pribadi, dst)
    └── div.row.no-margin             ← 1 baris form
        ├── div.span4 > label         ← label field (bisa class "required")
        └── div.span7/span5           ← input (bisa lebih dari 1)
```

### Aturan Pemetaan Label ke Input

1. Jangan pasangkan label dengan sibling terdekat saja — beberapa baris
   punya **lebih dari satu input** (contoh: `salutation` + `name`,
   `startMonthPayment` + `startYearPayment`, `btnManualNumber` +
   `typeAutoNumber`).
2. Naik ke `div.row` terdekat dari label, lalu kumpulkan **semua**
   `input/select/textarea` di dalam row tersebut.
3. Deduplikasi berdasarkan `name` agar field yang sama tidak tercatat
   dua kali.
4. Field wajib ditandai class `required` pada label.
5. Input tanpa `name` bisa dirujuk lewat binding `formData.<field>` di
   atribut `data-bind`.

### Klasifikasi Tipe Input

Tipe input ditentukan dari binding Knockout pada `data-bind`:

| Binding | Tipe |
|---------|------|
| `metroDatepicker` | date |
| `metroLookup` | lookup (cari/pilih dari API) |
| `metroNumberfield` | number |
| `metroCombobox` atau `select` | select |
| `metroCheckbox` atau `type=checkbox` | checkbox |
| `textarea` | textarea |
| lainnya | text |

Opsi `select` diambil dari elemen `<option>` di dalamnya.

### Output Dokumentasi

Simpan hasil analisa form ke dua tempat:

1. `modules/accurate/<menu>/<menu>.md` — section baru `## Form Data
   Baru (...)` di atas section daftar, berisi tabel per tab/section
   dengan kolom: Field, Input, Tipe, Wajib, Keterangan.
2. `modules/accurate/<menu>/<menu>.json` — key baru `"form"` berisi
   struktur `tabs[].sections[].fields[].inputs[]`. Agar file tidak
   membengkak, opsi panjang disimpan sebagai `option_count` +
   `options_ref` yang merujuk ke key di `selects`.

### Contoh Script Ekstraksi

```python
from bs4 import BeautifulSoup
from pathlib import Path
import json

html = Path("dom_capture.html").read_text(encoding="utf-8")
soup = BeautifulSoup(html, "html.parser")
module = next(d for d in soup.find_all("div", id=True)
              if d["id"].startswith("accurate__company__employee--")
              and "module-form" in " ".join(d.get("class", [])))

def classify(inp):
    bind = " ".join((inp.get("data-bind") or "").split())
    if "metroDatepicker" in bind: return "date"
    if "metroLookup" in bind: return "lookup"
    if "metroNumberfield" in bind: return "number"
    if inp.name == "select" or "metroCombobox" in bind: return "select"
    if "metroCheckbox" in bind or inp.get("type") == "checkbox": return "checkbox"
    if inp.name == "textarea": return "textarea"
    return "text"

entries = []
seen = set()
for frame in module.find_all("div", class_="general-tab-content"):
    section = None
    for el in frame.find_all(True):
        cls = " ".join(el.get("class", []) or [])
        if el.name == "div" and "span12" in cls:
            section = " ".join(el.get_text().split())
            continue
        if el.name != "label" or el.find_parent("div", class_="input-control"):
            continue
        label = " ".join(el.get_text().split())
        row = el.find_parent("div", class_="row")
        if not label or row is None:
            continue
        inputs = []
        for inp in row.find_all(["input", "select", "textarea"]):
            name = inp.get("name") or inp.get("id") or ""
            if not name or name in seen:
                continue
            seen.add(name)
            opts = ([o.get_text(strip=True) for o in inp.find_all("option")]
                    if inp.name == "select" else [])
            inputs.append({"name": name, "kind": classify(inp), "options": opts})
        if inputs:
            entries.append({"section": section, "label": label,
                            "required": "required" in cls, "inputs": inputs})

Path("form_map.json").write_text(
    json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
```

### Checklist Analisa Form

- [ ] Semua tab form teridentifikasi (frame `general-tab-content`).
- [ ] Semua section di dalam tab tercatat (div `span12`).
- [ ] Baris multi-input tidak terpecah (label dipetakan ke semua input
      dalam row yang sama).
- [ ] Field wajib ditandai berdasarkan class `required` pada label.
- [ ] Opsi select diekstrak dan dirujuk dengan `options_ref` di JSON.
- [ ] Input tanpa `name` dirujuk lewat binding `formData.<field>`.

# Hasil Analisa REA Accurate

## Ringkasan

REA berhasil dipakai untuk mengotomasi halaman Accurate menggunakan
`capture-browser-scenario`. Skenario dijalankan dari `D:\learns\random`
melalui CLI `rea@6.8.0` dengan Chrome yang sudah terpasang di sistem.

Hasil utamanya:

- Login berhasil menggunakan email dan password.
- Halaman setelah login berpindah dari `https://account.accurate.id/` ke
  `https://account.accurate.id/manage`.
- Dialog aktivasi 2FA muncul pada beberapa percobaan dan bisa ditutup
  dengan tombol `Nanti Saja` atau tombol `Escape`.
- Daftar perusahaan menampilkan kartu `cy` dengan label `CC TRIAL`.
- Klik pada kartu `cy` berhasil, tetapi halaman aktif tetap berada di
  `/manage` karena aplikasi membuka perusahaan di jendela atau tab baru.

## Konfigurasi Browser

Skenario memakai konfigurasi berikut:

```yaml
browser:
  mode: launch
  executable_path: C:\Program Files\Google\Chrome\Application\chrome.exe
  headless: true
environment:
  viewport:
    width: 1440
    height: 900
  locale: id-ID
  timezone: Asia/Makassar
```

Mode `headless` sudah dipakai agar browser berjalan di background dan tidak
lagi membuka jendela Chrome.

## Alur Login

URL awal yang dipakai adalah URL Accurate Journal Voucher:

```text
https://zeus.accurate.id/accurate/?_dsi=R1c2Z21EVi82WmpqMEdVSHJ0ZFpMZ1ZTR1lrdnZCSVE0QitUa0dBWVNBYlRMSDVwb3RKNjJBZDVNL2NseS83TQ==#accurate__general-ledger__journal-voucher
```

Setelah dibuka, Accurate mengarahkan halaman ke:

```text
https://account.accurate.id/
```

Elemen form login yang terdeteksi:

| Elemen | Locator |
| --- | --- |
| Email atau No Handphone | `getByRole('textbox', { name: 'Email atau No Handphone Akun Accurate Anda' })` |
| Password | `#password` |
| Tombol Masuk | `getByRole('button', { name: 'Masuk' })` |

Urutan aksi yang berhasil:

1. Tunggu textbox email terlihat.
2. Isi email dari `ACCURATE_EMAIL`.
3. Isi password dari `ACCURATE_PASSWORD`.
4. Klik tombol `Masuk`.
5. Tunggu proses login selesai.
6. Tutup dialog 2FA bila muncul.
7. Tunggu kartu perusahaan `cy` muncul.
8. Klik kartu perusahaan `cy`.

## Temuan Penting

### Selector Password

Locator berbasis role berikut gagal:

```text
getByRole('textbox', { name: 'Password' })
```

Penyebabnya adalah strict mode Playwright menemukan dua elemen:

- `#password` untuk form login.
- `#registerPassword` untuk form registrasi.

Locator yang benar dan stabil untuk login adalah:

```yaml
kind: css
selector: '#password'
```

### Dialog 2FA

Dialog 2FA tidak selalu muncul di setiap run. Karena itu, menunggu tombol
`Nanti Saja` secara langsung bisa menyebabkan langkah gagal.

Pola yang lebih stabil:

1. Tunggu beberapa detik setelah login.
2. Tekan `Escape` pada elemen `body`.
3. Tunggu kartu perusahaan muncul.

### Kartu Perusahaan

Kartu `cy` ditemukan dengan selector:

```css
div.cursor-pointer:has(h3:text-is('cy'))
```

DOM kartu tersebut memakai handler Knockout:

```html
<div class='cursor-pointer' data-bind='click:$root.selectOpenedDatabase'></div>
```

Handler `selectOpenedDatabase` memanggil `window.open` dengan URL:

```text
https://zeus.accurate.id/accurate/open.do?uid=<unique-company-id>&product=aol
```

Data dari halaman `/manage` menunjukkan:

| Field | Nilai |
| --- | --- |
| Alias | `cy` |
| Nama perusahaan | `<company-name>` |
| ID data | `<company-id>` |
| Host | `https://zeus.accurate.id` |
| Produk | `aol` |
| License | `TRIAL` |
| Unique ID | `<unique-company-id>` |

## Kredensial

Kredensial tidak ditulis langsung ke dalam file skenario.

Nilai disimpan di `.env`:

```env
ACCURATE_EMAIL=
ACCURATE_PASSWORD=
```

`.env.example` hanya berisi placeholder:

```env
ACCURATE_EMAIL=
ACCURATE_PASSWORD=
```

Deklarasi secret di skenario REA memakai `secret_id`
`accurate_password` yang diambil dari environment variable
`ACCURATE_PASSWORD`.

## Status Skenario

| Skenario | Status |
| --- | --- |
| Inspeksi halaman login | Berhasil |
| Login ke Accurate | Berhasil |
| Tutup dialog 2FA | Berhasil |
| Menampilkan daftar perusahaan | Berhasil |
| Klik kartu `cy` | Berhasil |
| Masuk langsung ke halaman perusahaan | Perlu penanganan popup atau redirect langsung |

## Rekomendasi Langkah Berikutnya

1. Gunakan URL langsung
   `https://zeus.accurate.id/accurate/open.do?uid=<unique-company-id>&product=aol`
   setelah login, atau aktifkan capture event `popups`.
2. Tambahkan mekanisme retry karena kadang form login atau redirect
   `/manage` tidak selesai pada waktu yang sama.
3. Simpan session atau cookie bila ingin menghindari login berulang.
4. Selalu jalankan browser dengan `headless: true`.

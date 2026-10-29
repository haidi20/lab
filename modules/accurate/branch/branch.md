# Cabang

**Module:** `#accurate__company__branch`
**Tipe Modul:** `MASTERDATA`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Perbarui daftar
- Cetak
- Ekspor XLS
- Ekspor PDF
- Pengaturan kolom

## Form Data Baru
Form **Data Baru Cabang** dibuka dari tombol `btnAdd`.

Wajib diisi: **Nama**.

### Tab Info Umum

#### Info Umum

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Nama | `name` (text) | Ya | Input manual pengguna. |
| No. Telepon | `phoneNumber` (text) | Tidak | Input manual pengguna. |
| Non Aktif | `suspended` (checkbox) | Tidak | Input manual pengguna. |

#### Info Lainnya

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Alamat | `street` (textarea); `city` (text); `zipCode` (text); `province` (text); `country` (text) | Tidak | Input manual pengguna. |
| Akses Pengguna | `usedAllUser` (checkbox) | Tidak | Akses pengguna/grup perusahaan; pilih Semua Pengguna atau batasi daftar. |

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnAdd` | - |
| `btnRefresh` | - |
| `btnPrint` | - |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| - | Tidak ada filter dinamis pada capture | - | - |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `suspended` | Non Aktif | Ya | BOOLEAN |
| `phoneNumber` | No. Telepon | Ya | TEXT |
| `name` | Nama | Ya | BRANCH_NAME |
| `branchAddress` | Alamat | Tidak | - |
| `userListName` | Daftar Pengguna | Ya | - |

Record aktual tersimpan di `data.json`: **0 baris**, status `empty`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel dan form | Master Cabang pada database perusahaan. | Konfigurasi `entityType = Branch` dan grid daftar cabang. |
| Akses Pengguna | Daftar pengguna/grup akses perusahaan. | Kontrol `usedAllUser` dan teks `Semua Pengguna`. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

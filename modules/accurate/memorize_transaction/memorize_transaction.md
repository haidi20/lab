# Transaksi Favorit

**Module:** `#accurate__company__memorize-transaction`
**Tipe Modul:** `INFORMATION`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Perbarui daftar
- Cetak
- Ekspor XLS
- Ekspor PDF
- Gunakan transaksi favorit yang tersimpan

## Form Data Baru
Tidak ada form tambah standar; capture tidak menampilkan `btnAdd`. Data favorit dibuat dari aksi simpan favorit pada modul transaksi.

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnRefresh` | - |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| `transactionTypeFilter` | Tipe Transaksi | LIST | 21 opsi |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `name` | Nama Favorit | Ya | - |
| `transactionTypeText` | Tipe Transaksi | Ya | - |
| `userListName` | Daftar Pengguna | Ya | - |

Record aktual tersimpan di `data.json`: **0 baris**, status `Belum ada data`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel | Transaksi favorit/template yang disimpan pengguna. | Kolom Nama Favorit, Tipe Transaksi, dan Daftar Pengguna. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

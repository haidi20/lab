# Transaksi Berulang

**Module:** `#accurate__company__recurring`
**Tipe Modul:** `TRANSACTION`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Jalankan transaksi berulang
- Kelola kategori transaksi berulang
- Perbarui daftar
- Cetak
- Ekspor XLS
- Ekspor PDF

## Form Data Baru
Tidak ada form tambah standar; capture tidak menampilkan `btnAdd`. Transaksi berulang dibuat dari modul transaksi sumber, sedangkan menu ini menjalankan dan mengelolanya.

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnRefresh` | - |
| `btnRecurringCategory` | - |
| `btnBulkExecuteRecurring` | Jalankan |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| - | Tidak ada filter dinamis pada capture | - | - |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `count` | Berapa kali | Tidak | - |
| `perioda` | Periode | Tidak | - |
| `recurringCategory.name` | Kategori | Ya | LOOKUP |
| `name` | Nama | Ya | - |
| `transactionTypeText` | Tipe Transaksi | Ya | - |
| `statusName` | Status | Ya | - |

Record aktual tersimpan di `data.json`: **0 baris**, status `Belum ada data`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel | Definisi transaksi berulang yang sudah disimpan. | Kolom Kategori, Nama, Tipe Transaksi, dan Status. |
| Kategori | Kategori Transaksi Berulang. | Tombol `btnRecurringCategory`. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

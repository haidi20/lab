# Log Aktifitas

**Module:** `#accurate__company__audit`
**Tipe Modul:** `INFORMATION`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Perbarui log
- Cetak
- Ekspor XLS
- Ekspor PDF
- Pengaturan kolom
- Filter aktivitas sistem

## Form Data Baru
Tidak ada form tambah karena menu ini read-only; record dihasilkan otomatis oleh sistem.

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnRefresh` | - |
| `btnColumnSetting` | - |
| `-` | - |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| `transDateFilter` | Tgl Transaksi | DATE | - |
| `logDateFilter` | Tanggal | DATE | - |
| `transactionTypeFilter` | Tipe Transaksi | LIST | 109 opsi |
| `createdByFilter` | Pengguna | LIST | 1 opsi |
| `operationTypeFilter` | Tipe Tindakan | LIST | 3 opsi |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `transDate` | Tgl Transaksi | Ya | DATE |
| `description` | No/Nama Referensi | Ya | TEXT |
| `operationTypeName` | Tipe Tindakan | Ya | - |
| `transactionTypeName` | Tipe Transaksi | Ya | - |
| `createDateView` | Tanggal | Ya | - |
| `createdBy` | Pengguna | Ya | - |
| `email` | Email | Ya | - |
| `accessIp` | Alamat IP | Ya | - |

Record aktual tersimpan di `data.json`: **1 baris**, status `loaded`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel | Log aktivitas yang dihasilkan otomatis oleh sistem saat pengguna membuat, mengubah, atau menghapus data. | Record capture: `Buat Preferensi` pada 29 Oct 2026. |
| Pengguna | Akun pengguna perusahaan. | Filter `createdByFilter` dan kolom Pengguna/Email. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

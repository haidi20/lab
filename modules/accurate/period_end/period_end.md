# Proses Akhir Bulan

**Module:** `#accurate__company__period-end`
**Tipe Modul:** `TRANSACTION`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Perbarui daftar
- Cetak
- Ekspor XLS
- Ekspor PDF
- Pengaturan kolom
- Atur nilai tukar mata uang

## Form Data Baru
Form **Data Baru Proses Akhir Bulan** dibuka dari tombol `btnAdd`.

Wajib diisi: **Bulan**.

### Tab Info Utama

#### Info Utama

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Bulan | `monthPE` (select) | Ya | Input manual pengguna. |
| Tahun | `yearPE` (select) | Tidak | Input manual pengguna. |

### Tab Nilai Tukar Mata Uang

#### Nilai Tukar

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Nilai Tukar Mata Uang | `currencyRate` (grid) | Tidak | Master mata uang perusahaan; capture menampilkan Indonesian Rupiah dengan nilai tukar 1. |

### Tab Catatan

#### Catatan

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Catatan | `description` (textarea) | Tidak | Input manual pengguna. |

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnAdd` | - |
| `btnRefresh` | - |
| `btnColumnSetting` | - |
| `-` | - |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| `monthPEFilter` | Bulan | LIST | 12 opsi |
| `yearPEFilter` | Tahun | LIST | 5 opsi |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `number` | Nama | Ya | TEXT |
| `transDate` | Tanggal Input | Ya | DATE |
| `description` | Keterangan | Ya | TEXT |
| `attachmentExist` | Memiliki dokumen | Tidak | BOOLEAN |

Record aktual tersimpan di `data.json`: **0 baris**, status `empty`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel | Entri Proses Akhir Bulan yang sudah dibuat. | Kolom Nama, Tanggal Input, Keterangan, dan Memiliki dokumen. |
| Bulan/Tahun | Konfigurasi periode perusahaan. | Filter `monthPEFilter` dan `yearPEFilter` dengan opsi 2023-2027. |
| Nilai Tukar | Master mata uang perusahaan. | Grid Nilai Tukar Mata Uang dan baris Indonesian Rupiah = 1. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

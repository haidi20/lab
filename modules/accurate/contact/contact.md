# Kontak

**Module:** `#accurate__company__contact`
**Tipe Modul:** `INFORMATION`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Perbarui daftar
- Cetak
- Ekspor XLS
- Ekspor PDF
- Pengaturan kolom
- Tampilkan kontak dari modul pelanggan/pemasok

## Form Data Baru
Tidak ada form tambah standar; capture tidak menampilkan `btnAdd`. Kontak dikelola dari modul pelanggan/pemasok.

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnRefresh` | - |
| `btnPrint` | - |
| `btnColumnSetting` | - |
| `-` | - |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| `branchFilter` | Cabang | LIST | - |
| `contactTypeFilter` | Tipe | LIST | 3 opsi |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `name` | Nama Lengkap | Ya | TEXT |
| `contactType` | Tipe | Ya | - |
| `companyName` | Perusahaan | Ya | TEXT |
| `email` | Email | Ya | TEXT |
| `mobilePhone` | Handphone | Ya | TEXT |
| `workPhone` | No. Telp. Bisnis | Tidak | TEXT |
| `homePhone` | No. Telp. Rumah | Tidak | TEXT |
| `branch.name` | Cabang | Tidak | LOOKUP |
| `fax` | Faximili | Tidak | TEXT |
| `notes` | Catatan | Tidak | TEXT |
| `bbmPin` | No. WhatsApp | Tidak | TEXT |
| `website` | Website | Tidak | TEXT |
| `position` | Posisi Jabatan | Tidak | TEXT |

Record aktual tersimpan di `data.json`: **0 baris**, status `Belum ada data`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel | Data kontak pelanggan/pemasok yang sudah tersimpan. | Kolom identitas dan kontak pada grid Kontak. |
| Cabang | Master Cabang. | Filter `branchFilter`. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

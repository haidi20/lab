# Syarat Pembayaran

**Module:** `#accurate__company__payment-term`
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
Form **Data Baru Syarat Pembayaran** dibuka dari tombol `btnAdd`.

### Tab Info Umum

#### Info Umum

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Jika membayar antara | `discDays` (number) | Tidak | Input manual pengguna. |
| Akan mendapat diskon | `discPC` (number) | Tidak | Input manual pengguna. |
| Masa Jatuh Tempo | `netDays` (number) | Tidak | Input manual pengguna. |
| Keterangan | `memo` (textarea) | Tidak | Input manual pengguna. |
| Default Syarat Pembayaran | `isDefault` (checkbox) | Tidak | Input manual pengguna. |
| Non Aktif | `suspended` (checkbox) | Tidak | Input manual pengguna. |

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnAdd` | - |
| `btnRefresh` | - |
| `btnPrint` | - |
| `btnColumnSetting` | - |
| `-` | - |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| `suspendedFilter` | Non Aktif | BOOLEAN | - |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `name` | Nama | Ya | TERM_NAME |
| `discPC` | Diskon (%) | Ya | MONEY |
| `discDays` | Masa Diskon (hari) | Ya | DAY_VALUE |
| `netDays` | Masa Jatuh Tempo (hari) | Ya | DAY_VALUE |
| `memo` | Keterangan | Ya | TEXT |
| `suspended` | Non Aktif | Ya | BOOLEAN |
| `defaultTerm` | Default | Ya | BOOLEAN |

Record aktual tersimpan di `data.json`: **0 baris**, status `empty`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel dan form | Master Syarat Pembayaran pada database perusahaan. | Konfigurasi `entityType = PaymentTerm`. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

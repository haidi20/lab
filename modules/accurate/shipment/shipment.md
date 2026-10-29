# Pengiriman

**Module:** `#accurate__company__shipment`
**Tipe Modul:** `MASTERDATA`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Perbarui daftar
- Impor
- Cetak
- Ekspor XLS
- Ekspor PDF
- Pengaturan kolom

## Form Data Baru
Form **Data Baru Pengiriman** dibuka dari tombol `btnAdd`.

Wajib diisi: **Nama**.

### Tab Info Umum

#### Info Umum

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Nama | `name` (text) | Ya | Input manual pengguna. |
| PIC | `picName` (text) | Tidak | Input manual pengguna. |
| No. Telp | `picPhoneNumber` (text) | Tidak | Input manual pengguna. |
| Non Aktif | `suspended` (checkbox) | Tidak | Input manual pengguna. |

#### Info Lainnya

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Alamat Pengiriman | `shipAddressStreet` (textarea); `shipAddressCity` (text); `shipAddressZipCode` (text); `shipAddressProvince` (text); `shipAddressCountry` (text) | Tidak | Input manual pengguna. |

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnAdd` | - |
| `btnRefresh` | - |
| `btnImport` | - |
| `btnPrint` | - |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| `suspendedFilter` | Non Aktif | BOOLEAN | - |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `name` | Nama | Ya | SHIPMENT_NAME |
| `picName` | PIC | Ya | TEXT |
| `picPhoneNumber` | No. Telp | Ya | TEXT |
| `shipAddress` | Alamat Lengkap | Ya | TEXT |
| `suspended` | Non Aktif | Ya | BOOLEAN |

Record aktual tersimpan di `data.json`: **0 baris**, status `empty`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel dan form | Master Pengiriman pada database perusahaan. | Konfigurasi `entityType = Shipment`. |
| Impor | Berkas impor yang diunggah pengguna. | Tombol `btnImport` pada toolbar. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

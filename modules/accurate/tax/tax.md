# Pajak

**Module:** `#accurate__company__tax`
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
Form **Data Baru Pajak** dibuka dari tombol `btnAdd`.

Wajib diisi: **Tipe Pajak**, **Keterangan**, **Akun Pajak Penjualan**, **Akun Pajak Pembelian**.

### Tab Info Umum

#### Info Umum

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Tipe Pajak | `taxType` (select) | Ya | Input manual pengguna. |
| Keterangan | `description` (text) | Ya | Input manual pengguna. |
| Akun Pajak Penjualan | `salesTaxGlAccount` (lookup) | Ya | Buku Besar > Akun Perkiraan; endpoint `/accurate/general-ledger/childwithtype-glaccount.do`. |
| Akun Pajak Pembelian | `purchaseTaxGlAccount` (lookup) | Ya | Buku Besar > Akun Perkiraan; endpoint `/accurate/general-ledger/childwithtype-glaccount.do`. |

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
| - | Tidak ada filter dinamis pada capture | - | - |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `description` | Keterangan | Ya | TAX_NAME |
| `taxTypeName` | Tipe Pajak | Ya | - |
| `rate` | Persentase | Ya | MONEY |
| `salesTaxGlAccount.name` | Akun Pajak Penjualan | Tidak | LOOKUP |
| `purchaseTaxGlAccount.name` | Akun Pajak Pembelian | Tidak | LOOKUP |

Record aktual tersimpan di `data.json`: **0 baris**, status `empty`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel dan form | Master Pajak pada database perusahaan. | Konfigurasi `entityType = Tax`. |
| Akun Pajak Penjualan/Pembelian | Buku Besar > Akun Perkiraan. | Lookup `/accurate/general-ledger/childwithtype-glaccount.do`. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

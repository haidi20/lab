# Gaji/Tunjangan

**Module:** `#accurate__company__employee-fee`
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
Form **Data Baru Gaji/Tunjangan** dibuka dari tombol `btnAdd`.

Wajib diisi: **Nama**, **Akun Beban**.

### Tab Info Umum

#### Info Umum

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Nama | `name` (text) | Ya | Input manual pengguna. |
| Tipe Gaji/Tunjangan | `feeType` (select) | Tidak | Input manual pengguna. |
| Akun Beban | `expenseAccount` (lookup) | Ya | Buku Besar > Akun Perkiraan; endpoint `/accurate/general-ledger/childwithtype-glaccount.do`. |
| Non Aktif | `suspended` (checkbox) | Tidak | Input manual pengguna. |

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
| `name` | Nama | Ya | TEXT |
| `feeType` | Tipe Gaji/Tunjangan | Ya | - |
| `suspended` | Non Aktif | Ya | BOOLEAN |

Record aktual tersimpan di `data.json`: **0 baris**, status `empty`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel dan form | Master Gaji/Tunjangan pada database perusahaan. | Konfigurasi `entityType = EmployeeFee`. |
| Akun Beban | Buku Besar > Akun Perkiraan. | Lookup `/accurate/general-ledger/childwithtype-glaccount.do`. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

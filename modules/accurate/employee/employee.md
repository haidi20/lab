# Karyawan

**Module:** `#accurate__company__employee`
**Tipe Modul:** `MASTERDATA`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Perbarui daftar
- Cetak
- Ekspor XLS
- Ekspor PDF
- Pengaturan kolom
- Histori piutang pada data tersimpan

## Form Data Baru
Form **Data Baru Karyawan** dibuka dari tombol `btnAdd`.

### Tab Info Umum

#### Data Pribadi

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Nama Lengkap | `salutation` (select); `name` (text) | Ya | Input manual pengguna. |
| No. KTP | `nikNo` (text) | Tidak | Input manual pengguna. |
| Email | `email` (text) | Tidak | Input manual pengguna. |
| Handphone | `mobilePhone` (text) | Tidak | Input manual pengguna. |
| No. Telp. Bisnis | `workPhone` (text) | Tidak | Input manual pengguna. |
| No. Telp. Rumah | `homePhone` (text) | Tidak | Input manual pengguna. |
| No. WhatsApp | `bbmPin` (text) | Tidak | Input manual pengguna. |
| Website | `website` (text) | Tidak | Input manual pengguna. |
| Kewarganegaraan | `domisiliType` (select) | Tidak | Input manual pengguna. |

#### Data Karyawan

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| ID Karyawan | `btnManualNumber--24--0` (checkbox); `typeAutoNumber` (select) | Tidak | Input manual pengguna. |
| Posisi Jabatan | `position` (text) | Tidak | Input manual pengguna. |
| Tgl Masuk | `joinDate` (date) | Tidak | Input manual pengguna. |
| Cabang | `branch` (select) | Tidak | Input manual pengguna. |
| Departemen | `department` (lookup) | Tidak | Departemen; endpoint `/accurate/company/child-department.do`, tambah cepat via `/accurate/company/save-department.do`. |
| Penjual | `salesman` (checkbox) | Tidak | Input manual pengguna. |
| Catatan | `notes` (textarea) | Tidak | Input manual pengguna. |
| Non Aktif | `suspended` (checkbox) | Tidak | Input manual pengguna. |

### Tab Info Alamat

#### Info Alamat

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Alamat | `street` (textarea); `city` (text); `zipCode` (text); `province` (text); `country` (text) | Tidak | Input manual pengguna. |

### Tab Pajak Penghasilan

#### Pajak Penghasilan

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Dikenakan PPh 21 | `pph` (checkbox) | Tidak | Input manual pengguna. |
| No. NPWP | `npwpNo` (text) | Tidak | Input manual pengguna. |
| Status Pekerja | `employeeWorkStatus` (select) | Tidak | Input manual pengguna. |
| Status PTKP | `employeeTaxStatus` (select) | Tidak | Input manual pengguna. |

#### Perhitungan PPh

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| PPh mulai dihitung | `startMonthPayment` (select); `startYearPayment` (select) | Tidak | Input manual pengguna. |
| Penghasilan Sebelumnya | `nettoIncomeBefore` (number) | Tidak | Input manual pengguna. |
| PPh Sebelumnya | `pphBefore` (number) | Tidak | Input manual pengguna. |

### Tab Info Akun

#### Info Akun

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Nama Bank | `bank` (lookup) | Tidak | Kode/nama bank; endpoint `/accurate/company/search-bank-code-type.do`. |
| No Rekening | `bankAccount` (text) | Tidak | Input manual pengguna. |
| Atas Nama Rekening | `bankAccountName` (text) | Tidak | Input manual pengguna. |

### Tab Histori Piutang

#### Filter Histori

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Tanggal Histori | `fromDate` (date); `toDate` (date) | Tidak | Input manual pengguna. |

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|
| `btnAdd` | - |
| `btnRefresh` | - |
| `btnImport` | - |
| `btnExport` | - |
| `btnPrint` | - |
| `btnColumnSetting` | - |
| `-` | - |
| `-` | - |

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| `suspendedFilter` | Non Aktif | BOOLEAN | - |
| `employeeWorkStatusFilter` | Status Pekerja | LIST | 7 opsi |
| `branchFilter` | Cabang | LIST | - |
| `salesmanFilter` | Penjual | BOOLEAN | - |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| `name` | Nama | Ya | EMPLOYEE_NAME |
| `position` | Posisi Jabatan | Ya | - |
| `email` | Email | Ya | - |
| `mobilePhone` | Handphone | Ya | - |
| `joinDate` | Tgl Masuk | Tidak | DATE |
| `calculatePtkp` | Dikenakan PTKP | Tidak | BOOLEAN |
| `nikNo` | No. KTP | Tidak | TEXT |
| `suspended` | Non Aktif | Tidak | BOOLEAN |
| `bankAccount` | Rekening Gaji | Tidak | TEXT |
| `bankAccountName` | Atas Nama Rekening | Tidak | TEXT |
| `bankName` | Nama Bank | Tidak | TEXT |
| `branch.name` | Cabang | Tidak | LOOKUP |
| `npwpNo` | No. NPWP | Tidak | TEXT |
| `attachmentExist` | Memiliki dokumen | Tidak | - |
| `salesman` | Penjual | Tidak | BOOLEAN |
| `number` | ID Karyawan | Ya | TEXT |
| `workPhone` | No. Telp. Bisnis | Tidak | - |
| `homePhone` | No. Telp. Rumah | Tidak | - |
| `employeeTaxStatusName` | Status PTKP | Ya | - |
| `employeeWorkStatusName` | Status Pekerja | Ya | - |
| `lastBalanceView` | Utang | Ya | - |
| `salesmanUser` | Login Penjual | Tidak | - |

Record aktual tersimpan di `data.json`: **0 baris**, status `empty`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Tabel dan form | Master Karyawan pada database perusahaan. | Konfigurasi `entityType = Employee`. |
| Cabang | Master Cabang. | Opsi `root.branchListOption` pada form Karyawan. |
| Departemen | Master Departemen. | Lookup `/accurate/company/child-department.do`; tambah cepat `/accurate/company/save-department.do`. |
| Nama Bank | Kode/nama bank. | Lookup `/accurate/company/search-bank-code-type.do`. |
| Histori Piutang | Transaksi yang menyentuh piutang karyawan. | Tab Histori Piutang dengan filter tanggal dan tombol refresh. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

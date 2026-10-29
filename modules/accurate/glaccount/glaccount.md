# Akun Perkiraan

**Module:** `#accurate__general-ledger__glaccount`
**Tipe Modul:** `MASTERDATA`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Perbarui daftar
- Impor XLS
- Ekspor XLS
- Cetak
- Pengaturan kolom
- Hapus akun
- Histori akun pada form

## Form Data Baru
### Tab Data Baru — Informasi Akun

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Sub Akun | `sub` (checkbox) | Tidak | DOM capture; jika aktif akun menjadi anak akun induk. |
| Kode Perkiraan | `no` (text) | Ya | DOM capture; input manual atau otomatis dari akun induk. |
| Nama | `name` (text) | Ya | DOM capture; input manual pengguna. |
| Tipe Akun | `accountType` (select) | Tidak | DOM capture; daftar tipe akun dari init modul. |
| Mata Uang | `currency` (lookup) | Tidak | DOM capture; lookup search-currency.do. |
| Catatan | `memo` (textarea) | Tidak | DOM capture; input manual pengguna. |
| Non Aktif | `suspended` (checkbox) | Tidak | DOM capture; input manual pengguna. |

### Tab Data Baru — Informasi Bank

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Nama Bank | `bank` (lookup) | Tidak | DOM capture; lookup search-bank-code-type.do. |
| No Rekening | `bankAccount` (text) | Tidak | DOM capture; input manual pengguna. |
| Atas Nama Rekening | `bankAccountName` (text) | Tidak | DOM capture; input manual pengguna. |

### Tab Data Baru — Saldo Awal

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Cabang | `branchId` (lookup) | Tidak | DOM capture; lookup search-branch.do. |
| Nilai | `openBalance` (number) | Tidak | DOM capture; input manual pengguna. |
| Per Tgl | `asOf` (date) | Tidak | DOM capture; input manual pengguna. |

### Tab Data Baru — Akses Pengguna

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Semua Pengguna | `usedAllUser` (checkbox) | Tidak | DOM capture; aktif berarti semua pengguna dapat mengakses akun. |
| Daftar Pengguna | `useUserAccessList` (lookup) | Tidak | DOM capture; akses pengguna/grup perusahaan. |
| Daftar Role Pengguna | `useUserRoleAccessList` (lookup) | Tidak | DOM capture; akses role/grup perusahaan. |

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `deleteUrl` | `/accurate/general-ledger/delete-glaccount.do` |
| `exportXlsUrl` | `/accurate/general-ledger/export-xls-glaccount.do` |
| `formHelpUrl` | `/accurate/general-ledger/help-glaccount.do` |
| `helpUrl` | `fitur-buku-besar/akun-perkiraan` |
| `htmlUrl` | `/accurate/general-ledger/glaccount.do` |
| `importXlsModule` | `accurate__general-ledger__glaccount-import` |
| `initUrl` | `/accurate/general-ledger/init-glaccount.do` |
| `printListUrl` | `/accurate/general-ledger/print-list-glaccount.do` |
| `searchUrl` | `/accurate/general-ledger/search-glaccount.do` |
| `selectUrl` | `/accurate/general-ledger/detail-glaccount.do` |
| `submitUrl` | `/accurate/general-ledger/save-glaccount.do` |

## Daftar & Filter
| Key | Label | Tipe | Default/Tampil |
|---|---|---|---|
| `suspendedFilter` | Non Aktif | BOOLEAN | Ya |
| `currencyFilter` | Mata Uang | LIST | Tidak |
| `accountTypeFilter` | Tipe Akun | LIST | Ya |

## Kolom Tabel
| Key | Label | Tipe | Default/Tampil |
|---|---|---|---|
| `noWithIndent` | Kode Perkiraan | - | Ya |
| `nameWithIndent` | Nama | - | Ya |
| `accountTypeName` | Tipe Akun | - | Ya |
| `currency.name` | Mata Uang | LOOKUP | Tidak |
| `suspended` | Non Aktif | BOOLEAN | Tidak |
| `memo` | Catatan | TEXT | Tidak |
| `balance` | Saldo | MONEY_BALANCE | Ya |
| `bankAccount` | Rekening Gaji | TEXT | Tidak |
| `bankAccountName` | Atas Nama Rekening | TEXT | Tidak |
| `checked` | [Pilih] | CHECKBOX | Tidak |
| `userListName` | Daftar Pengguna | - | Tidak |
| `parentName` | Sub dari | - | Tidak |

Record aktual tersimpan di `data.json`: **19 baris**, status `loaded`.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/glaccount.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

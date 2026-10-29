# Anggaran

**Module:** `#accurate__budget-target__accountbudget-target`
**Tipe Modul:** `TRANSACTION`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Simpan
- Hapus
- Cari
- Cetak daftar
- Hitung anggaran

## Form Data Baru
### Tab Data Baru — Field Model

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Id | `id` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Opt lock | `optLock` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Budget year | `budgetYear` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Budget month | `budgetMonth` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Analyst name | `analystName` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Trans date | `transDate` (date) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Notes | `notes` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Scope type | `scopeType` (lookup) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Cost center name | `costCenterName` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Department | `department` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Project | `project` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Branch id | `branchId` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Transaction currency id | `transactionCurrencyId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Title tab name | `titleTabName` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Detail account | `detailAccount` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `calculateUrl` | `/accurate/budget-target/calculate-accountbudget-target.do` |
| `deleteUrl` | `/accurate/budget-target/delete-accountbudget-target.do` |
| `formHelpUrl` | `/accurate/budget-target/help-accountbudget-target.do` |
| `helpUrl` | `fitur-buku-besar/anggaran` |
| `htmlUrl` | `/accurate/budget-target/accountbudget-target.do` |
| `initUrl` | `/accurate/budget-target/init-accountbudget-target.do` |
| `printListUrl` | `/accurate/budget-target/print-list-account-budget-target.do` |
| `searchUrl` | `/accurate/budget-target/search-accountbudget-target.do` |
| `selectUrl` | `/accurate/budget-target/detail-accountbudget-target.do` |
| `submitUrl` | `/accurate/budget-target/save-accountbudget-target.do` |

## Daftar & Filter
Tidak ada data filter yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

## Kolom Tabel
Tidak ada data kolom yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

Belum ada capture tabel yang valid; `data.json` memakai **0 baris** dan status `not_captured`, bukan klaim tabel benar-benar kosong.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/accountbudget_target.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

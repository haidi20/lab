# Transfer Anggaran

**Module:** `#accurate__budget-target__accountbudget-transfer`
**Tipe Modul:** `TRANSACTION`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Simpan
- Hapus
- Cari
- Persetujuan/Tolak/Batalkan

## Form Data Baru
### Tab Data Baru — Field Model

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Id | `id` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Opt lock | `optLock` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Number | `number` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Trans date | `transDate` (date) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Type auto number | `typeAutoNumber` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Budget year | `budgetYear` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Scope type | `scopeType` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Department | `department` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Project | `project` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Branch id | `branchId` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Transfer from month | `transferFromMonth` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Transfer from account | `transferFromAccount` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Transfer amount | `transferAmount` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Transfer to month | `transferToMonth` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Transfer to account | `transferToAccount` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Description | `description` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `approveUrl` | `/accurate/budget-target/approve-accountbudget-transfer.do` |
| `cancelApprovalUrl` | `/accurate/budget-target/cancel-approval-accountbudget-transfer.do` |
| `deleteUrl` | `/accurate/budget-target/delete-accountbudget-transfer.do` |
| `htmlUrl` | `/accurate/budget-target/accountbudget-transfer.do` |
| `initUrl` | `/accurate/budget-target/init-accountbudget-transfer.do` |
| `rejectUrl` | `/accurate/budget-target/reject-accountbudget-transfer.do` |
| `searchUrl` | `/accurate/budget-target/search-accountbudget-transfer.do` |
| `selectUrl` | `/accurate/budget-target/view-accountbudget-transfer.do` |
| `submitUrl` | `/accurate/budget-target/save-accountbudget-transfer.do` |

## Daftar & Filter
Tidak ada data filter yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

## Kolom Tabel
Tidak ada data kolom yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

Belum ada capture tabel yang valid; `data.json` memakai **0 baris** dan status `not_captured`, bukan klaim tabel benar-benar kosong.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/accountbudget_transfer.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

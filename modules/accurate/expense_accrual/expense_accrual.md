# Pencatatan Beban

**Module:** `#accurate__general-ledger__expense-accrual`
**Tipe Modul:** `TRANSACTION`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Simpan
- Hapus
- Cetak daftar
- Impor dari file
- Hitung detail
- Persetujuan/Tolak/Batalkan
- Draft
- Transaksi berulang
- Lampiran
- Komentar

## Form Data Baru
### Tab Data Baru — Field Model

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Need detail result | `needDetailResult` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Attachment count | `attachmentCount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Comment count | `commentCount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Approval description | `approvalDescription` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Rejection reason | `rejectionReason` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Approval is urgent | `approvalIsUrgent` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Created by | `createdBy` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Id | `id` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Opt lock | `optLock` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Trans date | `transDate` (date) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Due date | `dueDate` (date) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Number | `number` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Type auto number | `typeAutoNumber` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Count auto number | `countAutoNumber` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Recurring detail id | `recurringDetailId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Expense payable id | `expensePayableId` (lookup) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Expense payable | `expensePayable` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Rate | `rate` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Description | `description` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Amount | `amount` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Paid amount | `paidAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Status name | `statusName` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Payment history | `paymentHistory` (complex_array) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Journal id | `journalId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Transaction currency id | `transactionCurrencyId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Detail account | `detailAccount` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Comment | `comment` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Attachments | `attachments` (complex_array) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field1 | `searchCharField1` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field2 | `searchCharField2` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field3 | `searchCharField3` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field4 | `searchCharField4` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field5 | `searchCharField5` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field6 | `searchCharField6` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field7 | `searchCharField7` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field8 | `searchCharField8` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field9 | `searchCharField9` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Search char field10 | `searchCharField10` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Char field1 | `charField1` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field2 | `charField2` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field3 | `charField3` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field4 | `charField4` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field5 | `charField5` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field6 | `charField6` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field7 | `charField7` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field8 | `charField8` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field9 | `charField9` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Char field10 | `charField10` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field1 | `numericField1` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field2 | `numericField2` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field3 | `numericField3` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field4 | `numericField4` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field5 | `numericField5` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field6 | `numericField6` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field7 | `numericField7` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field8 | `numericField8` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field9 | `numericField9` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Numeric field10 | `numericField10` (number) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Date field1 | `dateField1` (date) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Date field2 | `dateField2` (date) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Transaction id | `transactionId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Approval detail list | `approvalDetailList` (complex_array) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Approval status | `approvalStatus` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Save as status type | `saveAsStatusType` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Branch id | `branchId` (lookup) | Ya | Field wajib pada requiredFormData; nilai default diinisialisasi base class. |

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `approveUrl` | `/accurate/general-ledger/approve-expense-accrual.do` |
| `calculateUrl` | `/accurate/general-ledger/calculate-expense-accrual-detail.do` |
| `cancelApprovalUrl` | `/accurate/general-ledger/cancel-approval-expense-accrual.do` |
| `deleteUrl` | `/accurate/general-ledger/delete-expense-accrual.do` |
| `formHelpUrl` | `/accurate/general-ledger/help-expense-accrual.do` |
| `helpUrl` | `fitur-buku-besar/pencatatan-beban` |
| `htmlUrl` | `/accurate/general-ledger/expense-accrual.do` |
| `importFromFileModule` | `accurate__general-ledger__expense-accrual-import-file` |
| `initUrl` | `/accurate/general-ledger/init-expense-accrual.do` |
| `printListUrl` | `/accurate/general-ledger/print-list-expense-accrual.do` |
| `rejectUrl` | `/accurate/general-ledger/reject-expense-accrual.do` |
| `searchUrl` | `/accurate/contractor/search-getfrom-project-cost.do` |
| `selectUrl` | `/accurate/contractor/detail-getfrom-project-cost.do` |
| `submitUrl` | `/accurate/general-ledger/save-expense-accrual.do` |

## Daftar & Filter
Tidak ada data filter yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

## Kolom Tabel
Tidak ada data kolom yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

Belum ada capture tabel yang valid; `data.json` memakai **0 baris** dan status `not_captured`, bukan klaim tabel benar-benar kosong.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/expense_accrual.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

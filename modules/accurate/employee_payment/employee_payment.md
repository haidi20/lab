# Pencatatan Gaji

**Module:** `#accurate__cash-bank__employee-payment`
**Tipe Modul:** `TRANSACTION`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Simpan
- Hapus
- Cetak daftar
- Ekspor CSV
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
| Unique data number | `uniqueDataNumber` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Need detail result | `needDetailResult` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Attachment count | `attachmentCount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Comment count | `commentCount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Approval description | `approvalDescription` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Rejection reason | `rejectionReason` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Approval is urgent | `approvalIsUrgent` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Created by | `createdBy` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Id | `id` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Opt lock | `optLock` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Employee payment type | `employeePaymentType` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Trans date | `transDate` (date) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Due date | `dueDate` (date) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Pph due date | `pphDueDate` (date) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Pension due date | `pensionDueDate` (date) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Health insurance due date | `healthInsuranceDueDate` (date) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Number | `number` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Type auto number | `typeAutoNumber` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Count auto number | `countAutoNumber` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Expense payable | `expensePayable` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Rate | `rate` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Description | `description` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Income amount | `incomeAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Amount | `amount` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Pph amount | `pphAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Exceed pph amount | `exceedPphAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Pension amount | `pensionAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Health insurance amount | `healthInsuranceAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Says | `says` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Journal id | `journalId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Transaction currency id | `transactionCurrencyId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Detail employee payment | `detailEmployeePayment` (complex_array) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Summary employee payment | `summaryEmployeePayment` (complex_array) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Comment | `comment` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Attachments | `attachments` (complex_array) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Payment history | `paymentHistory` (complex_array) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Payment year | `paymentYear` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Payment month | `paymentMonth` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Period month name | `periodMonthName` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Paid amount | `paidAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Salary paid amount | `salaryPaidAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Pph paid amount | `pphPaidAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Exceed pph paid amount | `exceedPphPaidAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Pension paid amount | `pensionPaidAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Health insurance paid amount | `healthInsurancePaidAmount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Return exceed pph to allowance | `returnExceedPphToAllowance` (checkbox) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Status | `status` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Status name | `statusName` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Branch name | `branchName` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Pph account | `pphAccount` (lookup) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Health insurance account | `healthInsuranceAccount` (lookup) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Pension account | `pensionAccount` (lookup) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Return exceed pph to allowance account | `returnExceedPphToAllowanceAccount` (checkbox) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
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
| Employee payable type | `employeePayableType` (lookup) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Approval detail list | `approvalDetailList` (complex_array) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Approval status | `approvalStatus` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Save as status type | `saveAsStatusType` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Branch id | `branchId` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `approveUrl` | `/accurate/cash-bank/approve-employee-payment.do` |
| `calculateUrl` | `/accurate/cash-bank/calculate-employee-payment-detail.do` |
| `cancelApprovalUrl` | `/accurate/cash-bank/cancel-approval-employee-payment.do` |
| `deleteUrl` | `/accurate/cash-bank/delete-employee-payment.do` |
| `exportCsvUrl` | `/accurate/cash-bank/export-csv-employee-payment.do` |
| `formHelpUrl` | `/accurate/cash-bank/help-employee-payment.do` |
| `helpUrl` | `fitur-buku-besar/pencatatan-gaji` |
| `htmlUrl` | `/accurate/cash-bank/employee-payment.do` |
| `initUrl` | `/accurate/cash-bank/init-employee-payment.do` |
| `printListUrl` | `/accurate/cash-bank/print-list-employee-payment.do` |
| `rejectUrl` | `/accurate/cash-bank/reject-employee-payment.do` |
| `searchUrl` | `/accurate/cash-bank/search-employee-payment.do` |
| `selectUrl` | `/accurate/cash-bank/search-employee-for-payment.do` |
| `submitUrl` | `/accurate/cash-bank/bg-save-employee-payment.do` |

## Daftar & Filter
Tidak ada data filter yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

## Kolom Tabel
Tidak ada data kolom yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

Belum ada capture tabel yang valid; `data.json` memakai **0 baris** dan status `not_captured`, bukan klaim tabel benar-benar kosong.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/employee_payment.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

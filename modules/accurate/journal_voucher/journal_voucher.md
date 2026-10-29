# Jurnal Umum

**Module:** `#accurate__general-ledger__journal-voucher`
**Tipe Modul:** `TRANSACTION`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Data Baru
- Simpan
- Hapus
- Cari
- Cetak
- Hitung jurnal
- Impor dari file
- Audit
- Transaksi berulang
- Lampiran
- Komentar

## Form Data Baru
### Tab Data Baru — Field Model

| Field | Input | Wajib | Sumber Data |
|---|---|---|---|
| Unique data number | `uniqueDataNumber` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Id | `id` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Opt lock | `optLock` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Transaction type | `transactionType` (lookup) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Transaction id | `transactionId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Transaction type name | `transactionTypeName` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Type auto number | `typeAutoNumber` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Recurring detail id | `recurringDetailId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Number | `number` (text) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Trans number | `transNumber` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Trans date | `transDate` (date) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Description | `description` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Total debit | `totalDebit` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Total credit | `totalCredit` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Transaction currency id | `transactionCurrencyId` (text) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Detail journal voucher | `detailJournalVoucher` (complex_array) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Comment | `comment` (textarea) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Attachments | `attachments` (complex_array) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Attachment count | `attachmentCount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Comment count | `commentCount` (number) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Branch id | `branchId` (lookup) | Ya | Field model defaultData; label UI belum terekam dari DOM. |
| Is depreciation period end | `isDepreciationPeriodEnd` (checkbox) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
| Is bank transfer | `isBankTransfer` (checkbox) | Tidak | Field model defaultData; label UI belum terekam dari DOM. |
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
| Date field2 | `dateField2` (date) | Ya | Field wajib pada requiredFormData; nilai default diinisialisasi base class. |

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `calculateUrl` | `/accurate/general-ledger/calculated-journal-voucher.do` |
| `deleteUrl` | `/accurate/general-ledger/delete-journal-voucher.do` |
| `formHelpUrl` | `/accurate/general-ledger/help-journal-voucher.do` |
| `helpUrl` | `fitur-buku-besar/jurnal-umum` |
| `htmlUrl` | `/accurate/general-ledger/journal-voucher.do` |
| `importFromFileModule` | `accurate__general-ledger__journal-voucher-import-file` |
| `initUrl` | `/accurate/general-ledger/init-journal-voucher.do` |
| `searchUrl` | `/accurate/general-ledger/search-journal-voucher.do` |
| `selectUrl` | `/accurate/general-ledger/view-journal-voucher.do` |
| `submitUrl` | `/accurate/general-ledger/save-journal-voucher.do` |

## Daftar & Filter
Tidak ada data filter yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

## Kolom Tabel
Tidak ada data kolom yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

Belum ada capture tabel yang valid; `data.json` memakai **0 baris** dan status `not_captured`, bukan klaim tabel benar-benar kosong.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/journal_voucher.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

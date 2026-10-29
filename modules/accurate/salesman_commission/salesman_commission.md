# Komisi Penjual

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Komisi Berlaku | `activePeriod` | text | Tidak | - |
| Selamanya | `activePeriod` | text | Tidak | - |
| Periode Tertentu | `activePeriod` | text | Tidak | - |
| Nama perhitungan komisi | `name` | text | Ya | - |
| Berlaku ke Tenaga Penjual | `activePeriod`, `name`, `rbsalesmantarget`, `userList`, `forLevel1`, `forLevel2`, `forLevel3`, `forLevel4`, `forLevel5`, `optionItemTarget`, `itemCategoryTarget`, `itemTarget`, `itemBrandTarget`, `optionVendorTarget`, `vendorTarget`, `rbrequirement`, `requirementAmountFrom`, `requirementAmountTo`, `requirementQuantityFrom`, `requirementQuantityTo`, `requirementQuantityMinimum`, `gain`, `gainAmountPercent`, `gainCalculatedBy`, `memo`, `suspended` | text, text, text, lookup, checkbox, checkbox, checkbox, checkbox, checkbox, select, lookup, lookup, lookup, select, lookup, text, number, number, number, number, number, select, number, select, textarea, checkbox | Ya | optionItemTarget: Semua Barang, Pilih Kategori Barang, Pilih Barang, Pilih Merk Barang; optionVendorTarget: Semua Pemasok, Pilih Pemasok; gain: Persentase, Nilai Tetap; gainCalculatedBy: Nilai Penjualan, Laba Kotor |
| Semua | `rbsalesmantarget` | text | Tidak | - |
| Tertentu | `rbsalesmantarget`, `userList` | text, lookup | Tidak | - |
| Diberikan pada penjual urutan (Urutan input penjual di faktur) | `forLevel1`, `forLevel2`, `forLevel3`, `forLevel4`, `forLevel5` | checkbox, checkbox, checkbox, checkbox, checkbox | Ya | - |
| Pertama | `forLevel1`, `forLevel2`, `forLevel3`, `forLevel4`, `forLevel5` | checkbox, checkbox, checkbox, checkbox, checkbox | Tidak | - |
| Komisi berlaku untuk barang | `optionItemTarget`, `itemCategoryTarget`, `itemTarget`, `itemBrandTarget` | select, lookup, lookup, lookup | Ya | optionItemTarget: Semua Barang, Pilih Kategori Barang, Pilih Barang, Pilih Merk Barang |
| Dari pemasok utama | `optionVendorTarget`, `vendorTarget` | select, lookup | Ya | optionVendorTarget: Semua Pemasok, Pilih Pemasok |
| Dengan syarat perhitungan | `rbrequirement`, `requirementAmountFrom`, `requirementAmountTo`, `requirementQuantityFrom`, `requirementQuantityTo`, `requirementQuantityMinimum` | text, number, number, number, number, number | Ya | - |
| Tanpa batasan dan syarat | `rbrequirement` | text | Tidak | - |
| Nilai Penjualan antara | `rbrequirement`, `requirementAmountFrom`, `requirementAmountTo` | text, number, number | Tidak | - |
| Kuantitas penjualan antara | `rbrequirement`, `requirementQuantityFrom`, `requirementQuantityTo` | text, number, number | Tidak | - |
| Kuantitas terjual per | `rbrequirement`, `requirementQuantityMinimum` | text, number | Tidak | - |
| Akan mendapat komisi | `gain`, `gainAmountPercent`, `gainCalculatedBy` | select, number, select | Ya | gain: Persentase, Nilai Tetap; gainCalculatedBy: Nilai Penjualan, Laba Kotor |
| Non Aktif | `suspended` | checkbox | Tidak | - |

### Tombol Form
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
- Tidak ada filter dropdown yang terekstrak dari DOM.
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `memo` | Catatan | Ya |
| `name` | Nama | Ya |
| `activePeriod` | Periode Berlaku | Ya |

## Sumber Data
- `/accurate/company/salesman-commission.do`
- `/accurate/company/`
- `/accurate/inventory/`
- `/accurate/inventory/tree-item-brand.do`
- `/accurate/vendor/`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

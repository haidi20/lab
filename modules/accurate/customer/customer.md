# Pelanggan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Pelanggan |
| Nama | `name` | text | Ya | - |
| Kategori | `category` | lookup | Tidak | - |
| No. Telp. Bisnis | `workPhone` | text | Tidak | - |
| Handphone | `mobilePhone` | text | Tidak | - |
| No. WhatsApp | `bbmPin` | text | Tidak | - |
| Email | `email` | text | Tidak | - |
| Faximili | `fax` | text | Tidak | - |
| Website | `website` | text | Tidak | - |
| Alamat Penagihan | `billStreet`, `billCity`, `billZipCode`, `billProvince`, `billCountry` | textarea, text, text, text, text | Tidak | - |
| Dipakai di Cabang | `branch` | select | Tidak | branch: [Semua Cabang], Kantor Pusat |
| Sama dengan alamat penagihan | `shipSameAsBill` | checkbox | Tidak | - |
| Jadikan Agen | `reseller` | checkbox | Tidak | - |
| Kategori Harga | `priceCategory` | lookup | Ya | - |
| Kategori Diskon | `discountCategory` | lookup | Tidak | - |
| Syarat Pembayaran | `term` | lookup | Tidak | - |
| Default Penjual | `salesmanList` | lookup | Tidak | - |
| Default Diskon (%) | `defaultSalesDisc` | text | Tidak | - |
| Default Deskripsi | `defaultInvoiceDesc` | text | Tidak | - |
| Konsinyasi | `consignmentStore` | checkbox | Tidak | - |
| Piutang | `customerReceivableAccountList` | lookup | Tidak | - |
| Uang muka | `customerDownPaymentAccountList` | lookup | Tidak | - |
| Penjualan | `salesAccount` | lookup | Tidak | - |
| Diskon Barang | `itemDiscountAccount` | lookup | Tidak | - |
| Beban Pokok Penjualan | `costOfGoodsSoldAccount` | lookup | Tidak | - |
| Retur Penjualan | `salesReturnAccount` | lookup | Tidak | - |
| Diskon Penjualan | `salesDiscountAccount` | lookup | Tidak | - |
| Pajak | `defaultIncTax` | checkbox | Tidak | - |
| Tipe ID Pajak | `wpType` | select | Tidak | wpType: NIK, NPWP, Passpor, Lainnya |
| Nomor Wajib Pajak | `wpNumber` | text | Tidak | - |
| Nama Wajib Pajak | `wpName` | text | Tidak | - |
| NITKU | `nitku` | text | Tidak | - |
| Kode Negara | `countryTax` | lookup | Tidak | - |
| Tipe Transaksi | `documentCode` | select | Tidak | documentCode: Faktur Pajak, Dokumen Tertentu, Ekspor, Digunggung |
| Alamat Pajak | `taxSameAsBill`, `taxStreet`, `taxCity`, `taxZipCode`, `taxProvince`, `taxCountry` | checkbox, textarea, text, text, text, text | Tidak | - |
| Sama dengan alamat penagihan | `taxSameAsBill` | checkbox | Tidak | - |
| Per Pelanggan | `groupCustomerLimit` | text | Tidak | - |
| Jika ada faktur dengan umur lebih dari | `customerLimitAge` | checkbox | Tidak | - |
| Jika total piutang & pesanan melebihi | `customerLimitAmount` | checkbox | Tidak | - |
| Tergabung ke Pelanggan Induk | `groupCustomerLimit` | text | Tidak | - |
| Gudang Default | `defaultWarehouse` | lookup | Tidak | - |
| Non Aktif | `suspended` | checkbox | Tidak | - |
| s/d | `fromDate`, `toDate` | date, date | Tidak | - |

### Info Lainnya
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Catatan | `notes` | textarea | Tidak | - |

### Tombol Form
- `btnGetFrom` — Ambil Favorit.
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
| Field | Nilai Tampil |
| --- | --- |
| `suspendedFilter` — Non Aktif | Semua |
| `categoryFilter` — Kategori | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `checked` | [Pilih] | Opsional |
| `name` | Nama | Ya |
| `customerNo` | ID Pelanggan | Ya |
| `category.name` | Kategori | Opsional |
| `currency.code` | Mata Uang | Opsional |
| `wpName` | Nama Wajib Pajak | Opsional |
| `contactInfo.name` | Kontak Utama | Ya |
| `countryCode` | Kode Negara | Opsional |
| `suspended` | Non Aktif | Opsional |
| `nitku` | NITKU | Opsional |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `wpType` | Tipe ID Wajib Pajak | Opsional |
| `wpNumber` | Nomor Wajib Pajak | Opsional |
| `defaultTerm.name` | Syarat Pembayaran | Opsional |
| `discountCategory.name` | Kategori Diskon | Opsional |
| `defaultWarehouse.name` | Gudang Default | Opsional |
| `priceCategory.name` | Kategori Penjualan | Opsional |
| `consignmentStore` | Konsinyasi | Opsional |
| `customerNoVa` | Nomor VA | Opsional |
| `reseller` | Agen | Opsional |
| `lastBalanceView` | Saldo | Ya |
| `owingLimitDescription` | Limit Piutang | Opsional |
| `customerBranchName` | Cabang | Opsional |
| `salesmanNameList` | Default Penjual | Opsional |
| `shipAddress.concatFullAddress` | Alamat Utama | Opsional |
| `billAddress.concatFullAddress` | Alamat Penagihan | Opsional |
| `taxAddress.concatFullAddress` | Alamat Pajak | Opsional |
| `notes` | Catatan | Opsional |
| `contactInfoView` | Kontak Utama | Opsional |
| `otherContactInfo1View` | Kontak Lainnya #1 | Opsional |
| `otherContactInfo2View` | Kontak Lainnya #2 | Opsional |
| `otherContactInfo3View` | Kontak Lainnya #3 | Opsional |

## Sumber Data
- `/accurate/customer/customer.do`
- `/accurate/cu`
- `/accurate/company/`
- `/accurate/general-ledger/childwithtype-glaccount.do`
- `/accurate/inventory/lookup-`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

# Faktur Penjualan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Faktur Penjualan |
| Pelanggan | `customer` | lookup | Ya | - |
| Tanggal | `transDate` | date | Ya | - |
| Biaya Lainnya | `searchDetailAccount` | lookup | Ya | - |
| Syarat Pembayaran | `paymentTerm` | lookup | Tidak | - |
| No. PO | `poNumber` | text | Tidak | - |
| Alamat | `toAddress` | textarea | Tidak | - |
| Pajak | `taxable`, `inclusiveTax` | checkbox, checkbox | Tidak | - |
| Kena Pajak | `taxable`, `inclusiveTax` | checkbox, checkbox | Tidak | - |
| Tgl Faktur Pajak | `taxDate` | date | Tidak | - |
| Tipe Transaksi | `documentCode` | select | Tidak | documentCode: Faktur Pajak, Dokumen Tertentu, Ekspor, Digunggung |
| Detail Transaksi | `taxType` | select | Tidak | taxType: 01 - kepada selain Pemungut PPN, 02 - kepada Pemungut PPN Instansi Pemerintah, 03 - kepada Pemungut PPN selain Instansi Pemerintah, 04 - DPP Nilai Lain, 05 - Besaran tertentu, 06 - kepada orang pribadi pemegang paspor luar negeri (16E UU PPN), 07 - penyerahan dengan fasilitas PPN atau PPN dan PPnBM tidak dipungut/ditanggung pemerintah, 08 - penyerahan dengan fasilitas dibebaskan PPN atau PPN dan PPnBM, 09 - penyerahan aktiva yang menurut tujuan semula tidak diperjualbelikan (16D UU PPN), 10 - Penyerahan lainnya |
| Tgl Pengiriman | `shipDate` | date | Tidak | - |
| Pengiriman | `shipment` | lookup | Tidak | - |
| FOB | `fob` | lookup | Tidak | - |

### Detail
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Rincian Barang | `searchDetailItem`, `searchKeywordItem` | lookup, text | Ya | - |

### Info Lainnya
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Keterangan | `description` | textarea | Tidak | - |

### Tombol Form
- `btnGetFrom` — Ambil Favorit.
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
| Field | Nilai Tampil |
| --- | --- |
| `transDateFilter` — Tanggal | Semua |
| `customerFilter` — Pelanggan | Semua |
| `statusFilter` — Status | Semua |
| `hasUserPrintedFilter` — Sudah dicetak | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `number` | Nomor # | Ya |
| `transDate` | Tanggal | Ya |
| `customer.name` | Pelanggan | Ya |
| `currency.code` | Mata Uang | Opsional |
| `poNumber` | No. PO | Opsional |
| `paymentTerm.name` | Syarat Pembayaran | Opsional |
| `shipDate` | Tgl Pengiriman | Opsional |
| `taxDate` | Tgl Faktur Pajak | Opsional |
| `description` | Keterangan | Ya |
| `statusName` | Status | Ya |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `tax4Amount` | PPh 22 Impor | Opsional |
| `dppAmount` | DPP | Opsional |
| `taxable` | Kena Pajak | Opsional |
| `inclusiveTax` | Total termasuk Pajak | Opsional |
| `branch.name` | Cabang | Opsional |
| `tax3Amount` | PPh | Opsional |
| `dueDate` | Jatuh Tempo | Opsional |
| `arAccount.name` | Akun Piutang | Opsional |
| `efakturFileName` | File efaktur | Opsional |
| `vaNumber` | Nomor VA | Opsional |
| `subComp` | Sub Kode Perusahaan | Opsional |
| `posPromotion.name` | Promo | Opsional |
| `openingBalance` | Saldo awal | Opsional |
| `reverseInvoice` | Faktur Dimuka | Opsional |
| `retailWpType` | Tipe ID Wajib Pajak | Ya |
| `masterSalesman.name` | Penjual Utama | Opsional |
| `taxType` | Detail Transaksi | Opsional |
| `hasExchangeInvoice` | Ditukar Faktur | Opsional |
| `masterDepartment.name` | Departemen Utama | Opsional |
| `taxNumber` | No. Faktur Pajak | Opsional |
| `masterProject.name` | Proyek Utama | Opsional |
| `exchangeInvoiceDueDate` | Jatuh Tempo (Tukar Faktur) | Opsional |
| `pendingAmortized` | Pendapatan Tertunda | Opsional |
| `paidOverTotal` | Pendapatan Tertunda | Opsional |
| `cashierEmployee.name` | Kasir | Opsional |
| `paymentWithUniqueAmount` | Faktur Kode Unik | Opsional |
| `uniqueAmount` | Kode Unik | Opsional |
| `totalAmountWithUniqueAmount` | Total Transfer | Opsional |
| `masterPosSalesType.name` | Tipe Penjualan Utama | Opsional |
| `checked` | [Pilih] | Opsional |
| `age` | Umur (hr) | Ya |
| `printedByUser` | Dicetak/email | Opsional |
| `invoicePrintedTime` | Waktu cetak/email | Opsional |
| `deliveryPackingNumber` | No Pengepakan | Opsional |
| `createdByUserName` | Pembuat Data | Opsional |
| `customerCategoryName` | Kategori Pelanggan | Opsional |
| `documentCodeName` | Jenis Dokumen | Opsional |
| `totalDiscountDetail` | Diskon Barang | Opsional |
| `totalDiscount` | Total Diskon | Opsional |
| `customerNo` | ID Pelanggan | Opsional |
| `subTotal` | Sub Total | Opsional |
| `cashDiscPercent` | Diskon % | Opsional |
| `cashDiscount` | Diskon | Opsional |
| `totalDownPayment` | Uang Muka | Opsional |
| `tax1Amount` | Nilai PPN | Opsional |
| `tax2Amount` | Nilai PPNBM | Opsional |
| `totalExpense` | Biaya Lainnya | Opsional |
| `totalAmount` | Total | Ya |
| `primeReceipt` | Pembayaran | Opsional |
| `taxReceipt` | Terima Pajak | Opsional |
| `primeReturn` | Retur | Opsional |
| `taxReturn` | Retur Pajak | Opsional |
| `primeOwing` | Piutang | Opsional |
| `taxOwing` | Piutang Pajak | Opsional |

## Sumber Data
- `/accurate/customer/sales-invoice.do`
- `/accurate/cu`
- `/accurate/inventory/`
- `/accurate/general-ledger/childwithtype-glaccount.do`
- `/accurate/company/`
- `/accurate/company/detail-`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

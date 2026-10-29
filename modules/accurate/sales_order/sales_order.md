# Pesanan Penjualan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Pesanan Penjualan |
| Dipesan oleh | `customer` | lookup | Ya | - |
| Tanggal | `transDate` | date | Ya | - |
| Biaya Lainnya | `searchDetailAccount` | lookup | Ya | - |
| Syarat Pembayaran | `paymentTerm` | lookup | Tidak | - |
| No. PO | `poNumber` | text | Tidak | - |
| Alamat | `toAddress` | textarea | Tidak | - |
| Kontak | `contactInfo` | lookup | Tidak | - |
| Pajak | `taxable`, `inclusiveTax` | checkbox, checkbox | Tidak | - |
| Kena Pajak | `taxable`, `inclusiveTax` | checkbox, checkbox | Tidak | - |
| Tgl Pengiriman | `shipDate` | date | Tidak | - |
| Pengiriman | `shipment` | lookup | Tidak | - |
| Auto tutup pesanan | `autoCloseVisible` | checkbox | Tidak | - |
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
| `customerFilter` — Dipesan oleh | Semua |
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
| `description` | Keterangan | Ya |
| `statusName` | Status | Ya |
| `availableDownPayment` | Sisa Uang Muka | Opsional |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `tax4Amount` | PPh 22 Impor | Opsional |
| `branch.name` | Cabang | Opsional |
| `taxable` | Kena Pajak | Opsional |
| `inclusiveTax` | Total termasuk Pajak | Opsional |
| `dppAmount` | DPP | Opsional |
| `tax3Amount` | PPh | Opsional |
| `masterSalesman.name` | Penjual Utama | Opsional |
| `totalDownPaymentUsed` | Uang Muka Terpakai/Retur | Opsional |
| `checked` | [Pilih] | Opsional |
| `createdByUserName` | Pembuat Data | Opsional |
| `percentShipped` | Terkirim (%) | Opsional |
| `totalDiscountDetail` | Diskon Barang | Opsional |
| `totalDiscount` | Total Diskon | Opsional |
| `printedByUser` | Dicetak/email | Opsional |
| `invoicePrintedTime` | Waktu cetak/email | Opsional |
| `customerNo` | ID Pelanggan | Opsional |
| `subTotal` | Sub Total | Opsional |
| `cashDiscPercent` | Diskon % | Opsional |
| `cashDiscount` | Diskon | Opsional |
| `totalDownPayment` | Uang Muka | Opsional |
| `tax1Amount` | Nilai PPN | Opsional |
| `tax2Amount` | Nilai PPNBM | Opsional |
| `totalExpense` | Biaya Lainnya | Opsional |
| `totalAmount` | Total | Ya |

## Sumber Data
- `/accurate/customer/sales-order.do`
- `/accurate/cu`
- `/accurate/inventory/`
- `/accurate/general-ledger/childwithtype-glaccount.do`
- `/accurate/company/`
- `/accurate/company/detail-`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

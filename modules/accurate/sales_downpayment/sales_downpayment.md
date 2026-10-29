# Uang Muka Penjualan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Faktur Penjualan, Uang Muka Penjualan |
| Pelanggan | `customer` | lookup | Ya | - |
| Tanggal | `transDate` | date | Ya | - |
| Uang Muka | `inputDownPayment` | number | Ya | - |
| No. PO | `poNumber` | text | Tidak | - |
| Pajak | `taxable`, `inclusiveTax` | checkbox, checkbox | Tidak | - |
| Kena Pajak | `taxable`, `inclusiveTax` | checkbox, checkbox | Tidak | - |
| Syarat Pembayaran | `paymentTerm` | lookup | Tidak | - |
| Alamat | `toAddress` | textarea | Tidak | - |
| Kontak | `contactInfo` | lookup | Tidak | - |

### Info Lainnya
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Keterangan | `description` | textarea | Tidak | - |

### Tombol Form
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
| `downPaymentUsed` | Uang Muka Terpakai/Retur | Opsional |
| `availableDownPayment` | Sisa Uang Muka | Opsional |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `branch.name` | Cabang | Opsional |
| `taxable` | Kena Pajak | Opsional |
| `inclusiveTax` | Total termasuk Pajak | Opsional |
| `dppAmount` | DPP | Opsional |
| `posPromotion.name` | Promo | Opsional |
| `taxNumber` | No. Faktur Pajak | Opsional |
| `dueDate` | Jatuh Tempo | Opsional |
| `masterProject.name` | Proyek Utama | Opsional |
| `masterPosSalesType.name` | Tipe Penjualan Utama | Opsional |
| `retailWpType` | Tipe ID Wajib Pajak | Ya |
| `pendingAmortized` | Pendapatan Tertunda | Opsional |
| `paidOverTotal` | Pendapatan Tertunda | Opsional |
| `cashierEmployee.name` | Kasir | Opsional |
| `hasExchangeInvoice` | Ditukar Faktur | Opsional |
| `masterDepartment.name` | Departemen Utama | Opsional |
| `taxType` | Detail Transaksi | Opsional |
| `arAccount.name` | Akun Piutang | Opsional |
| `efakturFileName` | File efaktur | Opsional |
| `vaNumber` | Nomor VA | Opsional |
| `subComp` | Sub Kode Perusahaan | Opsional |
| `checked` | [Pilih] | Opsional |
| `age` | Umur (hr) | Ya |
| `printedByUser` | Dicetak/email | Opsional |
| `invoicePrintedTime` | Waktu cetak/email | Opsional |
| `createdByUserName` | Pembuat Data | Opsional |
| `customerCategoryName` | Kategori Pelanggan | Opsional |
| `documentCodeName` | Jenis Dokumen | Opsional |
| `customerNo` | ID Pelanggan | Opsional |
| `orderDownPayment.number` | No. SO | Opsional |
| `subTotal` | Sub Total | Opsional |
| `tax1Amount` | Nilai PPN | Opsional |
| `tax2Amount` | Nilai PPNBM | Opsional |
| `totalAmount` | Total | Ya |
| `primeReceipt` | Pembayaran | Opsional |
| `taxReceipt` | Terima Pajak | Opsional |
| `primeReturn` | Retur | Opsional |
| `taxReturn` | Retur Pajak | Opsional |
| `primeOwing` | Piutang | Opsional |
| `taxOwing` | Piutang Pajak | Opsional |

## Sumber Data
- `/accurate/customer/sales-downpayment.do`
- `/accurate/cu`
- `/accurate/company/`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

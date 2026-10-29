# Retur Penjualan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Retur Penjualan |
| Pelanggan | `customer` | lookup | Ya | - |
| Tanggal | `transDate` | date | Ya | - |
| Retur dari | `returnType`, `invoice` | select, lookup | Ya | returnType: Faktur, Pengiriman, Tanpa Faktur, Uang Muka |
| Pengembalian Barang | `returnStatusType` | text | Tidak | - |
| Barang Dikembalikan | `returnStatusType` | text | Tidak | - |
| Barang TIDAK Dikembalikan | `returnStatusType` | text | Tidak | - |
| Sebagian Barang Dikembalikan | `returnStatusType` | text | Tidak | - |
| Dari Alamat | `toAddress` | textarea | Tidak | - |
| Pajak | `taxable`, `inclusiveTax` | checkbox, checkbox | Tidak | - |
| Kena Pajak | `taxable`, `inclusiveTax` | checkbox, checkbox | Tidak | - |
| Tgl Faktur Pajak | `taxDate` | date | Tidak | - |
| No Faktur Pajak | `taxNumber` | text | Tidak | - |
| No Dokumen Retur | `returnDocumentNumber` | text | Tidak | - |

### Detail
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Rincian Barang | `searchKeywordItem` | text | Ya | - |

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
| `returnTypeFilter` — Tipe Pengembalian | Semua |
| `hasUserPrintedFilter` — Sudah dicetak | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `number` | Nomor # | Ya |
| `transDate` | Tanggal | Ya |
| `customer.name` | Pelanggan | Ya |
| `currency.code` | Mata Uang | Opsional |
| `description` | Keterangan | Ya |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `tax4Amount` | PPh 22 Impor | Opsional |
| `branch.name` | Cabang | Opsional |
| `taxable` | Kena Pajak | Opsional |
| `inclusiveTax` | Total termasuk Pajak | Opsional |
| `dppAmount` | DPP | Opsional |
| `masterSalesman.name` | Penjual Utama | Opsional |
| `pendingAmortized` | Pendapatan Tertunda | Opsional |
| `cashierEmployee.name` | Kasir | Opsional |
| `createdByUserName` | Pembuat Data | Opsional |
| `returnType` | Tipe Pengembalian | Opsional |
| `invoiceNumber` | No. Referensi | Opsional |
| `customerNo` | ID Pelanggan | Opsional |
| `subTotal` | Sub Total | Opsional |
| `cashDiscPercent` | Diskon % | Opsional |
| `cashDiscount` | Diskon | Opsional |
| `tax1Amount` | Nilai PPN | Opsional |
| `tax2Amount` | Nilai PPNBM | Opsional |
| `totalExpense` | Biaya Lainnya | Opsional |
| `totalAmount` | Total | Ya |

## Sumber Data
- `/accurate/customer/sales-return.do`
- `/accurate/cu`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

# Pengiriman Pesanan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Pengiriman Pesanan |
| Kirim ke | `customer` | lookup | Ya | - |
| Tanggal | `transDate` | date | Ya | - |
| Pengiriman | `shipment` | lookup | Tidak | - |
| No. PO | `poNumber` | text | Tidak | - |
| Alamat | `toAddress` | textarea | Tidak | - |
| Kontak | `contactInfo` | lookup | Tidak | - |
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
| `customerFilter` — Kirim ke | Semua |
| `shipmentFilter` — Pengiriman | Semua |
| `statusFilter` — Status | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `number` | Nomor # | Ya |
| `transDate` | Tanggal | Ya |
| `customer.name` | Pelanggan | Ya |
| `toAddress` | Alamat | Opsional |
| `currency.code` | Mata Uang | Opsional |
| `poNumber` | No. PO | Opsional |
| `shipment.name` | Pengiriman | Ya |
| `description` | Keterangan | Ya |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `branch.name` | Cabang | Opsional |
| `canProcess` | Dapat diproses | Opsional |
| `masterSalesman.name` | Penjual Utama | Opsional |
| `printedByUser` | Dicetak/email | Opsional |
| `deliveryPrintedTime` | Waktu cetak/email | Opsional |
| `deliveryPackingNumber` | No Pengepakan | Opsional |
| `createdByUserName` | Pembuat Data | Opsional |
| `statusName` | Status | Ya |
| `customerNo` | ID Pelanggan | Opsional |
| `checked` | [Pilih] | Opsional |

## Sumber Data
- `/accurate/customer/delivery-order.do`
- `/accurate/cu`
- `/accurate/company/`
- `/accurate/company/detail-`
- `/accurate/inventory/`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

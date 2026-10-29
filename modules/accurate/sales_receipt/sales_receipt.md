# Penerimaan Penjualan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Bank, Deposito Bank, Kas & Bank, Kas Kecil, Nomor Bukti Kas/Bank, Setara Kas, Tunai |
| Terima dari | `customer` | lookup | Ya | - |
| Bank | `bank` | lookup | Ya | - |
| Nilai Pembayaran | `chequeAmount` | number | Tidak | - |
| Tgl Bayar | `transDate` | date | Ya | - |
| Faktur | `searchDetailInvoice`, `searchKeywordInvoice` | lookup, text | Ya | - |
| Metode Bayar | `paymentMethod` | select | Tidak | paymentMethod: Tunai, Cek/Giro, Transfer Bank, EDC, Kartu Debit, Kartu Kredit, QRIS, Payment Link, Virtual Account, Dompet Digital, Non Tunai Lainnya |

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
| `paymentMethodFilter` — Metode Bayar | Semua |
| `bankFilter` — Bank | Semua |
| `chequeDateFilter` — Tanggal Cek | Semua |
| `customerFilter` — Terima dari | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `number` | Nomor # | Ya |
| `transDate` | Tanggal | Ya |
| `chequeNo` | No. Cek | Ya |
| `chequeDate` | Tanggal Cek | Ya |
| `customer.name` | Pelanggan | Ya |
| `currency.name` | Mata Uang | Opsional |
| `bank.name` | Bank | Ya |
| `description` | Keterangan | Ya |
| `voidCheq` | Void | Opsional |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `branch.name` | Cabang | Opsional |
| `overPayUsed` | Kredit Terpakai | Opsional |
| `availableOverPay` | Sisa Kredit | Opsional |
| `useCredit` | Pakai Kredit | Ya |
| `uniqueNumberPayment` | Bayar (Kode Unik) | Opsional |
| `cashierEmployee.name` | Kasir | Opsional |
| `checked` | [Pilih] | Opsional |
| `createdByUserName` | Pembuat Data | Opsional |
| `paymentMethodName` | Metode Bayar | Opsional |
| `printedByUser` | Dicetak/email | Opsional |
| `printedTime` | Waktu cetak/email | Opsional |
| `customerNo` | ID Pelanggan | Opsional |
| `chequeAmount` | Nilai Pembayaran | Ya |
| `totalPayment` | Faktur Dibayar | Opsional |
| `totalDiscount` | Diskon | Opsional |
| `equivalentAmount` | Nilai Bayar | Opsional |

## Sumber Data
- `/accurate/customer/sales-receipt.do`
- `/accurate/cu`
- `/accurate/general-ledger/childwithtype-glaccount.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

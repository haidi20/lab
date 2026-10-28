# Analisa Sidebar Kiri Accurate Online

## Ringkasan

Hasil ini diambil dari halaman perusahaan `cy` pada Accurate Online versi
`v1.0.1#5010-<company-id>`. Analisa memakai REA melalui
`capture-browser-scenario`, `list-browser-targets`, dan
`inspect-web-page`.

Sidebar kiri menampilkan 10 menu utama berupa ikon. Nama menu tidak selalu
muncul di accessibility tree, sehingga identifikasi lengkap memakai judul
submenu dan anchor module pada DOM.

| No | Menu Utama | Jumlah Item |
| ---: | --- | ---: |
| 1 | Pengaturan | 6 |
| 2 | Perusahaan | 13 |
| 3 | Buku Besar | 9 |
| 4 | Kas & Bank | 9 |
| 5 | Penjualan | 15 |
| 6 | Pembelian | 11 |
| 7 | Persediaan | 16 |
| 8 | Aset Tetap | 7 |
| 9 | SmartLink Tax | 2 |
| 10 | Daftar Laporan | 3 |

Total item submenu yang terdeteksi: 91.

## Detail Menu

### 1. Pengaturan

| Menu | Module |
| --- | --- |
| Preferensi | `#accurate__company__preferences` |
| Akses Grup | `#accurate__company__access-privilege` |
| Pengguna | `#accurate__company__user-company` |
| Penomoran | `#accurate__company__auto-number` |
| Desain Cetakan | `#accurate__company__print-layout` |
| Accurate Store | `#accurate__company__application` |

### 2. Perusahaan

| Menu | Module |
| --- | --- |
| Cabang | `#accurate__company__branch` |
| Pajak | `#accurate__company__tax` |
| Syarat Pembayaran | `#accurate__company__payment-term` |
| Pengiriman | `#accurate__company__shipment` |
| FOB | `#accurate__company__freeonboard` |
| Gaji/Tunjangan | `#accurate__company__employee-fee` |
| Karyawan | `#accurate__company__employee` |
| Transaksi Berulang | `#accurate__company__recurring` |
| Proses Akhir Bulan | `#accurate__company__period-end` |
| Kontak | `#accurate__company__contact` |
| Transaksi Favorit | `#accurate__company__memorize-transaction` |
| Kalender | `#accurate__company__calendar` |
| Log Aktifitas | `#accurate__company__audit` |

### 3. Buku Besar

| Menu | Module |
| --- | --- |
| Akun Perkiraan | `#accurate__general-ledger__glaccount` |
| Pencatatan Beban | `#accurate__general-ledger__expense-accrual` |
| Pencatatan Gaji | `#accurate__cash-bank__employee-payment` |
| Jurnal Umum | `#accurate__general-ledger__journal-voucher` |
| Monitor Anggaran | `#accurate__budget-target__accountbudget-monitor` |
| Transfer Anggaran | `#accurate__budget-target__accountbudget-transfer` |
| Anggaran | `#accurate__budget-target__accountbudget-target` |
| Histori Akun | `#accurate__general-ledger__account-history` |
| Log Aktifitas Jurnal | `#accurate__company__audit-journal` |

### 4. Kas & Bank

| Menu | Module |
| --- | --- |
| Pembayaran | `#accurate__cash-bank__other-payment` |
| Penerimaan | `#accurate__cash-bank__other-deposit` |
| Transfer Bank | `#accurate__cash-bank__bank-transfer` |
| SmartLink e-Banking | `#accurate__cash-bank__internet-banking` |
| Rekening Koran | `#accurate__cash-bank__bank-statement` |
| Histori Bank | `#accurate__cash-bank__bank-book` |
| Rekonsiliasi Bank | `#accurate__cash-bank__bank-reconcile` |
| SmartLink Virtual Account | `#accurate__company__application-virtual-account` |
| SmartLink e-Payment | `#accurate__company__application-epayment` |

### 5. Penjualan

| Menu | Module |
| --- | --- |
| Penawaran Penjualan | `#accurate__customer__sales-quotation` |
| Pesanan Penjualan | `#accurate__customer__sales-order` |
| Pengiriman Pesanan | `#accurate__customer__delivery-order` |
| Uang Muka Penjualan | `#accurate__customer__sales-downpayment` |
| Faktur Penjualan | `#accurate__customer__sales-invoice` |
| Penerimaan Penjualan | `#accurate__customer__sales-receipt` |
| Retur Penjualan | `#accurate__customer__sales-return` |
| Kategori Pelanggan | `#accurate__customer__customer-category` |
| Kategori Penjualan | `#accurate__customer__price-category` |
| Pelanggan | `#accurate__customer__customer` |
| Penyesuaian Harga/Diskon | `#accurate__inventory__sellingprice-adjustment` |
| Komisi Penjual | `#accurate__company__salesman-commission` |
| Target Penjualan | `#accurate__budget-target__sales-target` |
| SmartLink e-Commerce | `#accurate__customer__ecommerce-setting` |
| Check In | `#accurate__customer__sales-check-in` |

### 6. Pembelian

| Menu | Module |
| --- | --- |
| Pesanan Pembelian | `#accurate__vendor__purchase-order` |
| Penerimaan Barang | `#accurate__vendor__receive-item` |
| Uang Muka Pembelian | `#accurate__vendor__purchase-downpayment` |
| Faktur Pembelian | `#accurate__vendor__purchase-invoice` |
| Pembayaran Pembelian | `#accurate__vendor__purchase-payment` |
| Retur Pembelian | `#accurate__vendor__purchase-return` |
| Harga Pemasok | `#accurate__inventory__vendor-price` |
| Kategori Pemasok | `#accurate__vendor__vendor-category` |
| Pemasok | `#accurate__vendor__vendor` |
| Perintah Pembayaran | `#accurate__vendor__transfer-order` |
| Transfer Pemasok | `#accurate__vendor__multi-vendor-transfer` |

### 7. Persediaan

| Menu | Module |
| --- | --- |
| Permintaan Barang | `#accurate__vendor__purchase-requisition` |
| Pemindahan Barang | `#accurate__inventory__item-transfer` |
| Penyesuaian Persediaan | `#accurate__inventory__item-adjustment` |
| Pekerjaan Pesanan | `#accurate__inventory__job-order` |
| Penambahan Bahan Baku | `#accurate__inventory__material-adjustment` |
| Penyelesaian Pesanan | `#accurate__inventory__roll-over` |
| Perintah Stok Opname | `#accurate__inventory__stock-opname-order` |
| Hasil Stok Opname | `#accurate__inventory__stock-opname-result` |
| Barang & Jasa | `#accurate__inventory__item` |
| Gudang | `#accurate__inventory__warehouse` |
| Satuan Barang | `#accurate__inventory__unit` |
| Kategori Barang | `#accurate__inventory__item-category` |
| Merek Barang | `#accurate__inventory__item-brand` |
| Pemenuhan Pesanan | `#accurate__inventory__backorder-inquiry` |
| Barang per Gudang | `#accurate__inventory__stock-warehouse` |
| Barang Stok Minimum | `#accurate__inventory__minimum-stock-item` |

### 8. Aset Tetap

| Menu | Module |
| --- | --- |
| Aset Tetap | `#accurate__fixed-asset__fixed-asset` |
| Kategori Aset | `#accurate__fixed-asset__fa-type` |
| Kategori Aset Tetap Pajak | `#accurate__fixed-asset__fiscal-fa-type` |
| Perubahan Aset Tetap | `#accurate__fixed-asset__fixed-asset-edited` |
| Disposisi Aset Tetap | `#accurate__fixed-asset__fixed-asset-disposed` |
| Pindah Aset | `#accurate__fixed-asset__asset-transfer` |
| Aset per Lokasi | `#accurate__fixed-asset__asset-location` |

### 9. SmartLink Tax

| Menu | Module |
| --- | --- |
| e-Faktur CTAS | `#accurate__company__efaktur-ctas` |
| Email Faktur Pajak | `#accurate__customer__efaktur-send` |

### 10. Daftar Laporan

| Menu | Module |
| --- | --- |
| Daftar Laporan | `#accurate__report__report` |
| SPT PPN / PPNBM | `#accurate__report__spt-masa` |
| Analisa AI | `#accurate__report-insight-analysis` |

## Tab Terbuka Saat Capture

Area tab di atas konten menampilkan:

- Dashboard
- Persiapan Data Perusahaan
- Berita

Bagian ini bukan bagian dari 10 ikon menu utama di sidebar kiri.

## Catatan Akses

Untuk membuka perusahaan secara langsung setelah login, Accurate memakai
pola:

```text
/accurate/open.do?uid=<unique-company-id>&product=aol
```

Parameter `id` tidak cukup. Halaman bisa terbuka sebagai shell kosong bila
memakai `id` saja. Analisa ini memakai `uid` perusahaan aktif dan product
`aol`.

Jumlah menu dapat berubah tergantung lisensi, fitur aktif, jenis produk,
dan hak akses pengguna.

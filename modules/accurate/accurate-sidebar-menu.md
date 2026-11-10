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

## Skill Untuk Pengerjaan Fitur

Skill berikut relevan untuk otomasi capture dan pengembangan fitur
berdasarkan daftar menu di atas.

### Wajib (Lokal)

| Skill | Fungsi |
| --- | --- |
| `skills/accurate-human-automation` | Wajib untuk semua otomasi Accurate: REA MCP / `capture-browser-scenario`, pace manusia, kredensial hanya dari `.env`. |

### Akuntansi dan Audit (Lokal)

Skill lokal berikut memahami proses akuntansi dan memetakan langsung ke
menu sidebar Accurate. Gunakan sesuai fitur yang dibangun.

| Skill | Menu Terkait | Fungsi |
| --- | --- | --- |
| `ask-accounting` | Semua | Router jika bingung memilih skill akuntansi mana. |
| `chart-of-accounts` | Buku Besar | Pemilihan COA dan overlay industri. |
| `classify-transactions` | Buku Besar, Kas & Bank | Klasifikasi transaksi ke COA, substanti MPERS/MFRS. |
| `journal-entries` | Buku Besar | Posting jurnal double-entry balancing, lalu roll TB. |
| `record-transactions` | Kas & Bank, Pembelian, Penjualan | Register multi-stream (bank, sales, purchases, payroll) dengan provenance. |
| `extract-bank-statement` | Kas & Bank | Ekstrak rekening koran PDF/CSV ke transaksi dengan bukti saldo. |
| `bank-reconciliation` | Kas & Bank | Rekonsiliasi bank GL ke statement. |
| `subledger-reconciliations` | Penjualan, Pembelian | Rekonsiliasi AR/AP dan subledger ke kontrol. |
| `adjusted-trial-balance` | Buku Besar | Neraca saldo setelah penyesuaian via roll_tb. |
| `year-end-adjustments` | Buku Besar, Proses Akhir Bulan | Katalog dan posting AJE akhir tahun (depresiasi, akrual, prabayar). |
| `revenue-recognition` | Penjualan | Pengakuan pendapatan MPERS/MFRS, cut-off, principal vs agent. |
| `capitalise-or-expense` | Aset Tetap, Pembelian | Analisis kapitalisasi vs beban untuk pengeluaran material. |
| `capex` | Aset Tetap | Cabang analisis kapitalisasi (PPE, renovasi, perbaikan). |
| `tax-computation` | SmartLink Tax | Perhitungan pajak dari akun (Form C, pajak penghasilan). |
| `do-books` | Semua | Entry point pengerjaan pembukuan penuh end-to-end. |

### Pelengkap (Eksternal)

| Skill | Installs | Fungsi | Install |
| --- | ---: | --- | --- |
| `vercel-labs/agent-skills@agent-browser` | 1.4M | Otomasi browser agent-grade untuk navigasi dan verifikasi DOM. | `npx skills add vercel-labs/agent-skills@agent-browser` |
| `microsoft/playwright-cli@playwright-cli` | 212.5K | Kontrol Playwright langsung untuk scraping tabel per menu. | `npx skills add microsoft/playwright-cli@playwright-cli` |
| `browser-use/browser-use@browser-use` | 99.4K | Otomasi browser berbasis AI sebagai alternatif. | `npx skills add browser-use/browser-use@browser-use` |

Catatan: skill eksternal tidak boleh menggantikan alur REA yang diwajibkan
`AGENTS.md` untuk Accurate; hanya pelengkap untuk kebutuhan umum di luar
capture Accurate. Skill eksternal akuntansi/audit yang tersedia saat pencarian
semuanya di bawah 2K installs dan generik, sehingga tidak direkomendasikan;
skill lokal di atas sudah lebih spesifik terhadap proses pembuatan fitur.

## Status Capture Per Menu

Per scan 10 November 2026: dari 46 folder menu, hanya 2 yang `data.json`-nya
terisi record hasil capture REA. Sisanya masih kosong (`record_count: 0`
atau belum ada `data.json`). Sesuai `AGENTS.md`, implementasi fitur Accurate
TIDAK BOLEH berdasar asumsi: kartu/fitur yang menunjuk menu belum-capture
WAJIB menjalankan capture REA dulu (`capture-browser-scenario`) sebelum
menulis migration/implementasi.

| Status | Menu | Kewajiban Sebelum Implementasi |
| --- | --- | --- |
| Tercapture | `audit`, `glaccount` | Langsung boleh implementasi; field mengikuti `data.json` + `<menu>.md`. |
| Belum capture | 44 folder lainnya | Capture REA dulu per menu, isi `data.json` (record asli) dan `<menu>.md`/`<menu>.json` (struktur form), baru implementasi. |

Daftar menu belum capture: `accountbudget_monitor`, `accountbudget_target`,
`accountbudget_transfer`, `account_history`, `application_epayment`,
`application_virtual_account`, `audit_journal`, `bank_book`,
`bank_reconcile`, `bank_statement`, `bank_transfer`, `branch`, `calendar`,
`contact`, `customer`, `customer_category`, `delivery_order`,
`ecommerce_setting`, `employee`, `employee_fee`, `employee_payment`,
`expense_accrual`, `freeonboard`, `internet_banking`, `journal_voucher`,
`memorize_transaction`, `other_deposit`, `other_payment`, `payment_term`,
`period_end`, `price_category`, `recurring`, `salesman_commission`,
`sales_check_in`, `sales_downpayment`, `sales_invoice`, `sales_order`,
`sales_quotation`, `sales_receipt`, `sales_return`, `sales_target`,
`sellingprice_adjustment`, `shipment`, `tax`.

Prioritas capture mengikuti prioritas kartu Trello: `sales_quotation`,
`sales_downpayment`, `payment_term`, `customer_category`, `price_category`,
`salesman_commission`, `sales_target`, lalu menu pembelian dan kas bank.

## Gap Menu vs Trello Klinik

Analisa board Trello `Inventory` (`vB4uz4Qb`) per 10 November 2026
menemukan menu berikut belum memiliki kartu. Satu kartu per gap, format
judul, deskripsi, dan checklist AC siap tempel ke Trello.

### 1. Aset Tetap

**Card:** `[MVP] Bangun modul fixed asset: kategori, lokasi, akuisisi, depresiasi, penjualan, dan penghapusan aset`

**Description:**

- Context: Menu Aset Tetap Accurate punya 7 item (akuisisi, depresiasi,
  penjualan aset, penghapusan, kategori, lokasi, laporan) tetapi board
  Trello klinik hanya punya satu kartu jurnal depreciation adjustment.
  Modul aset tetap belum ada sebagai fitur utuh.
- Acceptance Criteria:
  - [ ] CRUD kategori aset dan lokasi aset per tenant
  - [ ] Akuisisi aset: form input harga perolehan, tanggal, akun COA, dan jurnal otomatis
  - [ ] Depresiasi: method garis lurus dan saldo menurun, jurnal bulanan otomatis
  - [ ] Penjualan aset: hitung gain/loss, jurnal otomatis, bersihkan nilai buku
  - [ ] Penghapusan aset: jurnal penghapusan, nilai buku nol
  - [ ] Laporan daftar aset dan depresiasi per periode
  - [ ] PHPUnit untuk setiap alur di atas
- Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
- Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Aset Tetap.

### 2. SmartLink Tax

**Card:** `[MVP] Bangun modul e-Faktur: faktur pajak keluaran/masukan, email faktur, dan SPT PPN`

**Description:**

- Context: Menu SmartLink Tax Accurate punya e-Faktur CTAS dan email faktur
  pajak; daftar laporan punya SPT PPN/PPNBM. Board Trello klinik tidak
  punya satu pun kartu pajak (efaktur, SPT, PPN).
- Acceptance Criteria:
  - [ ] Generate faktur pajak keluaran dari sales invoice (NSFP, masa, tahun)
  - [ ] Catat faktur pajak masukan dari purchase invoice
  - [ ] Kirim faktur pajak via email ke pelanggan
  - [ ] Rekap PPN keluaran dan masukan per masa
  - [ ] Generate SPT PPN masa (CSV/format DJP) dari rekap
  - [ ] PHPUnit untuk generate, rekap, dan SPT
- Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
- Ref: `modules/accurate/accurate-sidebar-menu.md` bagian SmartLink Tax.

### 3. Kas & Bank

**Card:** `[MVP] Bangun modul bank: transfer antar rekening, rekonsiliasi bank, dan import rekening koran`

**Description:**

- Context: Pembayaran/penerimaan sudah ada via piutang-hutang, tetapi
  transfer bank antar rekening sendiri, rekonsiliasi bank, dan import
  rekening koran belum ada kartunya.
- Acceptance Criteria:
  - [ ] Transfer bank antar rekening: jurnal dua sisi otomatis
  - [ ] Import rekening koran CSV/MT940 ke draft transaksi
  - [ ] Rekonsiliasi: match statement ke transaksi GL, hitung selisih
  - [ ] Laporan histori bank (bank book) per rekening per periode
  - [ ] PHPUnit untuk transfer, import, dan rekonsiliasi
- Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
- Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Kas & Bank.

### Perencanaan Lengkap Per Menu

Rencana migration (table fields), form input (field-by-field), tab layout,
dan business flow per card tersimpan lengkap di
`modules/accurate/trello-gap-cards.md`. Ringkasan di bawah merujuk card
tersebut sebagai sumber detail.

| Menu | Card | Tab Layout | Tabel Utama | Form Input Ringkas | Business Flow |
| --- | --- | --- | --- | --- | --- |
| Aset Tetap | 1 | Ya — 3 tab: Informasi, Depresiasi, Penghapusan | `asset_categories`, `asset_locations`, `fixed_assets`, `fixed_asset_depreciations`, `fixed_asset_disposals` | Kode, nama, kategori, lokasi, cabang, tanggal, harga, salvage, masa manfaat, metode depresiasi, akun COA | Akuisisi → jurnal Debit FA / Kredit Kas-AP → depresiasi bulanan → penjualan (gain/loss) → penghapusan → laporan |
| SmartLink Tax | 2 | Ya — faktur: 2 tab (Informasi, Email); SPT: single form | `tax_invoices`, `tax_invoice_emails`, `spt_ppn_filings` | Tipe (output/input), NSFP, masa, tahun, dokumen sumber, DPP, PPN, email tujuan | Sales invoice → faktur keluaran → email → rekap per masa → SPT CSV DJP → filed |
| Kas & Bank | 3 | Ya — 3 tab: Transfer, Import Statement, Rekonsiliasi | `bank_transfers`, `bank_statements`, `bank_statement_lines`, `bank_reconciliations` | Transfer: rekening asal/tujuan, jumlah, fee. Import: file CSV/MT940, saldo awal/akhir. Rekonsiliasi: rekening, periode, match, selisih | Transfer → jurnal 2 sisi. Import → parse → validasi. Rekonsiliasi → auto/manual match → jurnal penyesuaian → bank book |
| Perusahaan | 4 | Ya — Karyawan 2 tab (Informasi, Komponen Gaji); master lain single form | `payment_terms`, `shipments`, `free_on_boards`, `employees`, `employee_fees`, `document_sequences` | Payment term: nama, tipe, hari. Karyawan: nama, NIK, jabatan, gaji. Penomoran: tipe dok, prefix, padding | Payment term → due_date invoice. Shipment/FOB → dropdown di SO/DO. Karyawan → komponen gaji → payroll. Penomoran → prefix per cabang per tipe |
| Penjualan | 5 | Ya — Quotation 2 tab (Informasi, Detail Item); lainnya single form | `sales_quotations(+items)`, `sales_down_payments`, `customer_categories`, `price_categories`, `sales_commissions`, `sales_targets` | Quotation: pelanggan, item (produk, qty, harga, diskon). DP: pelanggan, jumlah, rekening. Komisi: salesman, rate, invoice. Target: karyawan/cabang, periode, jumlah | Quotation → won → konversi SO. DP → terima → alokasi ke invoice. Komisi → hitung per invoice → paid. Target → capaian vs aktual |
| Pembelian | 6 | Ya — Perintah Pembayaran 2 tab (Informasi, Detail multi-vendor); lainnya single form | `purchase_down_payments`, `vendor_prices`, `vendor_categories`, `transfer_orders(+payments)` | DP: pemasok, jumlah, rekening. Harga: pemasok, produk, harga, qty min, tgl efektif. Transfer order: pemasok, invoice hutang, jumlah | DP → bayar → alokasi faktur. Harga → suggest di PO. Perintah pembayaran → approve → transfer → jurnal Debit AP / Kredit Kas |
| Buku Besar | 7 | Ya — 4 sub-fitur: Anggaran, Transfer Anggaran, Pencatatan Beban, Histori Akun | `account_budgets`, `account_budget_transfers`, `expense_accruals` | Anggaran: cabang, akun, periode, target. Transfer: dari/ke budget, jumlah. Beban: akun, jumlah, tanggal. Histori: filter akun + periode (report-only) | Set budget → jurnal update actual → monitor vs target. Transfer antar akun. Akrual → reversing entry. Histori: drill-down per akun |
| Persediaan | 8 | Ya — Material Requisition 2 tab (Informasi, Detail Item); Serial/Batch single form | `product_serials`, `product_batches`, `material_requisitions(+items)` | Serial: produk, nomor seri, status, gudang. Batch: produk, nomor batch, expiry. Requisition: cabang, BOM/assembly, item (produk, qty) | GR → assign serial/batch. Penjualan → pilih serial → sold. Batch → FEFO picking. Requisition → approve → fulfil → stock movement dengan batch/serial trace |
| Daftar Laporan | 9 | Tidak — report-only dengan filter | `report_insights` | Filter: tipe laporan, periode, tipe insight (trend/anomaly/summary) | Scheduled/manual → baca laporan → analisa tren/anomali → simpan insight → tampilkan di dashboard |

Detail lengkap (migration plan, field-by-field, tab layout dengan alasan,
dan business flow step-by-step) ada di
`modules/accurate/trello-gap-cards.md` bagian card 1-9.

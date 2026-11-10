# Gap Cards Trello Klinik vs Menu Accurate

Sumber: `accurate-sidebar-menu.md` vs board Trello `Inventory` (`vB4uz4Qb`).
Per analisa 10 November 2026. Satu kartu per gap, siap tempel ke Trello.
Konvensi global semua migration: primary key UUID (uuid, unique), kolom
`tenant_id` (uuid, FK `tenants.id`), `created_at`/`updated_at`
(timestamp, nullable), `deleted_at` (timestamp, nullable, soft delete),
dan FK dengan `onDelete: restrict` kecuali disebut lain.

Referensi dokumentasi per menu ada di folder
`modules/accurate/<menu>/` — setiap folder berisi `<menu>.md`
(dokumentasi form/field/filter), `<menu>.json` (struktur form), dan
`data.json` (data tabel hasil capture). Kartu pecahan di bawah merujuk
folder terkait sebagai sumber field dan alur form.

---

## 1. Aset Tetap

**Card:** `[MVP] Bangun modul fixed asset: kategori, lokasi, akuisisi, depresiasi, penjualan, dan penghapusan aset`

**Description:**

Context: Menu Aset Tetap Accurate punya 7 item (akuisisi, depresiasi,
penjualan aset, penghapusan, kategori, lokasi, laporan) tetapi board
Trello klinik hanya punya satu kartu jurnal depreciation adjustment.
Modul aset tetap belum ada sebagai fitur utuh.

**Migration Plan:**

Tabel `asset_categories`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| name | varchar(100) | unique per tenant |
| accumulation_account_id | uuid | FK `gl_accounts.id` (akumulasi depresiasi) |
| depreciation_expense_account_id | uuid | FK `gl_accounts.id` (beban depresiasi) |
| gain_account_id | uuid | FK `gl_accounts.id` (gain penjualan aset) |
| loss_account_id | uuid | FK `gl_accounts.id` (loss penjualan/penghapusan) |

Tabel `asset_locations`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| branch_id | uuid, nullable | FK `branches.id` |
| name | varchar(100) | unique per tenant+branch |

Tabel `fixed_assets`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| branch_id | uuid | FK `branches.id` |
| asset_category_id | uuid | FK `asset_categories.id` |
| asset_location_id | uuid, nullable | FK `asset_locations.id` |
| code | varchar(50) | unique per tenant |
| name | varchar(150) | - |
| acquisition_journal_id | uuid | FK `general_journals.id` (jurnal akuisisi) |
| acquisition_date | date | - |
| cost | decimal(18,2) | harga perolehan |
| salvage_value | decimal(18,2), default 0 | nilai sisa |
| useful_life_months | integer | masa manfaat |
| depreciation_method | enum: straight_line, declining_balance | default straight_line |
| accumulated_depreciation | decimal(18,2), default 0 | di-update saat posting depresiasi |
| status | enum: active, sold, disposed | default active |
| sold_at / disposed_at | date, nullable | - |

Tabel `fixed_asset_depreciations`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| fixed_asset_id | uuid | FK `fixed_assets.id` |
| period | char(7) YYYY-MM | unique(fixed_asset_id, period) |
| amount | decimal(18,2) | beban periode |
| journal_id | uuid | FK `general_journals.id` |

Tabel `fixed_asset_disposals`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| fixed_asset_id | uuid | FK `fixed_assets.id` |
| type | enum: sale, disposal | - |
| date | date | - |
| proceeds | decimal(18,2), nullable | harga jual (type=sale) |
| gain_loss | decimal(18,2) | hasil perhitungan |
| journal_id | uuid | FK `general_journals.id` |

**Checklist (Acceptance Criteria):**

- [ ] CRUD kategori aset dan lokasi aset per tenant
- [ ] Akuisisi aset: harga perolehan, tanggal, akun COA, jurnal otomatis
- [ ] Depresiasi: garis lurus dan saldo menurun, jurnal bulanan otomatis
- [ ] Penjualan aset: hitung gain/loss, jurnal otomatis, nilai buku bersih
- [ ] Penghapusan aset: jurnal penghapusan, nilai buku nol
- [ ] Laporan daftar aset dan depresiasi per periode
- [ ] PHPUnit untuk setiap alur di atas

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Aset Tetap.

---

## 2. SmartLink Tax

**Card:** `[MVP] Bangun modul e-Faktur: faktur pajak keluaran/masukan, email faktur, dan SPT PPN`

**Description:**

Context: Menu SmartLink Tax Accurate punya e-Faktur CTAS dan email faktur
pajak; daftar laporan punya SPT PPN/PPNBM. Board Trello klinik tidak punya
satu pun kartu pajak (efaktur, SPT, PPN).

**Migration Plan:**

Tabel `tax_invoices`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| branch_id | uuid | FK `branches.id` |
| type | enum: output, input | output = keluaran, input = masukan |
| nsfp | varchar(30), nullable | nomor seri faktur pajak |
| tax_period | char(2) MM | - |
| tax_year | char(4) YYYY | - |
| invoiceable_type / invoiceable_id | morph | ke sales invoices / purchase invoices |
| counterparty_name | varchar(150) | snapshot nama pembeli/pemasok |
| counterparty_npwp | varchar(25), nullable | snapshot NPWP |
| counterparty_address | text, nullable | snapshot alamat |
| dpp_amount | decimal(18,2) | dasar pengenaan pajak |
| vat_amount | decimal(18,2) | PPN |
| status | enum: draft, issued, sent | default draft |
| unique | - | (tenant_id, type, nsfp) |

Tabel `tax_invoice_emails`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tax_invoice_id | uuid | FK `tax_invoices.id` |
| email | varchar(150) | tujuan |
| sent_at | timestamp, nullable | - |
| status | enum: pending, sent, failed | default pending |

Tabel `spt_ppn_filings`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| tax_period | char(2) MM | unique(tenant_id, tax_period, tax_year) |
| tax_year | char(4) YYYY | - |
| output_vat_total | decimal(18,2) | rekap PPN keluaran |
| input_vat_total | decimal(18,2) | rekap PPN masukan |
| payable_amount | decimal(18,2) | output - input |
| document_path | varchar(255), nullable | file CSV format DJP |
| status | enum: draft, filed | default draft |

**Checklist (Acceptance Criteria):**

- [ ] Generate faktur pajak keluaran dari sales invoice (NSFP, masa, tahun)
- [ ] Catat faktur pajak masukan dari purchase invoice
- [ ] Kirim faktur pajak via email ke pelanggan
- [ ] Rekap PPN keluaran dan masukan per masa
- [ ] Generate SPT PPN masa (CSV/format DJP) dari rekap
- [ ] PHPUnit untuk generate, rekap, dan SPT

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian SmartLink Tax.

---

## 3. Kas & Bank

**Card:** `[MVP] Bangun modul bank: transfer antar rekening, rekonsiliasi bank, dan import rekening koran`

**Description:**

Context: Pembayaran/penerimaan sudah ada via piutang-hutang, tetapi
transfer bank antar rekening, rekonsiliasi bank, dan import rekening
koran belum ada kartunya.

**Migration Plan:**

Tabel `bank_transfers`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| from_account_id | uuid | FK `cash_bank_accounts.id` |
| to_account_id | uuid | FK `cash_bank_accounts.id` |
| amount | decimal(18,2) | - |
| fee | decimal(18,2), default 0 | biaya transfer |
| date | date | - |
| reference | varchar(100), nullable | - |
| journal_id | uuid | FK `general_journals.id` (jurnal dua sisi + fee) |

Tabel `bank_statements`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| cash_bank_account_id | uuid | FK `cash_bank_accounts.id` |
| period_start / period_end | date | unique(account_id, period_start) |
| opening_balance / closing_balance | decimal(18,2) | - |
| source | enum: csv, mt940 | - |
| uploaded_by | uuid | FK `users.id` |

Tabel `bank_statement_lines`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| bank_statement_id | uuid | FK `bank_statements.id` |
| line_no | integer | unique(statement_id, line_no) |
| date | date | - |
| description | varchar(255) | - |
| amount_in / amount_out | decimal(18,2), default 0 | - |
| match_type | enum: auto, manual, unmatched | default unmatched |
| matchable_type / matchable_id | morph, nullable | ke transaksi GL terkait |
| status | enum: pending, matched, adjusted | - |

Tabel `bank_reconciliations`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| bank_statement_id | uuid | FK `bank_statements.id`, unique |
| cash_bank_account_id | uuid | FK `cash_bank_accounts.id` |
| matched_count / unmatched_count | integer | - |
| difference | decimal(18,2) | selisih akhir |
| adjustment_journal_id | uuid, nullable | FK `general_journals.id` (jurnal penyesuaian selisih) |
| reconciled_at | timestamp, nullable | - |
| reconciled_by | uuid, nullable | FK `users.id` |

**Checklist (Acceptance Criteria):**

- [ ] Transfer bank antar rekening: jurnal dua sisi otomatis
- [ ] Import rekening koran CSV/MT940 ke draft transaksi
- [ ] Rekonsiliasi: match statement ke transaksi GL, hitung selisih
- [ ] Laporan histori bank (bank book) per rekening per periode
- [ ] PHPUnit untuk transfer, import, dan rekonsiliasi

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Kas & Bank.

---

## 4. Perusahaan / Pengaturan

**Card:** `[MVP] Lengkapi master perusahaan: payment term, shipment, FOB, karyawan, dan penomoran otomatis`

**Description:**

Context: Board Trello klinik belum punya kartu untuk syarat pembayaran
(payment term), pengiriman (shipment), FOB, payroll/karyawan, dan
penomoran dokumen otomatis. Payment term memengaruhi jatuh tempo invoice
penjualan dan pembelian.

**Migration Plan:**

Tabel `payment_terms`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| name | varchar(100) | unique per tenant |
| days | integer | jatuh tempo X hari |
| is_eom | boolean, default false | end of month |

Tabel `shipments`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| name | varchar(100) | unique per tenant |
| description | varchar(255), nullable | - |

Tabel `free_on_boards`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| name | varchar(100) | unique per tenant (mis. FOB Origin, FOB Destination) |

Tabel `employees`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| branch_id | uuid, nullable | FK `branches.id` |
| user_id | uuid, nullable | FK `users.id` (link akun login) |
| name | varchar(150) | - |
| npwp | varchar(25), nullable | - |
| join_date | date | - |
| status | enum: active, inactive | default active |

Tabel `employee_fees`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| employee_id | uuid | FK `employees.id` |
| type | enum: salary, allowance, deduction | - |
| name | varchar(100) | nama komponen |
| amount | decimal(18,2) | - |
| effective_date | date | - |

Tabel `document_sequences`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| branch_id | uuid | FK `branches.id` |
| document_type | enum: sales_order, sales_invoice, purchase_order, purchase_invoice, journal, payment | unique(tenant_id, branch_id, document_type) |
| prefix | varchar(20) | - |
| next_number | bigInteger, default 1 | di-increment atomik (locking) |
| padding | integer, default 5 | panjang digit |

ALTER tabel yang sudah ada:

| Tabel | Kolom baru | Type / Relasi |
| --- | --- | --- |
| sales invoices, purchase invoices | payment_term_id | uuid, nullable, FK `payment_terms.id` |
| sales invoices, purchase invoices | due_date | date, nullable, dihitung dari payment term |

**Checklist (Acceptance Criteria):**

- [ ] CRUD payment term (net X hari, EOM) dan integrasi jatuh tempo invoice
- [ ] CRUD shipment dan FOB sebagai master sederhana
- [ ] CRUD karyawan, gaji/tunjangan, dan komponen payroll dasar
- [ ] Penomoran otomatis per dokumen per cabang (SO, invoice, PO, jurnal)
- [ ] PHPUnit untuk setiap master di atas

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Perusahaan dan Pengaturan.

---

## 5. Penjualan

**Card:** `[MVP] Lengkapi siklus penjualan: quotation, down payment, kategori pelanggan, komisi, dan target`

**Description:**

Context: SO, DO, invoice, retur, dan piutang sudah ada di board, tetapi
penawaran (quotation), uang muka penjualan, kategori pelanggan, kategori
harga, komisi penjual, target penjualan, dan check-in belum ada kartunya.

**Migration Plan:**

Tabel `sales_quotations` (pola kolom mengikuti `sales_orders` yang ada):

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| branch_id | uuid | FK `branches.id` |
| customer_id | uuid | FK `customers.id` |
| document_number | varchar(50) | unique per tenant |
| quotation_date | date | - |
| valid_until | date, nullable | - |
| status | enum: draft, sent, won, lost, expired | default draft |
| converted_sales_order_id | uuid, nullable | FK `sales_orders.id` (isi saat konversi) |
| subtotal / discount_total / tax_total / grand_total | decimal(18,2) | snapshot |

Tabel `sales_quotation_items`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| sales_quotation_id | uuid | FK `sales_quotations.id` |
| product_id | uuid | FK `products.id` |
| quantity | decimal(18,4) | - |
| price / discount / total | decimal(18,2) | snapshot harga |

Tabel `sales_down_payments`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| customer_id | uuid | FK `customers.id` |
| amount | decimal(18,2) | diterima |
| allocated_amount | decimal(18,2), default 0 | teralokasi ke invoice |
| journal_id | uuid | FK `general_journals.id` |
| date | date | - |

Tabel `customer_categories` dan `price_categories`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| name | varchar(100) | unique per tenant |

Tabel `sales_commissions`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| employee_id | uuid | FK `employees.id` |
| sales_invoice_id | uuid | FK `sales_invoices.id` |
| rate | decimal(5,2) | persen |
| amount | decimal(18,2) | rate x nilai invoice |
| status | enum: accrued, paid | default accrued |
| journal_id | uuid, nullable | FK `general_journals.id` saat accrue |

Tabel `sales_targets`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| employee_id | uuid, nullable | FK `employees.id` |
| branch_id | uuid, nullable | FK `branches.id` (salah satu wajib) |
| period | char(7) YYYY-MM | unique(tenant_id, employee_id, period) |
| target_amount | decimal(18,2) | - |

ALTER tabel yang sudah ada:

| Tabel | Kolom baru | Type / Relasi |
| --- | --- | --- |
| customers | customer_category_id | uuid, nullable, FK `customer_categories.id` |
| sales invoices | price_category_id | uuid, nullable, FK `price_categories.id` |

**Checklist (Acceptance Criteria):**

- [ ] Quotation: CRUD dan konversi ke sales order
- [ ] Uang muka penjualan: penerimaan DP dan alokasi ke invoice
- [ ] Kategori pelanggan dan kategori harga: CRUD dan terpakai di invoice
- [ ] Komisi penjual: perhitungan per transaksi dan laporan
- [ ] Target penjualan: set target per periode dan laporan capaian
- [ ] PHPUnit untuk setiap alur di atas

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Penjualan.

---

## 6. Pembelian

**Card:** `[MVP] Lengkapi siklus pembelian: down payment, harga pemasok, kategori pemasok, dan transfer pemasok`

**Description:**

Context: PO, GR, invoice, 3-way matching, pembayaran, dan retur sudah
ada di board, tetapi uang muka pembelian, harga pemasok, kategori
pemasok, perintah pembayaran, dan transfer pemasok belum ada kartunya.

**Migration Plan:**

Tabel `purchase_down_payments`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| vendor_id | uuid | FK `vendors.id` |
| amount | decimal(18,2) | dibayar |
| allocated_amount | decimal(18,2), default 0 | teralokasi ke faktur |
| journal_id | uuid | FK `general_journals.id` |
| date | date | - |

Tabel `vendor_prices`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| vendor_id | uuid | FK `vendors.id` |
| product_id | uuid | FK `products.id` |
| price | decimal(18,2) | - |
| min_qty | decimal(18,4), default 1 | - |
| effective_date | date | unique(vendor_id, product_id, effective_date) |

Tabel `vendor_categories`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| name | varchar(100) | unique per tenant |

Tabel `transfer_orders` (perintah pembayaran):

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| document_number | varchar(50) | unique per tenant |
| date | date | - |
| status | enum: draft, approved, paid, cancelled | default draft |
| journal_id | uuid, nullable | FK `general_journals.id` |

Tabel `transfer_order_payments`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| transfer_order_id | uuid | FK `transfer_orders.id` |
| vendor_id | uuid | FK `vendors.id` |
| payable_invoice_id | uuid, nullable | FK `purchase_invoices.id` |
| amount | decimal(18,2) | - |

ALTER tabel yang sudah ada:

| Tabel | Kolom baru | Type / Relasi |
| --- | --- | --- |
| vendors | vendor_category_id | uuid, nullable, FK `vendor_categories.id` |

**Checklist (Acceptance Criteria):**

- [ ] Uang muka pembelian: bayar DP dan alokasi ke faktur
- [ ] Harga pemasok per produk: CRUD dan terpakai saat buat PO
- [ ] Kategori pemasok: CRUD dan filter di list pemasok
- [ ] Perintah pembayaran dan transfer pemasok: alur multi-vendor transfer
- [ ] PHPUnit untuk setiap alur di atas

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Pembelian.

---

## 7. Buku Besar

**Card:** `[MVP] Lengkapi buku besar: anggaran per akun, monitor anggaran, dan histori akun`

**Description:**

Context: COA, jurnal, dan laporan keuangan sudah ada di board, tetapi
anggaran (budget), monitor anggaran, transfer anggaran, pencatatan
beban, dan histori akun belum ada kartunya.

**Migration Plan:**

Tabel `account_budgets`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| branch_id | uuid | FK `branches.id` |
| gl_account_id | uuid | FK `gl_accounts.id` |
| period | char(7) YYYY-MM | unique(branch_id, gl_account_id, period) |
| target_amount | decimal(18,2) | anggaran |
| actual_amount | decimal(18,2), default 0 | di-update dari posting jurnal |

Tabel `account_budget_transfers`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| from_budget_id | uuid | FK `account_budgets.id` |
| to_budget_id | uuid | FK `account_budgets.id` |
| amount | decimal(18,2) | - |
| journal_id | uuid, nullable | FK `general_journals.id` bila perlu jurnal |
| date | date | - |

Tabel `expense_accruals`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| gl_account_id | uuid | FK `gl_accounts.id` (akun beban) |
| amount | decimal(18,2) | - |
| accrual_date | date | - |
| accrual_journal_id | uuid | FK `general_journals.id` |
| reversal_journal_id | uuid, nullable | FK `general_journals.id` |
| status | enum: accrued, reversed | default accrued |

Histori akun: tidak butuh tabel baru — report-only dari `general_journals`
yang sudah ada; tambah composite index `(gl_account_id, date)` jika belum.

**Checklist (Acceptance Criteria):**

- [ ] Anggaran per akun per periode: CRUD
- [ ] Monitor anggaran: realisasi vs anggaran, indikator melebihi budget
- [ ] Transfer anggaran antar akun
- [ ] Histori akun: riwayat mutasi per akun dengan drill-down transaksi
- [ ] PHPUnit untuk anggaran, monitor, dan histori

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Buku Besar.

---

## 8. Persediaan

**Card:** `[Non-MVP] Lengkapi persediaan: nomor seri, tracking batch per lot, dan permintaan material produksi`

**Description:**

Context: Item, unit, gudang, transfer, adjustment, opname, BOM, dan
assembly sudah ada di board, tetapi nomor seri, tracking batch detail
per lot, dan permintaan material produksi belum ada kartunya.

**Migration Plan:**

Tabel `product_serials`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| product_id | uuid | FK `products.id` |
| serial_number | varchar(100) | unique(tenant_id, product_id, serial_number) |
| status | enum: in_stock, sold, returned | default in_stock |
| received_item_id | uuid, nullable | FK ke tabel penerimaan barang (GR items) |
| sales_item_id | uuid, nullable | FK ke tabel sales invoice items |
| warehouse_id | uuid, nullable | FK `warehouses.id` |

Tabel `product_batches`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| product_id | uuid | FK `products.id` |
| batch_number | varchar(100) | unique(tenant_id, product_id, batch_number) |
| expiry_date | date, nullable | untuk FEFO |
| received_item_id | uuid, nullable | FK ke GR items |

Tabel `material_requisitions`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| branch_id | uuid | FK `branches.id` |
| document_number | varchar(50) | unique per tenant |
| bom_id | uuid, nullable | FK ke tabel BOM |
| assembly_id | uuid, nullable | FK ke tabel assembly |
| status | enum: draft, approved, fulfilled, cancelled | default draft |

Tabel `material_requisition_items`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| material_requisition_id | uuid | FK `material_requisitions.id` |
| product_id | uuid | FK `products.id` |
| quantity | decimal(18,4) | - |
| fulfilled_quantity | decimal(18,4), default 0 | - |

ALTER tabel yang sudah ada:

| Tabel | Kolom baru | Type / Relasi |
| --- | --- | --- |
| stock movements | batch_id | uuid, nullable, FK `product_batches.id` |
| stock movements | serial_id | uuid, nullable, FK `product_serials.id` |

**Checklist (Acceptance Criteria):**

- [ ] Nomor seri: assign saat penerimaan, track saat keluar
- [ ] Batch/lot: expiry date per lot dan FEFO saat picking
- [ ] Permintaan material produksi: requisition ke BOM/assembly
- [ ] Laporan umur stok per batch/seri
- [ ] PHPUnit untuk setiap alur di atas

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Persediaan.

---

## 9. Daftar Laporan

**Card:** `[Non-MVP] Tambah analisa AI laporan: insight otomatis dari laporan keuangan dan penjualan`

**Description:**

Context: Laporan keuangan inti sudah ada di board, tetapi fitur analisa
AI/insight (menu Daftar Laporan Accurate) belum ada kartunya.

**Migration Plan:**

Tabel `report_insights`:

| Field | Type | Relasi / Keterangan |
| --- | --- | --- |
| id | uuid PK | unique |
| tenant_id | uuid | FK `tenants.id` |
| report_type | enum: financial, sales, inventory | sumber laporan |
| period_start / period_end | date | rentang analisa |
| insight_type | enum: trend, anomaly, summary | - |
| payload | json | hasil insight (tren, anomali, narasi) |
| generated_at | timestamp | - |
| generated_by | enum: system, user-triggered | - |

Tidak ada FK ke data transaksi; insight dibaca dari laporan yang sudah
ada sehingga migration tetap ringan.

**Checklist (Acceptance Criteria):**

- [ ] Insight otomatis: tren revenue, expense, margin per periode
- [ ] Anomali: deteksi fluktuasi tidak wajar di akun utama
- [ ] Ringkasan naratif dari laporan keuangan
- [ ] PHPUnit untuk generator insight

Definition of Done: PHPUnit lulus, Pint + PHPStan clean, `_progress.md` update.
Ref: `modules/accurate/accurate-sidebar-menu.md` bagian Daftar Laporan.

---

## Pecahan Kartu (1 Kartu = 1-3 Hari Kerja)

Kartu induk di atas dipecah mengikuti aturan ukuran kartu Trello.
Migration Plan pada kartu induk tetap jadi sumber acuan; setiap kartu
pecahan mengerjakan subset tabelnya. Urutan prioritas: 1A-6A dulu
(paling dekat siklus MVP), lalu 4A (dependensi invoice), sisanya
mengikuti kapasitas.

### 1A. Aset Tetap - Master dan Akuisisi

**Card:** `[MVP] Aset tetap: master kategori, lokasi, dan akuisisi aset`

- Checklist: CRUD kategori/lokasi; form akuisisi; jurnal akuisisi otomatis;
  list aset aktif; PHPUnit master + akuisisi.
- Migration: `asset_categories`, `asset_locations`, `fixed_assets` (status
  active saja; kolom depresiasi/disposal menyusul di 1B/1C).
- Ref folder: `modules/accurate/glaccount/` (akun COA terkait).

### 1B. Aset Tetap - Depresiasi

**Card:** `[MVP] Aset tetap: engine depresiasi garis lurus dan saldo menurun`

- Checklist: kalkulasi straight line dan declining balance; posting jurnal
  bulanan; cegah duplikat per periode; laporan depresiasi; PHPUnit.
- Migration: `fixed_asset_depreciations`; ALTER `fixed_assets` tambah kolom
  `accumulated_depreciation`, `depreciation_method`, `useful_life_months`.
- Ref folder: `modules/accurate/expense_accrual/` (pola jurnal beban).

### 1C. Aset Tetap - Penjualan, Penghapusan, Laporan

**Card:** `[MVP] Aset tetap: penjualan aset, penghapusan, dan laporan`

- Checklist: penjualan dengan gain/loss; penghapusan; nilai buku nol;
  laporan daftar aset; PHPUnit.
- Migration: `fixed_asset_disposals`.
- Ref folder: `modules/accurate/journal_voucher/` (pola jurnal manual).

### 2A. SmartLink Tax - Faktur Pajak

**Card:** `[MVP] e-Faktur: generate faktur pajak keluaran dan catat masukan`

- Checklist: generate dari sales invoice; catat dari purchase invoice;
  NSFP dan masa/tahun; list dan detail faktur; PHPUnit.
- Migration: `tax_invoices`.
- Ref folder: `modules/accurate/sales_invoice/`, `modules/accurate/tax/`.

### 2B. SmartLink Tax - Email Faktur

**Card:** `[MVP] e-Faktur: kirim faktur pajak via email`

- Checklist: kirim ke email pelanggan; log status kirim; retry manual;
  PHPUnit.
- Migration: `tax_invoice_emails`.
- Ref folder: `modules/accurate/sales_invoice/` (lampiran dan dokumen).

### 2C. SmartLink Tax - Rekap dan SPT

**Card:** `[MVP] Pajak: rekap PPN per masa dan generate SPT PPN`

- Checklist: rekap keluaran/masukan; hitung kurang/lebih bayar; export CSV
  DJP; status filed; PHPUnit.
- Migration: `spt_ppn_filings`.
- Ref folder: `modules/accurate/tax/`.

### 3A. Kas & Bank - Transfer Antar Rekening

**Card:** `[MVP] Bank: transfer antar rekening dengan jurnal otomatis`

- Checklist: form transfer; jurnal dua sisi + fee; list transfer; PHPUnit.
- Migration: `bank_transfers`.
- Ref folder: `modules/accurate/bank_transfer/`.

### 3B. Kas & Bank - Import Rekening Koran

**Card:** `[MVP] Bank: import rekening koran CSV dan MT940`

- Checklist: upload dan parse CSV/MT940; validasi saldo; draft lines;
  PHPUnit parser.
- Migration: `bank_statements`, `bank_statement_lines`.
- Ref folder: `modules/accurate/bank_statement/`.

### 3C. Kas & Bank - Rekonsiliasi dan Bank Book

**Card:** `[MVP] Bank: rekonsiliasi statement ke GL dan laporan bank book`

- Checklist: match auto/manual; selisih; jurnal penyesuaian; laporan bank
  book; PHPUnit.
- Migration: `bank_reconciliations`.
- Ref folder: `modules/accurate/bank_reconcile/`, `modules/accurate/bank_book/`.

### 4A. Perusahaan - Payment Term

**Card:** `[MVP] Master: payment term dan integrasi jatuh tempo invoice`

- Checklist: CRUD payment term; due_date invoice dihitung otomatis; PHPUnit.
- Migration: `payment_terms`; ALTER invoice penjualan/pembelian tambah
  `payment_term_id`, `due_date`.
- Ref folder: `modules/accurate/payment_term/`, `modules/accurate/sales_invoice/`.

### 4B. Perusahaan - Shipment dan FOB

**Card:** `[MVP] Master: shipment dan FOB`

- Checklist: CRUD shipment; CRUD FOB; PHPUnit.
- Migration: `shipments`, `free_on_boards`.
- Ref folder: `modules/accurate/shipment/`, `modules/accurate/freeonboard/`.

### 4C. Perusahaan - Karyawan, Payroll, Penomoran

**Card:** `[MVP] Perusahaan: karyawan, komponen gaji, dan penomoran dokumen`

- Checklist: CRUD karyawan; komponen gaji/tunjangan/potongan; sequence
  otomatis per dokumen per cabang; PHPUnit.
- Migration: `employees`, `employee_fees`, `document_sequences`.
- Ref folder: `modules/accurate/employee/`, `modules/accurate/employee_fee/`,
  `modules/accurate/employee_payment/`.

### 5A. Penjualan - Quotation

**Card:** `[MVP] Penjualan: quotation dan konversi ke sales order`

- Checklist: CRUD quotation; status won/lost/expired; konversi ke SO;
  PHPUnit.
- Migration: `sales_quotations`, `sales_quotation_items`.
- Ref folder: `modules/accurate/sales_quotation/`.

### 5B. Penjualan - Down Payment

**Card:** `[MVP] Penjualan: uang muka penjualan dan alokasi ke invoice`

- Checklist: terima DP; jurnal; alokasi ke invoice; PHPUnit.
- Migration: `sales_down_payments`.
- Ref folder: `modules/accurate/sales_downpayment/`.

### 5C. Penjualan - Kategori, Komisi, Target

**Card:** `[MVP] Penjualan: kategori pelanggan, kategori harga, komisi, dan target`

- Checklist: CRUD kategori; komisi per invoice; target per periode;
  laporan capaian; PHPUnit.
- Migration: `customer_categories`, `price_categories`,
  `sales_commissions`, `sales_targets`; ALTER customers dan invoice.
- Ref folder: `modules/accurate/customer_category/`,
  `modules/accurate/price_category/`, `modules/accurate/salesman_commission/`,
  `modules/accurate/sales_target/`.

### 6A. Pembelian - Down Payment dan Master Pemasok

**Card:** `[MVP] Pembelian: uang muka, harga pemasok, dan kategori pemasok`

- Checklist: DP dan alokasi; harga per produk per pemasok; kategori;
  PHPUnit.
- Migration: `purchase_down_payments`, `vendor_prices`, `vendor_categories`;
  ALTER vendors.
- Ref folder: `modules/accurate/customer/` (pola master kontak untuk
  pemasok), `modules/accurate/sellingprice_adjustment/` (pola harga).

### 6B. Pembelian - Perintah Pembayaran dan Transfer Pemasok

**Card:** `[MVP] Pembelian: perintah pembayaran dan transfer multi pemasok`

- Checklist: buat perintah pembayaran; alokasi ke banyak invoice pemasok;
  status paid; PHPUnit.
- Migration: `transfer_orders`, `transfer_order_payments`.
- Ref folder: `modules/accurate/other_payment/` (pola pembayaran).

### 7A. Buku Besar - Anggaran dan Transfer

**Card:** `[MVP] Buku besar: anggaran per akun dan transfer anggaran`

- Checklist: CRUD anggaran per periode; transfer antar akun; PHPUnit.
- Migration: `account_budgets`, `account_budget_transfers`.
- Ref folder: `modules/accurate/accountbudget_target/`,
  `modules/accurate/accountbudget_transfer/`.

### 7B. Buku Besar - Monitor Anggaran dan Histori Akun

**Card:** `[MVP] Buku besar: monitor realisasi anggaran dan histori akun`

- Checklist: realisasi vs anggaran; indikator over budget; drill-down
  histori akun; PHPUnit.
- Migration: report-only (query `general_journals`); index composite
  `(gl_account_id, date)` bila belum ada.
- Ref folder: `modules/accurate/accountbudget_monitor/`,
  `modules/accurate/account_history/`.

### 8. Persediaan - Serial, Batch, Requisition

**Card:** `[Non-MVP] Persediaan: nomor seri, batch FEFO, dan permintaan material`

- Checklist: assign seri; batch expiry FEFO; requisition ke BOM/assembly;
  laporan umur stok; PHPUnit.
- Migration: `product_serials`, `product_batches`,
  `material_requisitions(+items)`; ALTER stock movements.
- Ref folder: `modules/accurate/journal_voucher/` (pola form detail item),
  dokumentasi inventory di `all-menus.json`.

### 9. Daftar Laporan - Analisa AI

**Card:** `[Non-MVP] Laporan: insight AI tren, anomali, dan ringkasan`

- Checklist: tren revenue/expense/margin; deteksi anomali; ringkasan
  naratif; PHPUnit.
- Migration: `report_insights`.
- Ref folder: `modules/accurate/rea-accurate-analysis.md` (pola analisa).

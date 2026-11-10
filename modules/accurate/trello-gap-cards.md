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

**Form Input:**

Form Akuisisi Aset (`fixed_assets`):

Tab Informasi Aset:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Kode Aset | text (auto/manual) | Ya | unique per tenant |
| Nama Aset | text | Ya | |
| Kategori Aset | lookup `asset_categories` | Ya | menentukan akun COA otomatis |
| Lokasi Aset | lookup `asset_locations` | Tidak | |
| Cabang | lookup `branches` | Ya | |
| Tanggal Perolehan | date | Ya | |
| Harga Perolehan | number | Ya | |
| Nilai Sisa (Salvage) | number, default 0 | Tidak | |
| Masa Manfaat (bulan) | integer | Ya | |
| Metode Depresiasi | select: straight_line / declining_balance | Ya | default straight_line |
| Akun Kas/AP | lookup `gl_accounts` | Ya | kredit saat akuisisi |

Tab Depresiasi (read-only setelah posting):

| Field | Input | Keterangan |
| --- | --- | --- |
| Periode | char(7) YYYY-MM | unique per aset |
| Beban Periode | number | dihitung otomatis |
| Akumulasi | number | running total |

Tab Penghapusan/Penjualan:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Tipe | select: sale / disposal | Ya | |
| Tanggal | date | Ya | |
| Harga Jual | number | Jika sale | |
| Gain/Loss | number (auto) | - | dihitung sistem |

**Tab Layout:** Ya — 3 tab: Informasi Aset, Depresiasi, Penghapusan. Tab Depresiasi dan Penghapusan muncul setelah aset di-post. Terkait tabel `asset_categories` (COA mapping), `fixed_asset_depreciations`, dan `fixed_asset_disposals`.

**Business Flow:**

1. Admin membuat kategori aset → pilih akun akumulasi depresiasi, beban depresiasi, gain, dan loss di COA.
2. Admin membuat lokasi aset per cabang (opsional).
3. User input akuisisi aset → isi form Informasi Aset → submit → jurnal otomatis: Debit Fixed Asset, Kredit Kas/AP.
4. Setiap akhir bulan (period-end), sistem menghitung depresiasi: straight_line = (cost - salvage) / useful_life_months; declining_balance = net_book_value × rate.
5. Posting depresiasi → jurnal otomatis: Debit Beban Depresiasi, Kredit Akumulasi Depresiasi. Cegah duplikat per periode per aset.
6. Saat aset dijual: input harga jual + tanggal → sistem hitung gain/loss = harga_jual - (cost - accumulated_depreciation) → jurnal: Debit Kas + Akumulasi Depresiasi (+ Loss), Kredit Fixed Asset + PPN (+ Gain).
7. Saat aset dihapus (disposal): jurnal: Debit Akumulasi Depresiasi + Loss, Kredit Fixed Asset. Nilai buji bersih jadi nol.
8. Laporan daftar aset dan depresiasi per periode dapat dicetak.

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

**Form Input:**

Form Faktur Pajak (`tax_invoices`):

Tab Informasi Faktur:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Tipe | select: output / input | Ya | output=keluaran, input=masukan |
| NSFP | text (auto dari DJP) | Ya (output) | nomor seri faktur pajak |
| Masa Pajak | char(2) MM | Ya | |
| Tahun Pajak | char(4) YYYY | Ya | |
| Dokumen Sumber | lookup sales/purchase invoice | Ya | morph relation |
| Nama Lawan Transaksi | text (snapshot dari invoice) | Ya | |
| NPWP | text (snapshot) | Tidak | |
| Alamat | textarea (snapshot) | Tidak | |
| DPP | number (snapshot dari invoice) | Ya | dasar pengenaan pajak |
| PPN | number (snapshot = 11% dari DPP) | Ya | |

Tab Email Faktur:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Email Tujuan | text/email | Ya | default dari pelanggan |
| Status Kirim | auto: pending/sent/failed | - | log di `tax_invoice_emails` |
| Retry | button | - | manual jika gagal |

Form SPT PPN (`spt_ppn_filings`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Masa | char(2) MM | Ya | unique per tahun |
| Tahun | char(4) YYYY | Ya | |
| Total PPN Keluaran | number (auto rekap) | - | dari tax_invoices type=output |
| Total PPN Masukan | number (auto rekap) | - | dari tax_invoices type=input |
| Kurang/Lebih Bayar | number (auto) | - | output - input |
| File CSV DJP | file download | - | format DJP |
| Status | select: draft / filed | - | filed = sudah dilaporkan |

**Tab Layout:** Ya — untuk faktur pajak: tab Informasi Faktur dan tab Email. Untuk SPT: single form tanpa tab. Terkait tabel `sales_invoices`, `purchase_invoices`, dan `tax_invoice_emails`.

**Business Flow:**

1. Sales invoice di-post → sistem otomatis membuat faktur pajak keluaran (type=output) dengan snapshot DPP dan PPN.
2. Purchase invoice di-post → user dapat mencatat faktur pajak masukan (type=input) dari faktur pemasok.
3. NSFP (Nomor Seri Faktur Pajak) di-generate dari DJP atau diinput manual.
4. User dapat mengirim faktur pajak via email ke pelanggan → log status di `tax_invoice_emails` → retry manual jika gagal.
5. Setiap akhir masa pajak: sistem rekap semua faktur output dan input per masa/tahun.
6. Hitung kurang/lebih bayar: PPN Keluaran - PPN Masukan.
7. Generate file CSV format DJP untuk pelaporan SPT Masa PPN.
8. User laporkan ke DJP → ubah status menjadi `filed`.

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

**Form Input:**

Form Transfer Bank (`bank_transfers`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Rekening Asal | lookup bank accounts / GL | Ya | kredit |
| Rekening Tujuan | lookup bank accounts / GL | Ya | debit |
| Tanggal | date | Ya | |
| Jumlah | number | Ya | |
| Biaya Admin | number, default 0 | Tidak | masuk beban bank |
| Catatan | textarea | Tidak | |

Form Import Rekening Koran (`bank_statements` + `bank_statement_lines`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Rekening Bank | lookup | Ya | statement untuk rekening ini |
| Periode | date range | Ya | |
| File CSV/MT940 | file upload | Ya | parse otomatis |
| Saldo Awal | number | Ya | validasi |
| Saldo Akhir | number | Ya | validasi |

Form Rekonsiliasi (`bank_reconciliations`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Rekening Bank | lookup | Ya | |
| Periode | char(7) YYYY-MM | Ya | |
| Saldo GL | number (auto dari GL) | - | |
| Saldo Bank | number (auto dari statement) | - | |
| Selisih | number (auto) | - | harus nol sebelum posted |
| Match | auto/manual per line | - | |
| Jurnal Penyesuaian | auto-generate untuk selisih | - | |

**Tab Layout:** Ya — modul bank punya 3 sub-fitur dengan tab: Transfer, Import Statement, Rekonsiliasi. Setiap tab adalah fitur terpisah dengan tabel sendiri. Terkait tabel `bank_transfers`, `bank_statements`, `bank_statement_lines`, `bank_reconciliations`, dan `general_journals`.

**Business Flow:**

Transfer Bank:
1. User buka form transfer → pilih rekening asal dan tujuan → isi jumlah dan biaya admin.
2. Submit → jurnal otomatis: Debit Bank Tujuan, Kredit Bank Asal (+ Debit Beban Bank jika ada fee).

Import Rekening Koran:
3. User upload file CSV/MT940 → sistem parse → tampilkan preview lines.
4. Sistem validasi saldo awal dan akhir → jika cocok, simpan sebagai draft.
5. Lines siap di-match ke transaksi GL pada tahap rekonsiliasi.

Rekonsiliasi:
6. User pilih rekening dan periode → sistem tampilkan saldo GL vs saldo bank.
7. Auto-match: cocokkan statement lines ke transaksi GL berdasarkan tanggal + jumlah + referensi.
8. Manual match: user drag-and-drop atau pilih pasangan line↔GL.
9. Selisih yang tidak match → user buat jurnal penyesuaian.
10. Ketika selisih = nol → posting rekonsiliasi → tandai periode reconciled.
11. Laporan Bank Book: mutasi per rekening per periode dengan running balance.

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

**Form Input:**

Form Payment Term (`payment_terms`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Nama | text | Ya | mis. "Net 30", "EOM" |
| Tipe | select: net_days / end_of_month | Ya | |
| Jumlah Hari | integer (jika net_days) | Tidak | |
| Diskon (%) | decimal, default 0 | Tidak | early payment discount |
| Hari Diskon | integer | Tidak | batas hari untuk diskon |

Form Shipment:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Nama | text | Ya | |
| Alamat Pickup | textarea | Tidak | |

Form FOB:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Nama | text | Ya | mis. "FOB Origin", "FOB Destination" |

Form Karyawan (`employees`):

Tab Informasi Karyawan:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Nama | text | Ya | |
| NIK/ID | text | Ya | |
| Jabatan | text | Tidak | |
| Cabang | lookup | Ya | |
| Email | text/email | Tidak | |
| Telepon | text | Tidak | |
| Non Aktif | checkbox | Tidak | |

Tab Komponen Gaji (`employee_fees`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Tipe | select: salary / allowance / deduction | Ya | |
| Nama | text | Ya | mis. "Gaji Pokok", "Tunjangan Transport" |
| Jumlah | number | Ya | |
| Tanggal Efektif | date | Ya | |

Form Penomoran (`document_sequences`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Tipe Dokumen | select: sales_order / sales_invoice / purchase_order / purchase_invoice / journal / payment | Ya | |
| Cabang | lookup | Ya | |
| Prefix | text | Ya | mis. "INV", "SO" |
| Padding | integer, default 5 | Tidak | panjang digit |
| Nomor Berikutnya | bigInteger, auto-increment | - | |

**Tab Layout:** Ya — form Karyawan punya tab Informasi dan tab Komponen Gaji. Master lain (payment term, shipment, FOB, penomoran) cukup single form karena tidak berelasi ke detail item. Terkait tabel `payment_terms`, `shipments`, `free_on_boards`, `employees`, `employee_fees`, `document_sequences`, dan `sales_invoices`/`purchase_invoices` (via payment_term_id).

**Business Flow:**

Payment Term:
1. Admin buat payment term (mis. Net 30).
2. Saat membuat sales/purchase invoice → pilih payment term → due_date otomatis = invoice_date + 30 hari (atau akhir bulan jika EOM).
3. Laporan AR/AP aging menggunakan due_date untuk kategorikan umur piutang.

Shipment/FOB:
4. Admin buat master shipment dan FOB → terpakai di sales order dan delivery order sebagai dropdown.

Karyawan & Payroll:
5. HR input data karyawan → set komponen gaji (salary, allowance, deduction).
6. Komponen gaji terpakai saat proses payroll bulanan.

Penomoran:
7. Admin set prefix per tipe dokumen per cabang.
8. Saat user membuat dokumen baru → nomor otomatis dari sequence → increment atomik (SELECT FOR UPDATE) → format: PREFIX/CABANG/YYYYMM/SEQ.

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

**Form Input:**

Form Quotation (`sales_quotations` + `sales_quotation_items`):

Tab Informasi:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Pelanggan | lookup `customers` | Ya | |
| Tanggal Quotation | date | Ya | |
| Berlaku Sampai | date | Tidak | |
| Cabang | lookup | Ya | |
| Status | auto: draft/sent/won/lost/expired | - | |

Tab Detail Item:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Produk | lookup `products` | Ya | |
| Qty | number | Ya | |
| Harga | number (default dari price category) | Ya | |
| Diskon | number/persen | Tidak | |
| Total | number (auto: qty × harga - diskon) | - | |

Form Down Payment (`sales_down_payments`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Pelanggan | lookup | Ya | |
| Tanggal | date | Ya | |
| Jumlah | number | Ya | |
| Rekening Kas/Bank | lookup | Ya | |
| Teralokasi | number (auto) | - | ke invoice |

Form Kategori Pelanggan/Harga:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Nama | text | Ya | unique per tenant |

Form Komisi (`sales_commissions`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Karyawan (Salesman) | lookup | Ya | |
| Invoice | lookup | Ya | dasar perhitungan |
| Rate (%) | decimal | Ya | |
| Jumlah | number (auto: rate × invoice total) | - | |
| Status | auto: accrued/paid | - | |

Form Target (`sales_targets`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Karyawan/Cabang | lookup (salah satu wajib) | Ya | |
| Periode | char(7) YYYY-MM | Ya | |
| Target | number | Ya | |

**Tab Layout:** Ya — Quotation punya tab Informasi dan tab Detail Item (sama dengan pattern Sales Order yang sudah ada). Down Payment cukup single form. Komisi dan Target juga single form. Terkait tabel `sales_quotations`, `sales_quotation_items`, `sales_down_payments`, `customer_categories`, `price_categories`, `sales_commissions`, `sales_targets`, dan `sales_orders` (konversi quotation).

**Business Flow:**

Quotation:
1. Sales buat quotation → pilih pelanggan → isi detail item (produk, qty, harga).
2. Kirim quotation ke pelanggan → status berubah dari draft ke sent.
3. Pelanggan setuju → status won → klik "Konversi ke SO" → sistem buat sales order dari data quotation.
4. Pelanggan menolak → status lost. Melewati valid_until tanpa konversi → status expired (scheduled job).

Down Payment:
5. Terima DP dari pelanggan → pilih rekening kas/bank → submit → jurnal: Debit Kas/Bank, Kredit Uang Muka Penjualan.
6. Saat invoice terbentuk → alokasi DP → jurnal: Debit Uang Muka Penjualan, Kredit AR.
7. Sisa DP bisa di-refund.

Kategori:
8. Admin buat kategori pelanggan dan kategori harga → assign ke customer dan invoice → harga default mengikuti kategori.

Komisi:
9. Sales invoice di-post → sistem hitung komisi = rate × invoice_total → simpan status accrued.
10. Payroll/proses pembayaran komisi → status paid → jurnal: Debit Beban Komisi, Kredit Kas/Utang Komisi.

Target:
11. Manager set target penjualan per karyawan atau cabang per bulan.
12. Laporan capaian: actual sales vs target per periode → indikator tercapai/melebihi/below.

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

**Form Input:**

Form Down Payment Pembelian (`purchase_down_payments`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Pemasok | lookup `vendors` | Ya | |
| Tanggal | date | Ya | |
| Jumlah | number | Ya | |
| Rekening Kas/Bank | lookup | Ya | kredit |
| Teralokasi | number (auto) | - | ke faktur |

Form Harga Pemasok (`vendor_prices`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Pemasok | lookup | Ya | |
| Produk | lookup | Ya | |
| Harga | number | Ya | |
| Qty Minimum | number, default 1 | Tidak | |
| Tanggal Efektif | date | Ya | unique per vendor+product |

Form Kategori Pemasok:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Nama | text | Ya | unique per tenant |

Form Perintah Pembayaran (`transfer_orders`):

Tab Informasi:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Nomor Dokumen | auto | - | |
| Tanggal | date | Ya | |
| Status | auto: draft/approved/paid/cancelled | - | |

Tab Detail Pembayaran (`transfer_order_payments`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Pemasok | lookup | Ya | |
| Invoice Hutang | lookup (opsional) | Tidak | jika membayar invoice spesifik |
| Jumlah | number | Ya | |

**Tab Layout:** Ya — Perintah Pembayaran punya tab Informasi dan tab Detail Pembayaran (multi-vendor). Down Payment dan master (harga pemasok, kategori) single form. Terkait tabel `purchase_down_payments`, `vendor_prices`, `vendor_categories`, `transfer_orders`, `transfer_order_payments`, dan `purchase_invoices`.

**Business Flow:**

Down Payment Pembelian:
1. Perusahaan bayar DP ke pemasok sebelum barang datang → jurnal: Debit Uang Muka Pembelian, Kredit Kas/Bank.
2. Saat faktur pembelian di-post → alokasi DP → jurnal: Debit AP, Kredit Uang Muka Pembelian.
3. Sisa DP bisa di-refund.

Harga Pemasok:
4. Admin input harga per produk per pemasok dengan tanggal efektif.
5. Saat buat PO → sistem suggest harga dari `vendor_prices` berdasarkan pemasok + produk + tanggal.

Kategori Pemasok:
6. Admin buat kategori → assign ke vendor → filter di list pemasok.

Perintah Pembayaran:
7. Finance buat perintah pembayaran → pilih multiple pemasok + invoice hutang yang mau dibayar.
8. Approve → status approved.
9. Transfer ke bank masing-masing pemasok → status paid → jurnal: Debit AP, Kredit Kas/Bank.
10. Jika ada invoice spesifik → link ke `payable_invoice_id` untuk tracking.

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

**Form Input:**

Form Anggaran (`account_budgets`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Cabang | lookup | Ya | |
| Akun | lookup `gl_accounts` | Ya | |
| Periode | char(7) YYYY-MM | Ya | unique per cabang+akun+periode |
| Target Anggaran | number | Ya | |
| Realisasi | number (auto) | - | dari posting jurnal |

Form Transfer Anggaran (`account_budget_transfers`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Dari Anggaran | lookup `account_budgets` | Ya | budget sumber |
| Ke Anggaran | lookup `account_budgets` | Ya | budget tujuan |
| Jumlah | number | Ya | tidak boleh > sisa budget asal |
| Tanggal | date | Ya | |

Form Pencatatan Beban (`expense_accruals`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Akun Beban | lookup `gl_accounts` | Ya | |
| Jumlah | number | Ya | |
| Tanggal Akrual | date | Ya | |
| Jurnal Akrual | auto | - | Debit Beban, Kredit Utang Beban |
| Jurnal Pembalikan | auto (periode berikutnya) | - | Debit Utang Beban, Kredit Beban |

Histori Akun (report-only, tidak ada form):

| Filter | Input | Keterangan |
| --- | --- | --- |
| Akun | lookup | pilih akun |
| Periode | date range | |
| Cabang | lookup (opsional) | |

**Tab Layout:** Ya — modul Buku Besar punya 4 sub-fitur dengan tab terpisah: Anggaran, Transfer Anggaran, Pencatatan Beban, Histori Akun. Anggaran dan Transfer punya tabel sendiri. Histori Akun adalah report-only. Terkait tabel `account_budgets`, `account_budget_transfers`, `expense_accruals`, dan `general_journals`.

**Business Flow:**

Anggaran:
1. Manager set anggaran per akun per cabang per bulan.
2. Setiap jurnal di-post → jika akun ada di anggaran → update `actual_amount`.
3. Monitor Anggaran: tampilkan target vs realisasi → indikator warning jika melebihi budget.

Transfer Anggaran:
4. Jika budget akun A kurang tapi akun B surplus → transfer anggaran dari B ke A.
5. Validasi: jumlah transfer tidak boleh melebihi sisa budget asal.

Pencatatan Beban (Expense Accrual):
6. Akhir bulan: catat beban yang sudah terjadi tapi belum ada invoice → jurnal akrual.
7. Periode berikutnya: jurnal pembalikan otomatis (reversing entry) agar tidak double-count.

Histori Akun:
8. User pilih akun + periode → sistem tampilkan semua jurnal yang menyentuh akun tsb.
9. Running balance: saldo awal + debit - kredit per transaksi.
10. Drill-down: klik transaksi → buka detail jurnal.

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

**Form Input:**

Form Nomor Seri (`product_serials`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Produk | lookup | Ya | |
| Nomor Seri | text | Ya | unique per tenant+produk |
| Status | auto: in_stock/sold/returned | - | |
| Gudang | lookup | Tidak | lokasi saat ini |
| GR Item | auto (saat penerimaan) | - | track sumber |
| Sales Item | auto (saat penjualan) | - | track keluar |

Form Batch/Lot (`product_batches`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Produk | lookup | Ya | |
| Nomor Batch | text | Ya | unique per tenant+produk |
| Tanggal Kedaluwarsa | date | Tidak | untuk FEFO |
| GR Item | auto (saat penerimaan) | - | |

Form Permintaan Material (`material_requisitions` + `material_requisition_items`):

Tab Informasi:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Nomor Dokumen | auto | - | |
| Cabang | lookup | Ya | |
| BOM/Assembly | lookup (opsional) | Tidak | jika permintaan dari produksi |
| Status | auto: draft/approved/fulfilled/cancelled | - | |

Tab Detail Item:

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Produk | lookup | Ya | |
| Qty Diminta | number | Ya | |
| Qty Terpenuhi | number (auto) | - | saat fulfilment |

**Tab Layout:** Ya — Material Requisition punya tab Informasi dan tab Detail Item. Serial dan Batch adalah master sederhana (single form). Terkait tabel `product_serials`, `product_batches`, `material_requisitions`, `material_requisition_items`, `stock_movements` (ALTER dengan batch_id dan serial_id), dan `products`.

**Business Flow:**

Nomor Seri:
1. Produk ditandai "track serial" → saat penerimaan barang (GR), user assign nomor seri per unit.
2. Serial status = in_stock, tercatat di gudang.
3. Saat penjualan (sales invoice/delivery order), user pilih nomor seri → status berubah ke sold.
4. Retur penjualan → status kembali ke returned.

Batch/Lot:
5. Produk ditandai "track batch" → saat GR, user input nomor batch + expiry date.
6. Saat picking (DO/sales), sistem pakai FEFO (First Expired First Out) → batch dengan expiry terdekat dipilih dulu.
7. Laporan umur stok: batch yang mendekati expiry ditandai warning.

Permintaan Material:
8. Produksi butuh material → buat material requisition → pilih BOM/assembly (opsional, untuk auto-fill item).
9. Approve requisition → status approved.
10. Gudang keluarkan material → update fulfilled_quantity → status fulfilled saat semua terpenuhi.
11. Stock movement tercatat dengan batch_id/serial_id untuk traceability.

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

**Form Input:**

Form/Laporan Insight AI (`report_insights`):

| Field | Input | Wajib | Keterangan |
| --- | --- | --- | --- |
| Tipe Laporan | select: financial / sales / inventory | Ya | sumber data |
| Periode Awal | date | Ya | |
| Periode Akhir | date | Ya | |
| Tipe Insight | select: trend / anomaly / summary | Ya | |
| Payload | JSON (auto-generate) | - | hasil analisa AI |
| Generated By | auto: system / user-triggered | - | |

**Tab Layout:** Tidak — single report page dengan filter, bukan form input dengan tab. Tidak ada relasi FK ke tabel transaksi; insight dibaca dari laporan yang sudah ada.

**Business Flow:**

1. Sistem menjalankan analisa otomatis (scheduled) atau user trigger manual.
2. Baca data laporan keuangan (profit & loss, balance sheet) atau laporan penjualan/inventory untuk rentang periode.
3. Trend: bandingkan revenue, expense, margin antar periode → identifikasi naik/turun dan persentase perubahan.
4. Anomaly: deteksi fluktuasi tidak wajar di akun utama (mis. expense naik > 50% tanpa penjelasan).
5. Summary: generate ringkasan naratif (template-based atau AI/LLM) dari laporan.
6. Simpan hasil ke `report_insights` → tampilkan di dashboard laporan.
7. User dapat melihat insight per periode dan per tipe laporan.

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

---

## Business Flow dan Aturan Implementasi

Bagian ini adalah aturan lintas kartu. Semua kartu pecahan WAJIB mengikuti
alur, mapping jurnal, dan aturan di bawah agar dokumen antar modul konsisten.

### Lifecycle Dokumen Penjualan

```text
Quotation (draft -> sent -> won/lost/expired)
  -> Sales Order (draft -> confirmed -> partial -> fulfilled -> closed)
    -> Delivery Order (draft -> posted; stok berkurang saat posting)
      -> Sales Invoice (draft -> posted; AR terbentuk saat posting)
        -> Sales Receipt (posted; piutang berkurang)
  -> Sales Down Payment (posted; alokasi ke invoice)
Retur Penjualan (posted; stok bertambah, AR berkurang / refund)
```

- Transisi status hanya maju; pembatalan memakai status `cancelled`, bukan
  menghapus dokumen (insert-only audit).
- DO hanya boleh dibuat dari SO yang `confirmed`; invoice boleh sebagian
  (partial invoicing) dengan sisa qty tetap terbuka.
- DP wajib teralokasi penuh; sisa DP bisa direfund.

### Lifecycle Dokumen Pembelian

```text
Purchase Requisition (draft -> approved -> converted)
  -> Purchase Order (draft -> approved -> partial -> received -> closed)
    -> Receive Item / GR (draft -> posted; stok bertambah, GRIR terbentuk)
      -> Purchase Invoice (draft -> posted; 3-way matching, hutang terbentuk)
        -> Purchase Payment (posted; hutang berkurang)
  -> Purchase Down Payment (posted; alokasi ke faktur)
Retur Pembelian (posted; stok berkurang, hutang berkurang / refund)
```

- 3-way matching wajib lulus (PO vs GR vs invoice) sebelum invoice posted;
  selisih harga/qty menolak posting kecuali di-overwrite dengan otorisasi.
- PO approval dinamis per company/branch mengikuti kartu Trello yang sudah
  ada (Dynamic PO Approval).

### Mapping Jurnal Per Dokumen

| Dokumen | Debit | Kredit |
| --- | --- | --- |
| Sales Invoice | AR (piutang) | Revenue + PPN Keluaran |
| Sales Receipt | Kas/Bank | AR |
| Sales Down Payment | Kas/Bank | Uang Muka Penjualan (liability) |
| Alokasi DP ke Invoice | Uang Muka Penjualan | AR |
| Delivery Order (posting) | COGS / HPP | Inventory |
| Retur Penjualan | Sales Return + PPN Keluaran (koreksi) | AR / Kas |
| Purchase Invoice | Inventory + PPN Masukan | AP (hutang) + GRIR |
| GR (posting) | Inventory | GRIR |
| Purchase Payment | AP | Kas/Bank |
| Purchase Down Payment | Uang Muka Pembelian (asset) | Kas/Bank |
| Retur Pembelian | AP / Kas | Inventory + PPN Masukan (koreksi) |
| Bank Transfer | Bank tujuan | Bank asal (+ fee ke beban bank) |
| Akuisisi Aset | Fixed Asset | Kas/AP |
| Depresiasi | Beban Depresiasi | Akumulasi Depresiasi |
| Penjualan Aset | Kas + Akumulasi Depresiasi (+ loss bila ada) | Fixed Asset + PPN (jika) (+ gain bila ada) |
| Pembebanan (expense accrual) | Beban | Utang Beban |

- Semua jurnal insert-only; pembalikan memakai reversal entry, bukan update.
- COA mapping tidak boleh hardcode di kode; simpan di tabel mapping per
  company/branch (mengikuti kartu MVP COA: Mapping jurnal level branch).

### Alur Period-End Close

Urutan wajib tutup periode (menghubungkan kartu 1B, 3C, 7A):

1. Posting semua dokumen draft yang tanggalnya masuk periode.
2. Depresiasi aset tetap (kartu 1B).
3. Pembebanan/akrual dan prabayar (kartu 7A, tabel `expense_accruals`).
4. Rekonsiliasi bank dan penyesuaian selisih (kartu 3C).
5. Validasi anggaran vs realisasi (kartu 7B).
6. Jurnal penutup periode; kunci periode (kartu existing Jurnal penutup).

Setelah periode dikunci, transaksi ber-tanggal periode tersebut DITOLAK.

### Aturan Penomoran Dokumen

- Format: `{PREFIX}/{CABANG}/{YYYYMM}/{SEQ}` - contoh `INV/BDG/202611/00042`.
- Sequence per `tenant + branch + document_type` di tabel
  `document_sequences`; increment atomik (SELECT FOR UPDATE) supaya tidak
  duplicate saat concurrent.
- Sumber prefix mengikuti field `typeAutoNumber` di `<menu>.md` Accurate
  (mis. Penawaran Penjualan punya auto number sendiri).
- Nomor final terbentuk saat dokumen posted; draft memakai nomor sementara.

### Aturan Akses dan Approval

- Pemetaan Akses Grup Accurate ke permission matrix klinik: setiap menu
  Accurate = satu permission key (mis. `sales.quotation.view`,
  `sales.quotation.create`).
- Approval berjenjang untuk dokumen material: PR/PO butuh approver sesuai
  threshold nilai (configurable per company/branch).
- Semua endpoint WAJIB cek permission di middleware; UI hanya menyembunyikan
  menu tanpa akses, bukan pengganti otorisasi server.
- Audit log wajib untuk create/update/delete/approve semua dokumen.
- Ref folder: `modules/accurate/rea-accurate-analysis.md` (pola analisa).

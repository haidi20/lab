import json
import os
import sys
import urllib.request
import urllib.parse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from modules.vps.config import load_env

load_env(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

KEY = os.environ['TRELLO_API_KEY']
TOKEN = os.environ['TRELLO_TOKEN']
BOARD = 'vB4uz4Qb'
TODO_LIST = '6ad7fee1ed4e45ebbb797384'
BASE = 'https://api.trello.com/1'


def api(method, path, params=None):
    params = params or {}
    params['key'] = KEY
    params['token'] = TOKEN
    qs = urllib.parse.urlencode(params)
    url = BASE + path + '?' + qs if method == 'GET' else BASE + path
    data = urllib.parse.urlencode(params).encode() if method != 'GET' else None
    req = urllib.request.Request(url, data=data, method=method)
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode()
    return json.loads(body) if body.strip() else {}


def ensure_label(name, color):
    labels = api('GET', '/board/%s/labels' % BOARD)
    for label in labels:
        if label['name'] == name:
            return label['id']
    return api('POST', '/labels', {'name': name, 'color': color, 'idBoard': BOARD})['id']


def create_card(name, desc, label_ids, checklist_name, checklist_items, position='bottom'):
    card = api('POST', '/cards', {
        'idList': TODO_LIST,
        'name': name,
        'desc': desc,
        'idLabels': ','.join(label_ids),
        'pos': position,
    })
    checklist = api('POST', '/cards/%s/checklists' % card['id'], {'name': checklist_name})
    for item in checklist_items:
        api('POST', '/checklists/%s/checkItems' % checklist['id'], {'name': item})
    return card


def main():
    labels = {
        'MVP': ensure_label('MVP', 'green'),
        'Non-MVP': ensure_label('Non-MVP', 'blue'),
        'P0': ensure_label('P0', 'red'),
        'P1': ensure_label('P1', 'orange'),
        'P2': ensure_label('P2', 'yellow'),
        'sales': ensure_label('sales', 'sky'),
        'purchasing': ensure_label('purchasing', 'lime'),
        'journal': ensure_label('journal', 'black'),
'procurement': ensure_label('procurement', 'orange'),
        'inventory': ensure_label('Inventori', 'purple'),
    }
    print('labels ready')

    existing = api('GET', '/lists/%s/cards' % TODO_LIST)
    existing_names = {c['name'] for c in existing}

    cards = build_cards()
    for card_def in cards:
        if card_def['name'] in existing_names:
            print('SKIP (exists):', card_def['name'])
            continue
        ids = [labels[t] for t in card_def['labels']]
        card = create_card(
            card_def['name'], card_def['desc'], ids,
            'Acceptance Criteria', card_def['ac'],
        )
        print('CREATED:', card['name'])


def build_cards():
    cards = []

    cards.append({
        'name': '[MVP] Bangun modul fixed asset: kategori, lokasi, akuisisi, depresiasi, penjualan, dan penghapusan aset',
        'labels': ['MVP', 'P0', 'journal'],
        'desc': (
            'Context: Menu Aset Tetap Accurate punya 7 item (akuisisi, depresiasi, '
            'penjualan aset, penghapusan, kategori, lokasi, laporan) tetapi board '
            'Trello klinik hanya punya satu kartu jurnal depreciation adjustment. '
            'Modul aset tetap belum ada sebagai fitur utuh.\n\n'
            'Insight: Siklus hidup aset tetap lengkap dari akuisisi sampai disposal '
            'menghasilkan 3 tipe jurnal otomatis: akuisisi (Debit FA / Kredit Kas-AP), '
            'depresiasi (Debit Beban / Kredit Akumulasi), dan disposal (gain/loss).\n\n'
            'Flow: Akuisisi -> posting -> depresiasi bulanan (straight_line / declining_balance) '
            '-> penjualan (hitung gain/loss) atau penghapusan (nilai buku nol) -> laporan.\n\n'
            'Migration: asset_categories, asset_locations, fixed_assets, '
            'fixed_asset_depreciations, fixed_asset_disposals.\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian Aset Tetap'
        ),
        'ac': [
            'CRUD kategori aset dan lokasi aset per tenant',
            'Akuisisi aset: harga perolehan, tanggal, akun COA, jurnal otomatis',
            'Depresiasi: garis lurus dan saldo menurun, jurnal bulanan otomatis',
            'Penjualan aset: hitung gain/loss, jurnal otomatis, nilai buku bersih',
            'Penghapusan aset: jurnal penghapusan, nilai buku nol',
            'Laporan daftar aset dan depresiasi per periode',
            'PHPUnit untuk setiap alur di atas',
        ],
    })

    cards.append({
        'name': '[MVP] Bangun modul e-Faktur: faktur pajak keluaran/masukan, email faktur, dan SPT PPN',
        'labels': ['MVP', 'P0', 'sales'],
        'desc': (
            'Context: Menu SmartLink Tax Accurate punya e-Faktur CTAS dan email faktur '
            'pajak; daftar laporan punya SPT PPN/PPNBM. Board Trello klinik tidak punya '
            'satu pun kartu pajak (efaktur, SPT, PPN).\n\n'
            'Insight: PPN keluaran muncul otomatis saat sales invoice di-post (snapshot '
            'DPP & PPN). PPN masukan dicatat manual dari faktur pemasok. SPT Masa PPN '
            'dihitung dari selisih keluaran-masukan.\n\n'
            'Flow: Sales invoice di-post -> faktur keluaran (NSFP, masa, tahun) -> email '
            'ke pelanggan -> rekap per masa -> generate CSV DJP -> filed.\n\n'
            'Migration: tax_invoices, tax_invoice_emails, spt_ppn_filings.\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian SmartLink Tax'
        ),
        'ac': [
            'Generate faktur pajak keluaran dari sales invoice (NSFP, masa, tahun)',
            'Catat faktur pajak masukan dari purchase invoice',
            'Kirim faktur pajak via email ke pelanggan',
            'Rekap PPN keluaran dan masukan per masa',
            'Generate SPT PPN masa (CSV/format DJP) dari rekap',
            'PHPUnit untuk generate, rekap, dan SPT',
        ],
    })

    cards.append({
        'name': '[MVP] Bangun modul bank: transfer antar rekening, rekonsiliasi bank, dan import rekening koran',
        'labels': ['MVP', 'P0', 'journal'],
        'desc': (
            'Context: Pembayaran/penerimaan sudah ada via piutang-hutang, tetapi '
            'transfer bank antar rekening sendiri, rekonsiliasi bank, dan import '
            'rekening koran belum ada kartunya.\n\n'
            'Insight: Transfer bank menghasilkan jurnal dua sisi otomatis (Debit Bank '
            'Tujuan, Kredit Bank Asal + fee). Rekonsiliasi menggunakan auto-match '
            '(tanggal + jumlah + referensi) dan manual match; selisih menghasilkan '
            'jurnal penyesuaian.\n\n'
            'Flow: Transfer -> jurnal. Import CSV/MT940 -> parse -> validasi saldo. '
            'Rekonsiliasi -> match -> jurnal penyesuaian -> bank book.\n\n'
            'Migration: bank_transfers, bank_statements, bank_statement_lines, '
            'bank_reconciliations.\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian Kas & Bank'
        ),
        'ac': [
            'Transfer bank antar rekening: jurnal dua sisi otomatis',
            'Import rekening koran CSV/MT940 ke draft transaksi',
            'Rekonsiliasi: match statement ke transaksi GL, hitung selisih',
            'Laporan histori bank (bank book) per rekening per periode',
            'PHPUnit untuk transfer, import, dan rekonsiliasi',
        ],
    })

    cards.append({
        'name': '[MVP] Lengkapi master perusahaan: payment term, shipment, FOB, karyawan, dan penomoran otomatis',
        'labels': ['MVP', 'P1', 'procurement'],
        'desc': (
            'Context: Payment term, shipment, FOB, karyawan/gaji, dan penomoran dokumen '
            'otomatis belum ada kartu di Trello padahal Accurate punya semuanya.\n\n'
            'Insight: Payment term menentukan due_date invoice (Net X atau EOM) yang '
            'dipakai laporan AR/AP aging. Penomoran pakai format PREFIX/CABANG/YYYYMM/SEQ '
            'dengan increment atomik (SELECT FOR UPDATE) untuk hindari duplicate saat '
            'concurrent.\n\n'
            'Flow: Payment term -> due_date invoice. Shipment/FOB -> dropdown di SO/DO. '
            'Karyawan -> komponen gaji -> payroll. Penomoran -> prefix per cabang per tipe.\n\n'
            'Migration: payment_terms, shipments, free_on_boards, employees, '
            'employee_fees, document_sequences + ALTER invoice.\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian Perusahaan dan Pengaturan'
        ),
        'ac': [
            'CRUD payment term (net X hari, EOM) dan integrasi jatuh tempo invoice',
            'CRUD shipment dan FOB sebagai master sederhana',
            'CRUD karyawan, gaji/tunjangan, dan komponen payroll dasar',
            'Penomoran otomatis per dokumen per cabang (SO, invoice, PO, jurnal)',
            'PHPUnit untuk setiap master di atas',
        ],
    })

    cards.append({
        'name': '[MVP] Lengkapi siklus penjualan: quotation, down payment, kategori pelanggan, komisi, dan target',
        'labels': ['MVP', 'P0', 'sales'],
        'desc': (
            'Context: SO, DO, invoice, retur, dan piutang sudah ada di board, tetapi '
            'penawaran (quotation), uang muka penjualan, kategori pelanggan, kategori '
            'harga, komisi penjual, target penjualan, dan check-in belum ada kartunya.\n\n'
            'Insight: Quotation adalah entry point funnel penjualan — status maju dari '
            'draft -> sent -> won/lost/expired. DP menghasilkan liability (Uang Muka '
            'Penjualan) yang dialokasi ke invoice saat terbentuk. Komisi dihitung '
            'otomatis per posted invoice.\n\n'
            'Flow: Quotation -> won -> konversi SO. DP -> terima -> alokasi. Komisi -> '
            'hitung per invoice -> paid. Target -> capaian vs aktual.\n\n'
            'Migration: sales_quotations(+items), sales_down_payments, '
            'customer_categories, price_categories, sales_commissions, sales_targets.\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian Penjualan'
        ),
        'ac': [
            'Quotation: CRUD dan konversi ke sales order',
            'Uang muka penjualan: penerimaan DP dan alokasi ke invoice',
            'Kategori pelanggan dan kategori harga: CRUD dan terpakai di invoice',
            'Komisi penjual: perhitungan per transaksi dan laporan',
            'Target penjualan: set target per periode dan laporan capaian',
            'PHPUnit untuk setiap alur di atas',
        ],
    })

    cards.append({
        'name': '[MVP] Lengkapi siklus pembelian: down payment, harga pemasok, kategori pemasok, dan transfer pemasok',
        'labels': ['MVP', 'P0', 'purchasing'],
        'desc': (
            'Context: PO, GR, invoice, 3-way matching, pembayaran, dan retur sudah ada '
            'di board, tetapi uang muka pembelian, harga pemasok, kategori pemasok, '
            'perintah pembayaran, dan transfer pemasok belum ada kartunya.\n\n'
            'Insight: Uang muka pembelian adalah asset (Uang Muka Pembelian) yang '
            'dialokasi ke faktur saat invoice di-post. Harga pemasok per produk dengan '
            'tanggal efektif memberi suggest harga di PO. Perintah pembayaran memungkinkan '
            'transfer multi-vendor dalam satu dokumen.\n\n'
            'Flow: DP -> bayar -> alokasi faktur. Harga pemasok -> suggest di PO. '
            'Perintah pembayaran -> approve -> transfer -> jurnal Debit AP / Kredit Kas.\n\n'
            'Migration: purchase_down_payments, vendor_prices, vendor_categories, '
            'transfer_orders, transfer_order_payments.\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian Pembelian'
        ),
        'ac': [
            'Uang muka pembelian: bayar DP dan alokasi ke faktur',
            'Harga pemasok per produk: CRUD dan terpakai saat buat PO',
            'Kategori pemasok: CRUD dan filter di list pemasok',
            'Perintah pembayaran dan transfer pemasok: alur multi-vendor transfer',
            'PHPUnit untuk setiap alur di atas',
        ],
    })

    cards.append({
        'name': '[MVP] Lengkapi buku besar: anggaran per akun, monitor anggaran, dan histori akun',
        'labels': ['MVP', 'P1', 'journal'],
        'desc': (
            'Context: COA, jurnal, dan laporan keuangan sudah ada di board, tetapi '
            'anggaran (budget), monitor anggaran, transfer anggaran, pencatatan beban, '
            'dan histori akun belum ada kartunya.\n\n'
            'Insight: Setiap jurnal di-post akan update actual_amount di anggaran. '
            'Pencatatan beban (expense accrual) menghasilkan jurnal akrual di akhir '
            'bulan dan jurnal pembalikan otomatis di periode berikutnya. Histori akun '
            'adalah report-only dari general_journals dengan drill-down.\n\n'
            'Flow: Set budget -> jurnal update actual -> monitor vs target. Transfer '
            'antar akun. Akrual -> reversing entry. Histori: drill-down per akun.\n\n'
            'Migration: account_budgets, account_budget_transfers, expense_accruals.\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian Buku Besar'
        ),
        'ac': [
            'Anggaran per akun per periode: CRUD',
            'Monitor anggaran: realisasi vs anggaran, indikator melebihi budget',
            'Transfer anggaran antar akun',
            'Histori akun: riwayat mutasi per akun dengan drill-down transaksi',
            'PHPUnit untuk anggaran, monitor, dan histori',
        ],
    })

    cards.append({
        'name': '[Non-MVP] Lengkapi persediaan: nomor seri, tracking batch per lot, dan permintaan material produksi',
        'labels': ['Non-MVP', 'P2', 'inventory'],
        'desc': (
            'Context: Item, unit, gudang, transfer, adjustment, opname, BOM, dan '
            'assembly sudah ada di board, tetapi nomor seri, tracking batch detail '
            'per lot, dan permintaan material produksi belum ada kartunya.\n\n'
            'Insight: Serial di-assign saat penerimaan (GR) dan di-track saat penjualan. '
            'Batch memakai FEFO (First Expired First Out) untuk picking. Material '
            'requisition terhubung ke BOM/assembly untuk auto-fill item produksi.\n\n'
            'Flow: GR -> assign serial/batch. Penjualan -> pilih serial -> sold. '
            'Batch -> FEFO. Requisition -> approve -> fulfil -> stock movement.\n\n'
            'Migration: product_serials, product_batches, material_requisitions(+items), '
            'ALTER stock_movements (batch_id, serial_id).\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian Persediaan'
        ),
        'ac': [
            'Nomor seri: assign saat penerimaan, track saat keluar',
            'Batch/lot: expiry date per lot dan FEFO saat picking',
            'Permintaan material produksi: requisition ke BOM/assembly',
            'Laporan umur stok per batch/seri',
            'PHPUnit untuk setiap alur di atas',
        ],
    })

    cards.append({
        'name': '[Non-MVP] Tambah analisa AI laporan: insight otomatis dari laporan keuangan dan penjualan',
        'labels': ['Non-MVP', 'P2', 'journal'],
        'desc': (
            'Context: Laporan keuangan inti sudah ada di board, tetapi fitur analisa '
            'AI/insight (menu Daftar Laporan Accurate) belum ada kartunya.\n\n'
            'Insight: Tiga tipe insight: trend (perbandingan revenue/expense/margin '
            'antar periode), anomaly (fluktuasi tidak wajar > threshold), dan summary '
            '(narrative dari laporan). Insight dibaca dari laporan yang sudah ada '
            'sehingga migration tetap ringan.\n\n'
            'Flow: Scheduled/manual trigger -> baca laporan -> analisa -> simpan ke '
            'report_insights -> tampilkan di dashboard.\n\n'
            'Migration: report_insights.\n\n'
            'Definition of Done: PHPUnit lulus, Pint + PHPStan clean, _progress.md update.\n'
            'Ref: modules/accurate/accurate-sidebar-menu.md bagian Daftar Laporan'
        ),
        'ac': [
            'Insight otomatis: tren revenue, expense, margin per periode',
            'Anomali: deteksi fluktuasi tidak wajar di akun utama',
            'Ringkasan naratif dari laporan keuangan',
            'PHPUnit untuk generator insight',
        ],
    })

    return cards


if __name__ == '__main__':
    main()

# Log Aktifitas

**Module:** `#accurate__company__audit`

## Fitur

- **Filter Data**: Filter log berdasarkan tanggal, tipe transaksi, pengguna, dan tipe tindakan
- **Cetak**: Mencetak daftar log aktifitas
- **Unduh XLS**: Ekspor daftar ke format Excel
- **Unduh PDF**: Ekspor daftar ke format PDF

Menu ini bertipe `INFORMATION` (read-only). Tidak ada form **Data Baru** karena
log aktifitas dihasilkan otomatis oleh sistem — satu-satunya record yang muncul
adalah jejak aktivitas pengguna (login, buat, ubah, hapus data di modul lain).

## Kolom Tabel

- Tgl Transaksi
- No/Nama Referensi
- Tipe Tindakan
- Tipe Transaksi
- Tanggal
- Pengguna
- Email
- Alamat IP

## Filter

| Filter | Tipe | Opsi Default |
|--------|------|--------------|
| Tgl Transaksi | DATE | - |
| Tanggal | DATE | - |
| Tipe Transaksi | LIST | 109 opsi |
| Pengguna | LIST | 1 opsi |
| Tipe Tindakan | LIST | 3 opsi |

### Opsi Tipe Tindakan

- Buat
- Hapus
- Ubah

### Opsi Pengguna

- haidi nurhadinata

### Opsi Tipe Transaksi (109)

- Akses Grup
- Akun Perkiraan
- Alokasi Biaya Produksi
- Anggaran
- Aset Tetap
- Barang & Jasa
- Cabang
- Departemen
- Desain Cetakan
- Disposisi Aset Tetap
- Distribusi Stok
- Etalase
- FOB
- Faktur Pembelian
- Faktur Penjualan
- Food Delivery
- Forecast PO
- Formula Produksi
- Gaji/Tunjangan
- Gudang
- Harga Pemasok
- Hasil Stok Opname
- Internet Banking
- Jurnal Umum
- Karyawan
- Katalog
- Kategori Aset
- Kategori Aset Tetap Pajak
- Kategori Barang
- Kategori Keuangan
- Kategori Pelanggan
- Kategori Pemasok
- Kategori Penjualan
- Kategori Transaksi Berulang
- Klaim Pelanggan
- Klaim Pemasok
- Koleksi
- Komisi Penjual
- Kontak
- Laporan Tersimpan
- Mata Uang
- Merek Barang
- Minimum Stok Cabang
- Pajak
- Pekerjaan Pesanan
- Pelanggan
- Pelunasan Pinjaman
- Pemasok
- Pembayaran
- Pembayaran Angsuran
- Pembayaran Pembelian
- Pemindahan Barang
- Penambahan Bahan Baku
- Penanggung Jawab
- Penawaran Penjualan
- Pencairan Pinjaman
- Pencatatan Beban
- Pencatatan Gaji
- Penerimaan
- Penerimaan Barang
- Penerimaan Penjualan
- Pengambilan Bahan Baku
- Pengaturan POS
- Pengaturan Sub Company Code
- Pengaturan Virtual Account
- Pengaturan e-Payment
- Pengepakan Barang
- Pengiriman
- Pengiriman Pesanan
- Pengisian Nomor Seri
- Penomoran
- Penyelesaian Barang Jadi
- Penyelesaian Pesanan
- Penyesuaian Harga/Diskon
- Penyesuaian Persediaan
- Penyetuju Transaksi
- Perintah Kerja
- Perintah Pembayaran
- Perintah Stok Opname
- Permintaan Barang
- Persiapan Bahan Baku
- Perubahan Aset Tetap
- Pesanan Pembelian
- Pesanan Penjualan
- Pihak Berwenang e-Faktur
- Pindah Aset
- Pinjaman Karyawan
- Preferensi
- Promo
- Proses Akhir Bulan
- Proyek
- Rencana Produksi
- Retur Pembelian
- Retur Penjualan
- SPT PPN/PPNBM
- Satuan Barang
- SmartLink Virtual Account
- SmartLink e-Commerce
- SmartLink e-Payment
- Standar Biaya Produksi
- Syarat Pembayaran
- Tahapan
- Tahapan Proses
- Target Penjualan
- Trade Portal
- Transfer Bank
- Tukar Faktur
- Uang Muka Pembelian
- Uang Muka Penjualan

## Input Fields

| Nama | Tipe | Fungsi |
|------|------|--------|
| keyword | text | Cari kata kunci pada daftar log |
| searchFilter | text | Cari kolom pada panel pengaturan kolom |
| selectedColumn | checkbox | Pilih kolom yang ditampilkan (8 kolom) |

Filter bertipe DATE (Tgl Transaksi, Tanggal) membuka panel rentang tanggal saat diklik. Filter bertipe LIST membuka panel pilihan sesuai opsi di atas.

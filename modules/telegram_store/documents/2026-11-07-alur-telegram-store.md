# Alur Telegram Store

## Ringkasan

Bot Telegram ini menghubungkan user dengan katalog produk Digiflazz. Mode transaksi dapat dipilih antara `Production` dan `Sandbox`. Harga produk yang ditampilkan sudah menggunakan **PPN 11%** sebelum markup.

## Alur Pengguna

### 1. Mulai Bot

1. User mengirim `/start` atau menekan tombol **Mulai**.
2. Bot menampilkan menu tombol:
   - **Mulai**
   - **Daftar Produk**
   - **Beli Produk**
   - **Cek Status**
   - **Isi Saldo**
   - **Mode Transaksi**
   - **Prod**
   - **Sandbox**
   - **Daftar Perintah**

### 2. Melihat Produk

1. User mengirim `/produk` atau menekan **Daftar Produk**.
2. Bot mengambil daftar produk dari Digiflazz.
3. Bot menyaring produk:
   - Free Fire tidak ditampilkan.
   - Produk seluler hanya menampilkan Telkomsel.
   - Produk non-seluler seperti PLN, games, voucher, dan e-money tetap tampil.
4. Bot mengurutkan produk:
   1. PLN.
   2. PDAM, jika tersedia.
   3. Telkomsel.
   4. Produk lain.
5. Bot menampilkan:
   - Daftar produk bernomor.
   - SKU dan harga final.
   - Tombol inline untuk tiap produk.
6. User bisa:
   - Menekan tombol produk.
   - Mengirim nomor produk, misalnya `1`.

### 3. Memilih Nomor Produk Secara Manual

1. Setelah `/produk`, user mengirim angka.
2. Bot mengonversi angka menjadi produk sesuai urutan tampilan.
3. Bot menampilkan:
   - Nama produk.
   - SKU.
   - Harga final dengan PPN dan markup.
4. Bot meminta nomor tujuan.

### 4. Membeli Produk

Ada dua cara.

#### Cara tombol atau angka

1. User memilih produk.
2. Bot meminta nomor tujuan.
3. User mengirim nomor tujuan.
4. Bot membuat order ke Digiflazz.
5. Bot menyimpan order lokal berdasarkan invoice.
6. Bot mengirim ringkasan:
   - Invoice.
   - Produk.
   - Status awal.

#### Cara cepat

1. User mengirim:
   - `/beli SKU nomor`
2. Bot langsung membuat order.
3. Bot mengirim invoice dan status.

### 5. Mengisi Saldo

1. User mengirim `/saldo` atau menekan **Isi Saldo**.
2. Bot menampilkan:
   - Mode aktif.
   - Saldo Digiflazz saat ini.
   - Pilihan nominal: `Rp 200.000`, `Rp 500.000`, `Rp 1.000.000`, `Rp 2.000.000`.
3. User memilih nominal.
4. Bot meminta format:
   - `/isidaldo nominal bank nama-pemilik`
5. User mengirim perintah tersebut.
6. Bot memanggil API deposit Digiflazz.
7. Digiflazz membuat tiket deposit.
8. Bot menampilkan:
   - Metode pembayaran.
   - Bank.
   - Nomor VA atau rekening tanpa spasi agar mudah disalin.
   - Nominal transfer.
   - Berita transfer atau kode unik.

Digiflazz tidak menyediakan QRIS pada endpoint deposit, jadi bot menggunakan bank transfer atau Virtual Account.

### 6. Memeriksa Status Transaksi

1. User mengirim `/cekstatus invoice`.
2. Bot membaca order lokal.
3. Bot mengirim permintaan status ke Digiflazz.
4. Jika provider memberikan status baru, bot memperbarui data order lokal.
5. Bot menampilkan:
   - Invoice.
   - Status terbaru.
   - Pesan provider.

### 7. Mengganti Mode

1. `/prod` mengaktifkan production key.
2. `/sandbox` mengaktifkan development key.
3. `/mode` menampilkan mode aktif.
4. Sandbox menggunakan flag testing pada transaksi.
5. Semua pengujian otomatis wajib memakai sandbox.

## Alur Teknis

```text
Telegram User
  -> Bot Telegram
    -> TelegramStoreBot
      -> TelegramStoreService
        -> DigiflazzClient
          -> Digiflazz API
```

## Status Dan Penyimpanan

- Saat ini order disimpan di `InMemoryOrderStore`.
- Data hilang jika bot direstart.
- Invoice dibuat otomatis dengan format `HN-YYYYMMDDHHMMSS-RANDOM`.
- Status order bisa diperbarui melalui `/cekstatus`.

## Kebutuhan Lanjutan

Untuk production yang stabil, sistem sebaiknya pindah ke database:

- `users`
- `orders`
- `deposit_tickets`
- `order_events`

This memudahkan audit transaksi, retry, dan sinkronisasi webhook Digiflazz.

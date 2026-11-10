# Progres Hardening dan Validasi Sandbox Telegram Store

Tanggal: 10 November 2026

## Ringkasan

Telegram Store sudah diperkuat untuk penggunaan jangka panjang. Pekerjaan mencakup pencegahan crash polling, persistensi transaksi, pesan proses, validasi deposit, filter produk, dan validasi end-to-end menggunakan sandbox Digiflazz.

## Yang Telah Dikerjakan

### 1. Anti-Crash Polling

- `getUpdates` yang gagal tidak menghentikan bot.
- `SystemExit` memicu restart polling.
- `KeyboardInterrupt` dihentikan secara graceful.
- Payload polling yang tidak valid di-skip.
- `update_id` yang tidak valid di-skip sebelum memicu handler.
- Callback acknowledgement dibungkus proteksi error agar tombol tetap berfungsi meski `answerCallbackQuery` gagal.

### 2. Supervisor Bot

Bot dijalankan melalui:

```bash
python3 -m modules.telegram_store.__main_supervisor__
```

Perilaku supervisor:

- Maksimal restart diatur oleh `TELEGRAM_STORE_MAX_RESTARTS`, default `5`.
- Delay restart eksponensial, default maksimal 30 detik.
- Proses yang hidup cukup lama dianggap healthy dan budget restart direset.
- `SIGTERM` dan `SIGINT` menghentikan child process tanpa restart.

### 3. Persistensi SQLite

State penting sudah disimpan menggunakan `SQLiteOrderStore` di `modules/telegram_store/data/store.sqlite3`.

Data yang tersimpan:

- Orders.
- Deposit tickets.
- Webhook events dengan deduplication.
- Audit logs.
- Update errors.
- Polling offset melalui tabel `bot_states`.

Konfigurasi SQLite:

- WAL mode.
- `busy_timeout = 5000`.
- `synchronous = NORMAL`.
- Integrity check tersedia di `/health`.

### 4. Loading UX

Agar bot tidak terlihat stuck, bot mengirim pesan proses sebelum operasi provider:

- `/produk`: `⏳ Memuat produk…`
- `/beli` atau checkout produk pilihan: `⏳ Memproses pesanan…`
- `/status` atau `/cekstatus`: `⏳ Memeriksa status…`

Pengiriman loading dan pesan hasil menggunakan `safe_send_message`, sehingga kegagalan Telegram tidak membuat order atau polling gagal.

Checkout juga punya recovery: jika order sudah dibuat tetapi pesan hasil gagal dikirim, state produk tetap dipulihkan dan bot mengarahkan user ke `/status`.

### 5. Deposit Digiflazz

Alur deposit:

1. User membuka `/saldo`.
2. Bot menampilkan saldo dan pilihan nominal.
3. User memilih nominal atau input manual.
4. User memilih bank.
5. User mengirim nama pemilik rekening.
6. Bot membuat ticket melalui API deposit Digiflazz.
7. Bot menampilkan nomor rekening dalam blok `code` agar mudah disalin.
8. Ticket deposit disimpan ke SQLite.

Perbaikan:

- Respons deposit dengan `rc` selain `00` ditolak sebelum disimpan.
- Nomor rekening dibersihkan dari spasi dan strip.
- Sandbox mendukung `Flip` dan `ShopeePay`.

### 6. Filter Produk

Produk berikut disaring di backend, bukan hanya di UI:

- Free Fire.
- SKU `kvision180d`.
- SKU `kvision30d`.
- SKU `ml10`.

Produk mobile hanya menampilkan Telkomsel. Brand seperti XL, Axis, Tri, Indosat, im3, Smartfren, dan sejenisnya tetap diblokir.

Ketika price list Digiflazz terkena rate limit dan mengembalikan array kosong, bot memakai cache produk dari `SQLiteProductCatalog` supaya daftar produk tetap tersedia.

### 7. Sandbox Purchase Safety

Mode production tetap mewajibkan saldo Digiflazz positif dan cukup untuk membeli produk.

Khusus `testing=True`, bot diizinkan membuat order sandbox meskipun saldo Digiflazz sedang `0`. Ini diperlukan karena endpoint sandbox Digiflazz tetap bisa memproses transaksi testing saat saldo buyer `0`.

Perilaku ini sudah dipisahkan dari production dan tidak melemahkan validasi saldo pada mode nyata.

### 8. Produk Tertentu Dalam Uji Real Sandbox

SKU `s10`, Telkomsel 10.000, digunakan untuk alur pembelian sandbox karena tersedia di price list dan catalog real.

Alur yang diuji:

1. `/produk s10`.
2. Pilih produk dari inline keyboard.
3. Buat order.
4. Terima status provider.
5. Simpan order ke SQLite.
6. Cek kembali status.

Status yang diterima dari provider dapat berupa `Sukses`, `Pending`, atau `Gagal`, tergantung skenario sandbox.

### 9. Whitelist IP Digiflazz

Digiflazz menolak permintaan sebelum IP terdaftar dengan pesan:

```text
IP Anda tidak kami kenali
```

IP aktif yang dipakai untuk testing real sandbox adalah:

```text
172.232.98.46
```

IP tersebut harus terdaftar pada setting IP Digiflazz untuk development dan production.

## Hasil Validasi

### Regression Lokal

Suite modul lulus:

```text
90 tests OK
```

Beberapa test real tetap dibatasi secara otomatis menggunakan `DIGIFLAZZ_REAL_TESTS=1`.

### Real Sandbox Dari VPS

Suite penuh dijalankan dari IP VPS yang sudah di-whitelist:

```text
DIGIFLAZZ_REAL_TESTS=1
153 tests OK
```

Yang sudah terverifikasi:

- `balance` berhasil.
- `price-list` berhasil dengan 74 produk.
- Deposit `Flip` berhasil membuat tiket.
- Deposit `ShopeePay` berhasil membuat tiket.
- Alur produk real berhasil.
- Order sandbox real berhasil dibuat.
- Status order dan persistensi berhasil.
- Webhook, audit, ledger, dan update error tetap berjalan tanpa crash.

## Status Saat Ini

```text
Runtime           : stabil untuk penggunaan jangka panjang
Sandbox           : 153/153 test lulus
Production        : belum diuji penuh
Persistensi       : aktif
Supervisor        : aktif
Loading UX        : aktif
Whitelist Digiflazz: aktif untuk VPS UC
```

## Batasan

- Production tidak diuji menggunakan transaksi berbayar nyata.
- Dana dari deposit belum bisa dinyatakan masuk sebelum konfirmasi nyata di dashboard Digiflazz.
- Webhook endpoint eksternal masih perlu dideploy agar update status otomatis masuk tanpa `/cekstatus`.
- Test UI/backend real lokal bisa gagal jika IP publik IndiHome berubah; jalankan dari VPS UC untuk hasil konsisten.

## Perintah Validasi

Jalankan regression cepat:

```bash
python3 -m unittest discover -s modules/telegram_store/tests -p 'test_telegram_store.py'
```

Jalankan regresi penuh tanpa provider real:

```bash
python3 -m unittest discover -s modules/telegram_store/tests
```

Jalankan suite real sandbox dari VPS:

```bash
PYTHONPATH=. \
DIGIFLAZZ_USERNAME=<username> \
DIGIFLAZZ_API_KEY=<production-key> \
DIGIFLAZZ_DEVELOPMENT_KEY=<development-key> \
DIGIFLAZZ_REAL_TESTS=1 \
python3 -m unittest discover -s modules/telegram_store/tests -t .
```

## Langkah Berikutnya

1. Deploy webhook Digiflazz untuk update status otomatis.
2. Tambah menu monitoring order pending/sukses/gagal.
3. Tambah admin menu untuk kontrol mode, markup, dan produk aktif.
4. Deploy bot ke VPS UC sebagai proses persistent.
5. Lakukan production smoke test dengan nominal kecil setelah deposit pertama benar-benar masuk.

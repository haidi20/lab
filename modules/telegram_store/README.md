# Telegram Digiflazz Store

Modul bot Telegram untuk toko digital yang terhubung ke Digiflazz sebagai buyer/reseller.

## Konfigurasi

Tambahkan nilai berikut ke `.env`:

```env
TELEGRAM_BOT_TOKEN=token-bot-telegram
TELEGRAM_BOT_USERNAME=@hn_assistent_bot
DIGIFLAZZ_USERNAME=username-digiflazz
DIGIFLAZZ_API_KEY=api-key-digiflazz
DIGIFLAZZ_TESTING=false
STORE_MARKUP_PERCENT=0
```

Jangan commit `.env` berisi kredensial asli.

## Menjalankan bot

```bash
python -m modules.telegram_store
```

Saat bot dijalankan, daftar perintah otomatis didaftarkan ke Telegram
melalui `setMyCommands`, sehingga tombol menu dan saran perintah muncul
di aplikasi Telegram.

## Perintah bot

- `/start`, `/help`, atau `/bantuan`: menampilkan menu tombol interaktif.
- `/produk [kata kunci]`: cari produk.
- `/beli <SKU> <nomor/id tujuan>`: buat transaksi.
- `/cekstatus <invoice>` atau `/status <invoice>`: cek status transaksi.

`/saldo` dinonaktifkan sampai payment gateway aktif. Perintah itu hanya
menampilkan pesan bahwa fitur belum tersedia.

Tombol menu di pesan `/start` memicu perintah yang sama melalui
callback query, jadi pengguna bisa memilih fitur tanpa mengetik.

## Catatan

Transaksi memakai alur buyer Digiflazz: SKU produk dikirim ke Digiflazz dengan `ref_id` invoice internal. Harga jual bisa dinaikkan dengan `STORE_MARKUP_PERCENT`. Mode `DIGIFLAZZ_TESTING=true` hanya untuk pengujian sandbox Digiflazz.

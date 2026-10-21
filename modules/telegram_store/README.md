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

## Perintah bot

- `/start` atau `/help`: bantuan.
- `/produk [kata kunci]`: cari produk.
- `/beli <SKU> <nomor/id tujuan>`: buat transaksi.
- `/status <invoice>`: cek status transaksi.
- `/saldo`: cek saldo Digiflazz.

## Catatan

Transaksi memakai alur buyer Digiflazz: SKU produk dikirim ke Digiflazz dengan `ref_id` invoice internal. Harga jual bisa dinaikkan dengan `STORE_MARKUP_PERCENT`. Mode `DIGIFLAZZ_TESTING=true` hanya untuk pengujian sandbox Digiflazz.

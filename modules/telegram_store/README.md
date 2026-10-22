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
TRELLO_API_KEY=trello-api-key
TRELLO_TOKEN=trello-token
TRELLO_PROGRESS_LIST_ID=trello-progress-list-id
HERMES_HOME=C:\Users\nhaid\AppData\Local\hermes
HERMES_LIVE_INTERVAL_SECONDS=20
HERMES_LIVE_DURATION_SECONDS=60
HERMES_CHAT_TIMEOUT_SECONDS=900
HERMES_WORKDIR=D:\projects\klinik-git
HERMES_PROVIDER_BASE_URL=http://127.0.0.1:20128/v1
HERMES_PROVIDER_API_KEY=provider-key
HERMES_PROVIDER_MODEL=cd
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
- `/hermes`, `/starthermes`, atau `/statushermes`: lihat kartu Trello di
  progress, checklist-nya, dan status cron Hermes.
- `/hermeslive` atau `/livehermes`: mulai monitoring realtime. Bot mengirim
  pesan baru hanya saat kartu, checklist, status cron, atau log aktivitas
  Hermes berubah. Status memuat proses `Berpikir`, `Analisa`, dan `Proses`.
  Sesi berjalan 1 menit, memeriksa tiap 5 detik, lalu berhenti otomatis.
- `/hermesstop` atau `/stophermes`: hentikan monitoring realtime.
- `/hubungihermes <pertanyaan>` atau `/tanyahermes <pertanyaan>`: kirim
  pertanyaan ke Hermes dan memulai mode komunikasi. Setelah itu, pesan biasa
  tanpa slash otomatis dikirim ke Hermes sampai mode ditutup. Hermes menerima
  konteks status terbaru. Mode ini memakai akses penuh Hermes dengan
  `--yolo`, jadi Hermes boleh menjalankan perubahan sesuai permintaan.
  Kalau gateway Hermes terkunci sesi Windows, bot memakai fallback provider
  Hermes; fallback ini hanya menjawab teks dan tidak menjalankan tool.
- `/akhirihermes` atau `/tutuphermes`: akhiri mode komunikasi Hermes.

`/saldo` dinonaktifkan sampai payment gateway aktif. Perintah itu hanya
menampilkan pesan bahwa fitur belum tersedia.

Tombol menu di pesan `/start` memicu perintah yang sama melalui
callback query, jadi pengguna bisa memilih fitur tanpa mengetik.

Menu `Status Hermes` dan `Hermes Live` hanya aktif kalau `TRELLO_API_KEY`
dan `TRELLO_TOKEN` sudah diisi. Kalau belum, bot tetap jalan dan menampilkan
pesan bahwa fitur belum tersedia.

## Catatan

Transaksi memakai alur buyer Digiflazz: SKU produk dikirim ke Digiflazz dengan `ref_id` invoice internal. Harga jual bisa dinaikkan dengan `STORE_MARKUP_PERCENT`. Mode `DIGIFLAZZ_TESTING=true` hanya untuk pengujian sandbox Digiflazz.

# Telegram Group Reader - Rust

Implementasi Rust dengan fungsi yang sama dengan modul Python telegram_group_reader:
- ambil semua dialog group/channel,
- ambil pesan N hari terakhir (SYNC_DAYS),
- upsert ke MySQL (telegram_groups, telegram_messages),
- pakai schema dan aturan upsert yang sama dengan Python.

Perbandingan real Python vs Rust bisa dilihat di ringkasan benchmark pada sesi kerja.

## Syarat

- Rust (stable, cargo di PATH)
- .env di root repo berisi:
  TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION,
  MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
- MySQL lokal sudah jalan dan database sesuai .env.
- Session Telethon sudah ada (telegram_group_reader.session).

## Konversi session (sekali)

Session Telethon tidak kompatibel langsung dengan grammers Rust. Jalankan:

`powershell
cd D:\learns\random
python modules\telegram_group_reader\rust\convert_session.py
`

Ini menambahkan tabel session grammers ke file session yang sudah ada dan membuat backup .session.bak.

## Jalankan

`powershell
cd D:\learns\random
cargo run --release --manifest-path modules\telegram_group_reader\rust\Cargo.toml
`

Program otomatis login memakai session hasil konversi. Jika session belum ada / tidak valid,
program meminta nomor telepon + kode login secara interaktif.

## Test

`powershell
cargo test --manifest-path modules\telegram_group_reader\rust\Cargo.toml
`

## Catatan

- SYNC_DAYS adalah konstanta di src/main.rs (default 30), bukan environment variable.
- Filter waktu memakai perhitungan yang sama dengan Python: Asia/Makassar (UTC+8) sebagai cutoff.
- Upsert Rust memakai batch 500 baris agar aman terhadap max_allowed_packet.

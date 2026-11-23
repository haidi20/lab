# Kesimpulan - Paket AI Unlimited dari Isi Pesan Grup Telegram (Rust)

Analisa ini dibuat oleh binary Rust `analyze_ai_packages` dengan membaca **isi pesan** dari tabel `telegram_messages` di MySQL.

Catatan: yang dianalisa adalah **message/text**, bukan nama grup. Nama grup hanya konteks tambahan.

## Ringkasan Data

- waktu running program Rust: **0.24 detik**
- total pesan dengan kata `unlimited`: **1905**
- pesan yang cocok dengan paket AI unlimited: **1533**
- pesan terlama di DB: **2026-10-23 21:53:34**
- pesan terbaru di DB: **2026-11-22 23:16:08**

## Ringkasan Berdasarkan Masa Waktu Paket AI

### 1 hari

- **Provider/penjual:** GATER | **pesan:** 2
  - Harga: tidak disebut eksplisit
  - Model AI: DeepSeek, GLM, Deepseek V4.1 Flash 1014, GLM 5.3 Flash
- **Provider/penjual:** Jerouter V2 | **pesan:** 504
  - Harga: tidak disebut eksplisit
  - Model AI: tidak disebut eksplisit
- **Provider/penjual:** Limo Router | **pesan:** 10
  - Harga paket AI: Rp 5.000 (10 pesan)
  - Model AI: DeepSeek, Qwen, GLM, STEP 5, KIMI
- **Provider/penjual:** NilovrAI | **pesan:** 1
  - Harga: tidak disebut eksplisit
  - Model AI: DeepSeek, Qwen, GLM, KIMI, Claude, GPT
- **Provider/penjual:** Tidak disebut | **pesan:** 7
  - Harga paket AI: Rp 7.000 (2 pesan), Rp 30.000 (3 pesan)
  - Model AI: Claude Opus 5.5, GPT-6.1, Claude, DeepSeek, GLM, Longcat

### 3 hari

- **Provider/penjual:** GATER | **pesan:** 1
  - Harga: tidak disebut eksplisit
  - Model AI: DeepSeek, GLM, Deepseek V4.1 Flash 1014, GLM 5.3 Flash
- **Provider/penjual:** Jerouter V2 | **pesan:** 242
  - Harga: tidak disebut eksplisit
  - Model AI: tidak disebut eksplisit
- **Provider/penjual:** Limo Router | **pesan:** 5
  - Harga paket AI: Rp 10.000 (5 pesan)
  - Model AI: DeepSeek, Qwen, GLM, STEP 5, KIMI

### 7 hari

- **Provider/penjual:** Jerouter V2 | **pesan:** 501
  - Harga: tidak disebut eksplisit
  - Model AI: tidak disebut eksplisit
- **Provider/penjual:** Tidak disebut | **pesan:** 2
  - Harga: tidak disebut eksplisit
  - Model AI: tidak disebut eksplisit

### 10 hari

- **Provider/penjual:** Limo Router | **pesan:** 5
  - Harga paket AI: Rp 20.000 (5 pesan)
  - Model AI: DeepSeek, Qwen, GLM, STEP 5, KIMI

### 14 hari

- **Provider/penjual:** Jerouter V2 | **pesan:** 170
  - Harga: tidak disebut eksplisit
  - Model AI: tidak disebut eksplisit

### 30 hari / 1 bulan

- **Provider/penjual:** Jerouter V2 | **pesan:** 79
  - Harga: tidak disebut eksplisit
  - Model AI: tidak disebut eksplisit
- **Provider/penjual:** Kangkung Store | **pesan:** 9
  - Harga paket AI: Rp 45.000 (9 pesan)
  - Model AI: DeepSeek, GLM, Solar
- **Provider/penjual:** Limo Router | **pesan:** 5
  - Harga paket AI: Rp 40.000 (5 pesan)
  - Model AI: DeepSeek, Qwen, GLM, STEP 5, KIMI
- **Provider/penjual:** NilovrAI | **pesan:** 1
  - Harga: tidak disebut eksplisit
  - Model AI: tidak disebut eksplisit
- **Provider/penjual:** Tidak disebut | **pesan:** 9
  - Harga paket AI: Rp 37.500 (1 pesan)
  - Model AI: DeepSeek, GLM, Solar

## Kesimpulan

Dari isi pesan grup Telegram yang tersimpan, paket AI Unlimited yang terdeteksi mencakup durasi **1 hari, 3 hari, 7 hari, 14 hari, dan 30 hari / 1 bulan**.

Pola dominan berasal dari notifikasi aktivasi dengan paket:

- `Trial` = 1 hari
- `Basic` = 3 hari
- `Plus` = 7 hari
- `Essential` = 14 hari
- `Pro` = 30 hari / 1 bulan

Harga yang ditampilkan hanya harga paket model AI yang terdeteksi eksplisit dari isi pesan. Voucher, paket data, dan angka konteks seperti RPM/context/token tidak dimasukkan.

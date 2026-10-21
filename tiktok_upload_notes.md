# Catatan Lengkap: Upload Konten Video ke TikTok

> Tanggal: 2026-10-21
> Konteks: riset cara upload video ke TikTok otomatis dari project (Python/laptop), tanpa melanggar ToS.

## 1. Pilihan Cara Upload

### Opsi 1 - Otomasi Browser (Selenium/Playwright) - TIDAK DISARANKAN

Secara teknis bisa (script buka tiktok.com, login, klik upload), tetapi:

- Melanggar ToS TikTok - risiko shadowban, video tidak didistribusikan, atau banned permanen.
- TikTok aktif mendeteksi otomasi (CAPTCHA, behavioral check, device fingerprint).
- Upload hasil otomasi sering ditandai algoritma sebagai konten low quality.

Kesimpulan: jangan dipakai untuk akun serius.

### Opsi 2 - TikTok Content Posting API (Resmi) - REKOMENDASI UTAMA

Cara resmi yang dirancang untuk upload otomatis:

1. Daftar developer di https://developers.tiktok.com
2. Buat app, aktifkan Content Posting API.
3. OAuth login sekali untuk dapat access token.
4. Upload video via API (direct post atau draft).

Catatan penting:

- App yang belum diaudit: video ter-post sebagai private/self-only.
- Setelah audit TikTok lolos: boleh public post.
- Untuk akun sendiri, self-only + publish manual via app sudah cukup untuk banyak kebutuhan.

### Opsi 3 - Scheduler Pihak Ketiga Resmi

Tool dengan partnership resmi TikTok - upload/schedule lewat mereka tanpa
daftar developer sendiri:

| Tool | Catatan |
|---|---|
| Buffer / Later / Hootsuite | Partnership resmi, ada free tier |
| Postiz / Mixpost (self-hosted, open source) | Pakai API resmi TikTok di belakang layar; kontrol penuh, gratis |
| SocialBee / Pallyy | Alternatif serupa |

### Opsi 4 - Draft + Publish Manual (Semi-Otomatis)

Content Posting API mode draft: video terkirim ke akun sebagai draft,
kamu buka app, review, tekan post. Legal, aman, hemat waktu, dan
algoritma tidak membedakan.

## 2. Masalah Registrasi Developer: Email

Beberapa layanan developer kurang mempercayai email free generic (Gmail)
untuk registrasi app. Solusi:

| Solusi | Biaya | Cara kerja |
|---|---|---|
| Cloudflare Email Routing | Gratis | Email `dev@domain-sendiri` di-forward ke Gmail; kirim/terima tetap nyaman |
| Zoho Mail Free | Gratis | Mailbox penuh di domain sendiri, webmail + IMAP |
| Outlook.com | Gratis | Alternatif yang sering diterima karena bukan throwaway |

Rekomendasi: Cloudflare Email Routing di domain sendiri
(contoh: `dev@rhantech.com`). App dengan email domain sendiri juga lebih
mudah lolos audit Content Posting API.

## 3. Perbandingan Opsi

| | Postiz (self-host) | Buffer (free) | Content Posting API langsung |
|---|---|---|---|
| Biaya | Rp0 | Rp0 (limited) | Rp0 |
| Kontrol dari kode | Ada API internal | Tidak | Penuh |
| Setup | Sedang | Sangat mudah | Sedang-berat (daftar dev + audit) |
| Multi-platform | 9+ platform | 3 channel (free) | Per-platform manual |
| Risiko akun | Rendah (API resmi) | Rendah | Rendah |
| Maintenance | Sendiri | Mereka | Sendiri |

## 4. Keputusan: Postiz + Cloudflare Tunnel di Laptop

Alasan memilih Postiz:

- Gratis dan open source (self-hosted).
- Multi-platform: TikTok, Instagram, YouTube, X, LinkedIn, Facebook,
  Threads, Pinterest.
- Punya REST API internal - bisa di-trigger dari script Python sendiri.
- Data (kredensial akun, jadwal) tersimpan di server sendiri.
- Aktif dikembangkan, komunitas besar.

Kekurangan yang harus disadari:

- Setup awal 30-60 menit (Docker + OAuth per platform).
- Upload TikTok lewat app resmi Postiz - terikat kebijakan/limit app
  mereka; app non-audited biasanya post sebagai private/self-only.
- Maintenance (update, backup, monitoring) jadi tanggung jawab sendiri.
- Butuh 1-2 GB RAM untuk stack (Node + Redis + PostgreSQL).
- Scheduler hanya jalan selagi laptop nyala + Docker running; kalau
  laptop sleep, post tertunda.
- AGPL license - ada kewajiban buka kode kalau dijual sebagai SaaS turunan.

## 5. Setup Postiz di Laptop + Cloudflare Tunnel

### Arsitektur

```text
Laptop Windows 11
  Docker Desktop
    - Postiz (app)
    - PostgreSQL + Redis
    - Cloudflare Tunnel (connector)
  postiz.rhantech.com (Cloudflare) -> tunnel -> localhost:3000
```

### Prasyarat

1. Docker Desktop terinstall dan running (belum ada di laptop - harus
   install dari https://www.docker.com/products/docker-desktop/).
2. Login Cloudflare sekali via browser saat `cloudflared tunnel login`
   (hanya pemilik akun yang bisa).
3. Domain sudah di Cloudflare: `rhantech.com` sudah terverifikasi aktif
   (DNS A/AAAA mengarah ke Cloudflare proxy).

### Langkah Setup

1. Install Docker Desktop, jalankan.
2. Install `cloudflared` (Windows binary dari Cloudflare).
3. `cloudflared tunnel login` - pilih domain di browser.
4. `cloudflared tunnel create postiz` - dapatkan tunnel UUID + credentials.
5. Route DNS: `cloudflared tunnel route dns postiz postiz.rhantech.com`
   (subdomain dibuat otomatis - TIDAK PERLU BELI DOMAIN BARU).
6. Jalankan Postiz stack via docker compose (app + PostgreSQL + Redis).
7. Config tunnel: `postiz.rhantech.com` -> `http://localhost:3000`.
8. Jalankan connector: `cloudflared tunnel run postiz`.
9. Buka `https://postiz.rhantech.com` - Postiz siap dipakai.
10. Connect channel TikTok via OAuth dari dashboard Postiz
    (butuh Client ID/Secret dari dashboard developer platform).

### Alternatif Tanpa Ribet

Postiz Cloud (hosted resmi di postiz.com):

- Free tier 1 channel.
- Laptop bebas mati - scheduling jalan di server mereka.
- Kekurangan: data di pihak ketiga, free tier terbatas.

## 6. Risiko & Kepatuhan

- Jangan pakai otomasi browser untuk upload - melanggar ToS.
- Semua jalur yang dipilih (Content Posting API / Postiz / Buffer) tetap
  melewati API resmi - risiko akun rendah.
- App non-audited = post private/self-only; ajukan audit untuk public post.
- Jangan hardcode access token; simpan di .env dan jangan commit.

## 7. Rencana Tindak Lanjut

1. Install Docker Desktop di laptop (user).
2. Setup Cloudflare Tunnel + Postiz stack (agent, setelah Docker siap).
3. Connect channel TikTok + test upload draft pertama.
4. Evaluasi: kalau butuh public post otomatis dari pipeline Python,
   daftar TikTok developer (pakai email domain sendiri) dan buat modul
   Content Posting API sendiri dengan TDD.

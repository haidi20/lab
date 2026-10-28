# Accurate Human Automation

## Tujuan

Skill ini dipakai setiap kali agent menjalankan otomasi Accurate.
Tujuannya adalah membuat interaksi berjalan seperti manusia biasa:
terbaca, berjeda, dan tidak terlihat seperti aksi bot.

## Prinsip Wajib

- Analisa Accurate WAJIB menggunakan MCP REA atau CLI REA
  `capture-browser-scenario` untuk observasi berbasis browser.
- Gunakan browser headless bila memungkinkan, tetapi jangan mempercepat
  interaksi karena berjalan di background.
- Jangan menjalankan aksi beruntun tanpa jeda.
- Jangan langsung mengisi form sebelum halaman stabil.
- Jangan retry cepat. Batasi maksimal tiga percobaan dan beri jeda acak.
- Jangan menulis email atau password asli ke skenario, log, capture,
  skill, atau dokumentasi.
- Ambil kredensial hanya dari `ACCURATE_EMAIL` dan `ACCURATE_PASSWORD`.
- Capture hanya data yang dibutuhkan. Hindari DOM/network besar tanpa alasan.

## Konfigurasi Dasar

Gunakan Chrome yang terpasang dan mode headless. Viewport 1440x900,
locale `id-ID`, dan timezone `Asia/Makassar`.

## Alur Human-Paced

1. Buka URL Accurate.
2. Tunggu form login stabil 2-5 detik.
3. Isi email, lalu beri jeda 500-1.500 ms.
4. Isi password, lalu beri jeda 800-2.000 ms.
5. Klik tombol `Masuk`.
6. Tunggu halaman `/manage` stabil 5-10 detik.
7. Jika dialog 2FA muncul, tunggu 1-3 detik, lalu klik `Nanti Saja`.
8. Diamkan daftar perusahaan 3-8 detik.
9. Klik kartu perusahaan yang dituju.
10. Tunggu tab atau jendela perusahaan terbuka.
11. Buka halaman tujuan setelah sesi perusahaan aktif.

## Selector Teruji

| Elemen | Selector |
| --- | --- |
| Email | `getByRole('textbox', { name: 'Email atau No Handphone Akun Accurate Anda' })` |
| Password | `#password` |
| Tombol Masuk | `getByRole('button', { name: 'Masuk' })` |
| Dialog 2FA | `getByRole('button', { name: 'Nanti Saja' })` |
| Kartu perusahaan | `div.cursor-pointer:has(h3:text-is('cy'))` |

Jangan memakai locator role `Password` karena Playwright menemukan dua
elemen: `#password` untuk login dan `#registerPassword` untuk registrasi.

## Penanganan Dialog 2FA

Dialog 2FA tidak selalu muncul. Jangan menjadikan tombol `Nanti Saja`
sebagai satu-satunya kondisi tunggu.

1. Tunggu 5-10 detik setelah login.
2. Tekan `Escape` pada `body`.
3. Tunggu kartu perusahaan muncul.
4. Klik `Nanti Saja` hanya bila dialog masih terlihat.

## Membuka Perusahaan

Kartu perusahaan memakai handler Knockout
`click:$root.selectOpenedDatabase`. Handler dapat memanggil `window.open`,
sehingga URL root bisa tetap di `/manage`. Jangan anggap gagal hanya karena
URL root tidak berubah. Tunggu popup, tab baru, atau gunakan URL langsung
hasil data perusahaan.

Ambil ulang ID perusahaan dari halaman `/manage` saat otomasi dijalankan.
Jangan mengandalkan ID dari dokumentasi.

## Pola Jeda

Jangan memakai delay tetap untuk semua run. Variasikan jeda manusia:

| Aksi | Jeda |
| --- | --- |
| Sebelum mengisi email | 1-3 detik |
| Setelah mengisi email | 500-1.500 ms |
| Setelah mengisi password | 800-2.000 ms |
| Sebelum klik `Masuk` | 300-1.000 ms |
| Setelah login | 5-10 detik |
| Sebelum klik perusahaan | 3-8 detik |
| Sebelum retry | 10-30 detik |

## Interaksi Natural

Untuk input yang perlu terlihat seperti diketik manusia:

- Gunakan `pressSequentially` pada Playwright dengan delay acak 75-180 ms
  per karakter.
- Gunakan `fill` hanya untuk password atau ketika runner tidak mendukung
  pengetikan per karakter.
- Jangan memakai shortcut DOM atau injeksi nilai langsung untuk
  menghindari alur aplikasi.

## Checklist Sebelum Menjalankan

- [ ] Kredensial dibaca dari `.env`.
- [ ] Browser headless.
- [ ] Tidak ada delay nol antar aksi.
- [ ] Retry maksimal tiga kali.
- [ ] Dialog 2FA tidak dianggap wajib muncul.
- [ ] Popup atau tab baru ditunggu dengan benar.
- [ ] Tidak ada kredensial pada hasil capture atau log.
- [ ] Skenario hanya menyimpan data yang benar-benar diperlukan.

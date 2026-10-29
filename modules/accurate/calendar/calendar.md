# Kalender

**Module:** `#accurate__company__calendar`
**Tipe Modul:** `None`
**Capture:** 2026-10-29T08:14:00+08:00 ? perusahaan `cy` (database `3058374`).

## Fitur
- Tampilkan kalender bulan/minggu/hari
- Buat kalender
- Buat event
- Subscribe kalender
- Drag/drop dan ubah ukuran event
- Kelola hak akses kalender

## Form Data Baru
Menu ini tidak memakai form tambah standar; dialog khusus berikut dipakai untuk membuat kalender/event.

### Form Kalender
Trigger: Buat Baru atau pilih area kalender.

| Field | Input | Tipe | Wajib | Sumber Data |
|---|---|---|---|---|
| Jenis Kalender | `type` | select | Ya | Jenis kalender yang tersedia pada capture. |
| Nama Kalender | `name` | text | Ya | Input manual pengguna. |
| Deskripsi | `description` | textarea | Tidak | Input manual pengguna. |
| Semua Pengguna / Grup / Pengguna | `usedViewAllUser; userRoleAccessList; userAccessList` | checkbox/lookup | Tidak | Pengguna dan grup akses perusahaan. |

### Form Event
Trigger: Pilih tanggal atau klik event.

| Field | Input | Tipe | Wajib | Sumber Data |
|---|---|---|---|---|
| Kalender | `calendarId` | select | Ya | Daftar kalender Kegiatan. |
| Nama Event | `title` | text | Ya | Input manual pengguna. |
| Tanggal Mulai | `eventStart` | date | Ya | Tanggal dipilih dari kalender. |
| Sepanjang Hari | `allDay` | checkbox | Tidak | Input manual pengguna. |
| Deskripsi | `description` | textarea | Tidak | Input manual pengguna. |

### Form Subscribe
Trigger: Tombol Subscribe.

| Field | Input | Tipe | Wajib | Sumber Data |
|---|---|---|---|---|
| Kata kunci | `keywords` | text | Tidak | Daftar kalender yang dapat disubscribe. |

### Form Hapus Kalender
Trigger: Hapus kalender.

| Field | Input | Tipe | Wajib | Sumber Data |
|---|---|---|---|---|
| Aksi Hapus | `action` | radio | Ya | Pilihan hak administrasi kalender. |

## Daftar & Filter

### Tombol Toolbar

| Tombol | Hint/Label |
|---|---|

### Filter

| Key | Label | Tipe | Opsi |
|---|---|---|---|
| - | Tidak ada filter dinamis pada capture | - | - |

## Kolom Tabel

| Key | Label | Default Tampil | Tipe |
|---|---|---|---|
| - | Kalender tidak memakai tabel data standar | - | - |

Record aktual tersimpan di `data.json`: **0 baris**, status `Belum ada kalender`.

## Sumber Data

| Cakupan | Sumber | Bukti Capture |
|---|---|---|
| Kalender | Kalender Kegiatan yang dibuat/disubscribe pengguna. | Form kalender dan teks `Belum ada kalender` pada panel Kegiatan. |
| Event | Event manual dan jadwal dari modul terkait (pembayaran, pengiriman, jatuh tempo, stok opname, dll.). | Daftar tipe event pada filter/konfigurasi kalender. |
| Hak akses | Pengguna/grup akses. | Lookup `/accurate/entity-access/search-user.do` dan `/accurate/entity-access/search-user-role.do`. |

## Catatan Analisa

- Analisa berbasis observasi browser; tidak menggunakan screenshot.
- REA `capture-browser-scenario` dipakai untuk skenario login/navigasi; CLI konsisten timeout pada klik pembuka modul setelah tiga percobaan.
- Struktur modul, form, filter, dan kolom diekstrak dari DOM capture yang valid.

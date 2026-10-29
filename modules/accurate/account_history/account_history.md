# Histori Akun

**Module:** `#accurate__general-ledger__account-history`
**Tipe Modul:** `INFORMATION`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Tampilkan histori akun
- Filter akun dan periode
- Toggle Debit/Kredit
- Ekspor XLS
- Buka transaksi sumber

## Form Data Baru
Tidak ada form tambah data standar. Menu informasi histori; tidak ada endpoint tambah atau model data baru.

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `helpUrl` | `fitur-buku-besar/histori-akun` |

## Daftar & Filter
| Key | Label | Tipe | Default/Tampil |
|---|---|---|---|
| `account` | Akun Perkiraan | LOOKUP | Ya |
| `fromDate` | Dari Tanggal | DATE | Ya |
| `toDate` | s/d Tanggal | DATE | Ya |
| `toggleDrCr` | Tampilkan Debit/Kredit | BOOLEAN | Tidak |

## Kolom Tabel
Tidak ada data kolom yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

Belum ada capture tabel yang valid; `data.json` memakai **0 baris** dan status `not_captured`, bukan klaim tabel benar-benar kosong.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/account_history.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

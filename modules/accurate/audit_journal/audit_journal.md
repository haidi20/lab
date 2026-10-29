# Log Aktifitas Jurnal

**Module:** `#accurate__company__audit-journal`
**Tipe Modul:** `INFORMATION`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Lihat log aktifitas jurnal
- Cari log
- Detail versi perubahan
- Filter versi
- Buka transaksi terkait

## Form Data Baru
Tidak ada form tambah data standar. Model menetapkan canAddNew = false; modul hanya menampung dan menampilkan log.

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `formHelpUrl` | `/accurate/company/help-audit-journal.do` |
| `helpUrl` | `fitur-buku-besar/log-aktifitas-jurnal` |
| `htmlUrl` | `/accurate/company/audit-journal.do` |
| `initUrl` | `/accurate/company/init-audit-journal.do` |
| `searchUrl` | `/accurate/company/search-audit-journal.do` |
| `selectUrl` | `/accurate/company/detail-audit-journal.do` |

## Daftar & Filter
| Key | Label | Tipe | Default/Tampil |
|---|---|---|---|
| `filterVersion` | Versi Pembaruan | LIST | Ya |

## Kolom Tabel
Tidak ada data kolom yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

Belum ada capture tabel yang valid; `data.json` memakai **0 baris** dan status `not_captured`, bukan klaim tabel benar-benar kosong.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/audit_journal.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

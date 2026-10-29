# Monitor Anggaran

**Module:** `#accurate__budget-target__accountbudget-monitor`
**Tipe Modul:** `INFORMATION`
**Capture:** 2026-10-29T12:05:00+08:00 - perusahaan `cy` (database `3058374`).

## Fitur
- Monitor anggaran
- Filter lingkup dan periode
- Ringkasan anggaran/terpakai/tersedia
- Detail akun anggaran

## Form Data Baru
Tidak ada form tambah data standar. Menu informasi/monitor; model tidak memiliki endpoint simpan atau tombol tambah data.

### Endpoint Model
| Properti | Endpoint |
|---|---|
| `helpUrl` | `fitur-persediaan/barang-per-gudang` |
| `htmlUrl` | `/accurate/budget-target/accountbudget-monitor.do` |
| `initUrl` | `/accurate/budget-target/init-accountbudget-monitor.do` |

## Daftar & Filter
| Key | Label | Tipe | Default/Tampil |
|---|---|---|---|
| `scopeType` | Lingkup | LIST | Ya |
| `period` | Periode | LOOKUP | Tidak |
| `budgetYear` | Tahun Anggaran | NUMBER | Ya |
| `budgetMonth` | Bulan Anggaran | NUMBER | Ya |
| `department` | Departemen | LOOKUP | Tidak |
| `project` | Proyek | LOOKUP | Tidak |
| `branch` | Cabang | LOOKUP | Tidak |

## Kolom Tabel
Tidak ada data kolom yang terekam pada bukti REA yang tersedia. Tidak ditulis sebagai asumsi.

Belum ada capture tabel yang valid; `data.json` memakai **0 baris** dan status `not_captured`, bukan klaim tabel benar-benar kosong.

## Sumber Data
| Cakupan | Sumber | Bukti |
|---|---|---|
| Logika modul, form, endpoint | tmp_rea/accurate_models/accountbudget_monitor.js | REA analyze-javascript-application: tmp_rea/accurate_models_rea.json |
| Perusahaan aktif | Sesi Accurate perusahaan cy (database 3058374) | REA capture-browser-scenario |

## Catatan Analisa
- Analisa berbasis REA; tidak menggunakan screenshot.
- `glaccount` memakai DOM capture valid; delapan modul lain dianalisa dari model JavaScript hasil REA.
- Navigasi sidebar, goto `.do`, klik perusahaan, dan endpoint `init` tidak menghasilkan DOM/tabel runtime untuk delapan modul lain setelah batas retry.
- `data.json` modul tanpa capture tabel sengaja kosong dan diberi status `not_captured`.

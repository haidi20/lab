# Target Penjualan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nama Target | `name` | text | Ya | - |
| Tipe Target | `salutation` | select | Tidak | salutation: Per Barang, Per Kategori Barang, Per Penjual, Per Bulan |
| Penjualan Cabang | `branch` | select | Tidak | branch: [Semua Cabang], Kantor Pusat |
| Dari Tanggal | `fromDate` | date | Tidak | - |
| S/d Tanggal | `toDate` | date | Ya | - |
| Penganalisa | `analystName` | text | Tidak | - |

### Detail
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Rincian Barang | `searchDetailItem`, `searchKeywordItem` | lookup, text | Tidak | - |

### Info Lainnya
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Catatan | `notes` | textarea | Tidak | - |

### Tombol Form
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
| Field | Nilai Tampil |
| --- | --- |
| `salesTargetTypeFilter` — Tipe Target | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `analystName` | Penganalisa | Opsional |
| `generalTargetYear` | Tahun | Opsional |
| `fromDate` | Dari Tanggal | Ya |
| `toDate` | S/d Tanggal | Ya |
| `notes` | Catatan | Opsional |
| `name` | Nama | Ya |
| `branchName` | Cabang | Opsional |
| `salesTargetTypeName` | Tipe Target | Opsional |

## Sumber Data
- `/accurate/budget-target/sales-target.do`
- `/accurate/inventory/`
- `/accurate/inventory/detail-lookup-item.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

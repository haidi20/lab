# Penyesuaian Harga/Diskon

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Penyesuaian Harga/Diskon |
| Kategori Penjualan | `priceCategory` | lookup | Ya | - |
| Tipe Penyesuaian | `salesAdjustmentType` | select | Tidak | salesAdjustmentType: Harga, Diskon (%) |
| Mulai Berlaku | `transDate` | date | Ya | - |
| Dipakai di Cabang | `listBranch` | lookup | Ya | - |
| Non Aktif | `suspended` | checkbox | Tidak | - |

### Detail
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Rincian Barang | `searchDetailItem`, `searchKeywordItem` | lookup, text | Ya | - |

### Info Lainnya
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Keterangan | `description` | textarea | Tidak | - |

### Tombol Form
- `btnGetFrom` — Ambil Favorit.
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
| Field | Nilai Tampil |
| --- | --- |
| `transDateFilter` — Tanggal | Semua |
| `suspendedFilter` — Non Aktif | Semua |
| `salesAdjustmentTypeFilter` — Tipe Penyesuaian | Semua |
| `priceCategoryFilter` — Kategori Penjualan | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `suspended` | Non Aktif | Opsional |
| `number` | Nomor # | Ya |
| `transDate` | Mulai Berlaku | Ya |
| `priceCategory.name` | Kategori Penjualan | Ya |
| `description` | Keterangan | Ya |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `branch.name` | Cabang #1 | Opsional |
| `endEffectiveDate` | Tanggal Berakhir | Ya |
| `salesAdjustmentTypeName` | Tipe Penyesuaian | Ya |
| `checked` | [Pilih] | Opsional |
| `spaBranchName` | Cabang | Opsional |

## Sumber Data
- `/accurate/inventory/sellingprice-adjustment.do`
- `/accurate/cu`
- `/accurate/inventory/`
- `/accurate/inventory/detail-lookup-item.do`
- `/accurate/company/report-lookup-`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

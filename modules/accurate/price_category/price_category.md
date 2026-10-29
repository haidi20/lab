# Kategori Penjualan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nama Kategori | `name` | text | Ya | - |

### Info Lainnya
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Keterangan | `notes` | textarea | Tidak | - |

### Tombol Form
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
- Tidak ada filter dropdown yang terekstrak dari DOM.
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `description` | Keterangan | Ya |
| `name` | Nama Kategori | Ya |

## Sumber Data
- `/accurate/customer/price-category.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

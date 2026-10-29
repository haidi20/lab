# Kategori Pelanggan

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nama Kategori | `name` | text | Ya | - |
| Kategori Default | `isDefault` | checkbox | Tidak | - |
| Sub Kategori | `sub` | checkbox | Tidak | - |

### Tombol Form
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
- Tidak ada filter dropdown yang terekstrak dari DOM.
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `nameWithIndent` | Nama Kategori | Ya |
| `defaultCategory` | Kategori Default | Ya |
| `parentName` | Sub dari | Opsional |

## Sumber Data
- `/accurate/customer/customer-category.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

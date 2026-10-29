# SmartLink e-Commerce

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nama Toko | `ecommerceType`, `shopName` | select, text | Ya | ecommerceType: Silakan Pilih, Tokopedia (Lama), Shopee, Lazada, Blibli, Tiktok, Tokopedia |
| Penjualan atas Cabang | `branch` | lookup | Ya | - |
| Kas/Bank Saldo e-Commerce | `paymentBankAccount` | lookup | Tidak | - |
| Penjualan Kena PPN | `taxable` | checkbox | Tidak | - |
| Impor Penjualan Berstatus | `importDoneTransaction` | text | Tidak | - |
| Selesai | `importDoneTransaction` | text | Tidak | - |
| Semua Status | `importDoneTransaction` | text | Tidak | - |
| Ongkos Kirim e-Commerce | `importCourierCost` | checkbox | Tidak | - |
| Gudang Penjualan | `warehouse` | lookup | Ya | - |

### Tombol Form
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
| Field | Nilai Tampil |
| --- | --- |
| `ecommerceTypeFilter` — Nama e-Commerce | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `ecommerceType` | Nama e-Commerce | Ya |
| `shopName` | Nama Toko | Ya |

## Sumber Data
- `/accurate/customer/ecommerce-setting.do`
- `/accurate/company/`
- `/accurate/general-ledger/childwithtype-glaccount.do`
- `/accurate/inventory/lookup-`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

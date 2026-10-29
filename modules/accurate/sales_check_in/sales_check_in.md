# Check In

## Fitur
- Daftar dan navigasi modul
- Filter daftar
- Pencarian

## Form Data Baru
- Menu tidak menyediakan tombol Tambah pada bukti DOM.

## Daftar & Filter
| Field | Nilai Tampil |
| --- | --- |
| `transDateFilter` — Tanggal | Semua |
| `employeeFilter` — Sales | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `transDate` | Tanggal | Ya |
| `number` | Nomor # | Ya |
| `storeName` | Nama Pelanggan (Saat Check In) | Ya |
| `customer.name` | Pelanggan | Opsional |
| `branch.name` | Cabang | Opsional |
| `employee.name` | Sales | Ya |
| `firstTransactionNumber` | Transaksi | Ya |

## Sumber Data
- `/accurate/customer/sales-check-in.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

# Histori Bank

## Fitur
- Daftar dan navigasi modul

## Form Data Baru
- Menu tidak menyediakan tombol Tambah pada bukti DOM.

## Daftar & Filter
- Tidak ada filter dropdown yang terekstrak dari DOM.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `transDateView` | Tanggal | Ya |
| `transNumber` | No. Sumber # | Ya |
| `chequeNumber` | No Cek # | Ya |
| `transactionTypeName` | Tipe Transaksi | Ya |
| `description` | Keterangan | Ya |
| `amount` | Mutasi | Ya |
| `amountType` | Tipe | Ya |
| `balance` | Saldo | Ya |
| `reconciled` | # | Ya |

## Sumber Data
- `/accurate/cash-bank/bank-book.do`
- `/accurate/general-ledger/childwithtype-glaccount.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

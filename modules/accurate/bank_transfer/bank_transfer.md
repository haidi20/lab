# Transfer Bank

## Fitur
- Menu `#accurate__cash-bank__bank-transfer` dikelompokkan sebagai TRANSACTION.
- Modul mendukung transfer uang antar Kas/Bank dan pencatatan biaya transfer.
- Daftar, filter, pencarian, navigasi halaman, dan tombol tambah data teridentifikasi.

## Form Data Baru
### Transfer Uang
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Tanggal | `transDate` | date | Ya | Datepicker untuk tanggal transaksi. |
| Nomor # | `typeAutoNumber` | select | Ya | Dikontrol `isAutoNumber`; opsi mencakup Bank Deposito, Bank, Kas & Bank, Kas Kecil, Nomor Bukti, Kas/Bank Setara Kas, dan Transfer Bank Tunai. |
| Dari Kas/Bank | `fromBank` | lookup | Ya | Mencari akun dari `/accurate/general-ledger/childwithtype-glaccount.do` dengan tipe `CASH_BANK`. |
| Nilai Transfer | `fromBankAmount` | number | Ya | Nilai uang keluar dari Kas/Bank asal. |
| Ke Kas/Bank | `toBank` | lookup | Ya | Akun Kas/Bank tujuan transfer. |
| Akun Selisih | `differenceAccount` | lookup | Tidak | Label dinamis mengikuti `formData.differenceAmountDescription`. |

### Biaya Transfer
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Pencarian Akun | `searchDetailAccount` | lookup | Tidak | Pencarian akun untuk baris biaya transfer. |
| Akun | `account.no` | text | Ya | Kolom grid biaya transfer. |
| Nama Akun Dibebankan Ke | `expenseName` | text | Ya | Kolom grid biaya transfer. |
| Tipe | `bankChargeTypeName` | text | Ya | Kolom grid biaya transfer. |
| Nilai | `amount` | text | Ya | Kolom grid biaya transfer. |

### Info Lainnya
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Keterangan | `description` | textarea | Tidak | Catatan transaksi. |
| Cabang | teks statis | text | Tidak | Menampilkan cabang aktif, misalnya Kantor Pusat, dan tidak dapat diubah. |

### Tombol Form
- `Sebagai Draf`.
- `Simpan`.

## Daftar & Filter
### Filter
| Field | Input | Nilai Tampil |
| --- | --- | --- |
| Tanggal | filter periode | Semua |
| Dari Kas/Bank | lookup | Semua |
| Ke Kas/Bank | lookup | Semua |
| Cabang | lookup | Semua |
| Pembuat Data | lookup | Semua |

### Pencarian
- Kolom pencarian `keyword`.

### Tombol Toolbar
| Tombol | Aksi |
| --- | --- |
| Tambah | `btnAdd`, membuka form data baru. |
| Perbarui | `btnRefresh`, memuat ulang daftar. |
| Ekspor | `btnExport`. |
| Cetak | `btnPrint`. |
| Pengaturan | `btnColumnSetting`, pengaturan kolom. |

## Kolom Tabel
| Field | Kolom |
| --- | --- |
| `number` | Nomor # |
| `transDate` | Tanggal |
| `fromBank.name` | Bank (Keluar) |
| `fromBankAmount` | Nilai (Keluar) |
| `fromBankRate` | Kurs (Keluar) |
| `toBank.name` | Bank (Masuk) |
| `toBankAmount` | Nilai (Masuk) |
| `toBankRate` | Kurs (Masuk) |
| `description` | Keterangan |
| `attachmentExist` | Memiliki dokumen |
| `cashInAmount` | Total |
| `purchasePayment.number` | Pembayaran Pembelian |
| `branch.name` | Cabang |
| `toBranch.name` | Ke Cabang |
| `createdByUserName` | Pembuat Data |
| `cashOutAmount` | Total |

## Sumber Data
- `/accurate/cash-bank/bank-transfer.do`
- `init-bank-transfer.do`
- `/accurate/general-ledger/childwithtype-glaccount.do`

## Catatan Analisa
- Sesi REA berhasil terhubung ke Chrome debugging visible pada port `9223`.
- Modul dibuka langsung dari dashboard dan DOM modul tercapture lengkap.
- Tabel menampilkan `Belum ada data`, sehingga `data.json` berisi `record_count: 0`.
- Model JS CDN tetap mengembalikan HTTP 403 pada sebagian permintaan, namun tidak menghalangi analisa DOM.

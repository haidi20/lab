# Pembayaran

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Nomor # | `typeAutoNumber` | select | Ya | typeAutoNumber: Bank, Deposito Bank, Kas & Bank, Kas Kecil, Nomor Bukti Kas/Bank, Setara Kas, Tunai |
| Kas/Bank | `bank` | lookup | Ya | - |
| Tanggal | `transDate` | date | Ya | - |

### Detail
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Rincian Pembayaran | `searchDetailAccount` | lookup | Ya | - |

### Info Lainnya
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| No Cek # | `chequeNo` | text | Tidak | - |
| Penerima | `payee` | textarea | Tidak | - |
| Catatan | `description` | textarea | Tidak | - |

### Tombol Form
- `btnGetFrom` — Ambil Favorit.
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
| Field | Nilai Tampil |
| --- | --- |
| `transDateFilter` — Tanggal | Semua |
| `bankFilter` — Kas/Bank | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `number` | Nomor # | Ya |
| `transDate` | Tanggal | Ya |
| `bank.name` | Kas/Bank | Ya |
| `chequeNo` | No Cek # | Ya |
| `payee` | Penerima | Opsional |
| `description` | Keterangan | Ya |
| `amount` | Nilai | Ya |
| `rate` | Kurs | Opsional |
| `voidCheq` | Void | Opsional |
| `attachmentExist` | Memiliki dokumen | Opsional |
| `branch.name` | Cabang | Opsional |
| `chequeDate` | Tanggal Cek | Opsional |
| `pendingAmortized` | Pendapatan Tertunda | Opsional |
| `checked` | [Pilih] | Opsional |
| `createdByUserName` | Pembuat Data | Opsional |
| `printedByUser` | Dicetak/email | Opsional |
| `printedTime` | Waktu cetak/email | Opsional |

## Sumber Data
- `/accurate/cash-bank/other-payment.do`
- `/accurate/general-ledger/childwithtype-glaccount.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

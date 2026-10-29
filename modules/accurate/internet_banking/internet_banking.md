# SmartLink e-Banking

## Fitur
- Daftar dan navigasi modul
- Form tambah data
- Filter daftar
- Pencarian

## Form Data Baru
### Utama
| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Jenis Internet Banking | `internetBankingType` | select | Ya | internetBankingType: -- Pilih Internet Banking --, Accurate Online Format, Accurate Online Format JSON, KlikBCA Bisnis (API), KlikBCA Bisnis, KlikBCA Personal, KlikBCA Bisnis (SNAP API), KlikBCA Syariah, KlikBCA Syariah Bisnis, MyBCA Bisnis, BNI Internet Bisnis, BNI Cash Management System, BNI Direct Business, BRI Cash Management Bisnis, BRI IBBIZ (Internet Banking Bisnis), BRI Mobile (BRIMO), BRI IB (BRI Internet Banking), BSI (Bank Syariah Indonesia), Danamon, Mandiri Internet Bisnis, Mandiri Cash Management, Maybank Bisnis, OCBC Business, Permata Internet Bisnis, UOB Bisnis, UOB Infinity |
| No. Rekening Bank | `accountNumber` | text | Ya | - |
| Relasi Akun Bank | `cashBankGlAccount` | lookup | Ya | - |

### Tombol Form
- `btnSaveAsDraft` — Sebagai Draf.
- `btnSave` — Simpan.

## Daftar & Filter
| Field | Nilai Tampil |
| --- | --- |
| `internetBankingTypeFilter` — Jenis Internet Banking | Semua |
- Pencarian: `keyword`.

## Kolom Tabel
| Field | Kolom | Tampil |
| --- | --- | --- |
| `accountNumber` | No. Rekening Bank | Ya |
| `cashBankGlAccount.name` | Relasi Akun Bank | Ya |
| `internetBankingTypeName` | Jenis Internet Banking | Ya |

## Sumber Data
- `/accurate/cash-bank/internet-banking.do`
- `/accurate/general-ledger/childwithtype-glaccount.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Tabel terbaca dengan 0 baris data.

# Rekonsiliasi Bank

## Fitur
- Menu `#accurate__cash-bank__bank-reconcile` adalah alat workflow rekonsiliasi dua panel, bukan daftar data biasa.
- Panel kiri **REKENING BANK** menampilkan mutasi rekening koran; panel kanan **JURNAL ACCURATE** menampilkan jurnal Accurate.
- Pengguna memilih bank dan periode, klik Perbarui, lalu mencocokkan mutasi kedua panel.
- Tersedia aksi rekonsiliasi manual, hapus per mutasi, dan proses semua data cocok.
- Saldo bank aktif ditampilkan setelah refresh.

## Form Data Baru
- Tidak tersedia. Modul ini tidak memiliki form tambah data; rekening koran diimpor melalui menu Rekening Koran atau SmartLink e-Banking.

## Daftar & Filter
| Field | Input | Tipe | Keterangan |
| --- | --- | --- | --- |
| Bank | `bank` | lookup | Sumber `/accurate/general-ledger/childwithtype-glaccount.do`, tipe `CASH_BANK`. |
| Dari Tanggal | `startDate` | date | Datepicker awal periode. |
| S/d Tanggal | `endDate` | date | Datepicker akhir periode. |

### Pilihan Bank Tersedia
| Nama Akun | No. Akun |
| --- | --- |
| Kas Kecil | 110101 |
| Bank | 110102 |
| Tunai | 110103 |
| Deposito Bank | 110201 |

## Panel & Tombol Aksi
### Panel REKENING BANK
| Tombol | Nama | Aksi |
| --- | --- | --- |
| Pilih | `btnSelect` | Menandai mutasi terpilih pada panel rekening bank. |
| Pilih untuk hapus / Hapus per mutasi | `btnMultiDelete` | Menghapus mutasi rekening koran terpilih. |

### Panel JURNAL ACCURATE
| Tombol | Nama | Aksi |
| --- | --- | --- |
| Proses semua data cocok | `btnMultiReconcile` | Merekonsiliasi seluruh mutasi yang cocok antara kedua panel. |

### Tombol Umum
| Tombol | Nama | Aksi |
| --- | --- | --- |
| Perbarui | `btnRefresh` | Memuat ulang data kedua panel berdasarkan bank dan periode terpilih. |

## Kolom Tabel
- Kolom grid kedua panel dimuat secara dinamis hanya setelah bank dipilih, Perbarui diklik, dan terdapat transaksi pada periode tersebut.
- Pada sesi analisa, akun `Bank` (110102) dipilih dan Perbarui diklik, namun periode aktif tidak memiliki transaksi sehingga kedua panel kosong dan hanya menampilkan `Saldo Rp -`.
- Tidak ada definisi kolom statis pada DOM atau script modul.

## Dialog Konfirmasi
| Konteks | Teks Konfirmasi |
| --- | --- |
| Rekonsiliasi manual | Apakah histori ini ada tercetak dalam rekening koran? |
| Hapus rekening koran | Apakah anda ingin menghapus Rekening koran ini? |
| Hapus multi rekening koran | Apakah anda ingin menghapus … Rekening koran ini? |
| Peringatan penghapusan | Rekening koran yang dihapus hanya dapat dibuat kembali dengan mengimpor dari Internet Banking atau file download mutasi. |

## Sumber Data
- `/accurate/cash-bank/bank-reconcile.do`
- `/accurate/general-ledger/childwithtype-glaccount.do`

## Catatan Analisa
- Sesi REA pertama membuka modul dan mengklik tombol pencarian lookup bank; dropdown menampilkan 4 akun Kas/Bank.
- Sesi REA kedua memilih akun `Bank` (110102), mengklik `btnRefresh`, menunggu 10-15 detik, lalu menangkap DOM hasil refresh.
- Kedua panel terbuka dengan label `JURNAL ACCURATE` dan `REKENING BANK`, namun tidak memiliki baris maupun kolom karena tidak ada transaksi pada periode aktif.
- Tidak ada screenshot; seluruh bukti berasal dari DOM REA.

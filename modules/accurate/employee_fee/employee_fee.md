# Gaji/Tunjangan

**Module:** `#accurate__company__employee-fee`

## Fitur

- **Data Baru**: Membuat entri gaji/tunjangan baru
- **Cetak**: Mencetak daftar gaji/tunjangan
- **Unduh XLS**: Ekspor daftar ke format Excel
- **Unduh PDF**: Ekspor daftar ke format PDF

## Form Data Baru (Tambah Gaji/Tunjangan)

Wajib diisi: **Nama, Akun Beban**.

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Nama | name | text | Ya | |
| Tipe Gaji/Tunjangan | feeType | select | - | 14 opsi (lihat Dropdown Options) |
| Akun Beban | expenseAccount | lookup | Ya | Cari/Pilih Akun Perkiraan. Tampil untuk tipe tertentu saja |
| Non Aktif | suspended | checkbox | - | |

## Filter & Kolom Daftar

### Label

- Data Baru
- Non Aktif : Semua
- Tipe Gaji/Tunjangan : Semua
- Info Umum
- Nama
- Tipe Gaji/Tunjangan
- Bayar/Potong
- Bulanan
- Akun Beban
- Non Aktif
- Ya

### Input Fields

| Nama | Tipe | Placeholder |
|------|------|-------------|
| keyword | text | Ketik dan [Enter] |
| name | text |  |
| feeType | select |  |
| expenseAccount | text | Cari/Pilih Akun Perkiraan... |
| suspended | checkbox |  |

### Dropdown Options

**feeType:**

- Gaji/Pensiun atau THT/JHT
- Tunjangan PPh
- Subsidi PPh
- Tunjangan Lainnya, Uang lembur dan sebagainya
- Tunjangan Jaminan Kecelakaan Kerja, Jaminan Kematian
- Honorarium dan Imbalan lain sejenisnya
- Premi asuransi kesehatan yang dibayarkan pemberi kerja
- Penerimaan dalam bentuk natura dan kenikmatan lainnya
- Tantiem, Bonus, Rapel, Gratifikasi, Jasa Produksi dan THR
- Tunjangan Iuran Pensiun/THT/JHT dibayarkan Pemberi Kerja
- Potongan Gaji (Tidak Mengurangi PPh)
- Pengurangan Gaji (Mengurangi PPh)
- Premi asuransi kesehatan dibayarkan pekerja
- Iuran Pensiun/THT/JHT dibayarkan Pekerja


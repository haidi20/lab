# Syarat Pembayaran

**Module:** `#accurate__company__payment-term`

## Fitur

- **Data Baru**: Membuat entri syarat pembayaran baru
- **Cetak**: Mencetak daftar syarat pembayaran
- **Unduh XLS**: Ekspor daftar ke format Excel
- **Unduh PDF**: Ekspor daftar ke format PDF

## Form Data Baru (Tambah Syarat Pembayaran)

Tidak ada field wajib.

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Jika membayar antara | discDays | number | - | Hari |
| Akan mendapat diskon | discPC | number | - | Persen |
| Masa Jatuh Tempo | netDays | number | - | Hari |
| Keterangan | memo | textarea | - | |
| Default Syarat Pembayaran | isDefault | checkbox | - | |
| Non Aktif | suspended | checkbox | - | |

## Filter & Kolom Daftar

### Label

- Data Baru
- Non Aktif : Semua
- Nama
- Diskon (%)
- Masa Diskon (hari)
- Masa Jatuh Tempo (hari)
- Keterangan
- Non Aktif
- Default
- Info Umum
- Jika membayar antara
- Hari
- Akan mendapat diskon
- Masa Jatuh Tempo
- Default Syarat Pembayaran
- Ya

### Input Fields

| Nama | Tipe | Placeholder |
|------|------|-------------|
| searchFilter | text | Cari/Pilih... |
| selectedColumn | checkbox |  |
| keyword | text | Ketik dan [Enter] |
| discDays | text |  |
| discPC | text |  |
| netDays | text |  |
| memo | textarea |  |
| isDefault | checkbox |  |
| suspended | checkbox |  |


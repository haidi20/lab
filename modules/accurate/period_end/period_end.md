# Proses Akhir Bulan

**Module:** `#accurate__company__period-end`

## Fitur

- **Data Baru**: Membuat entri proses akhir bulan baru
- **Cetak**: Mencetak daftar proses akhir bulan
- **Unduh XLS**: Ekspor daftar ke format Excel
- **Unduh PDF**: Ekspor daftar ke format PDF

## Form Data Baru (Tambah Proses Akhir Bulan)

Form ini dibuka dari tombol **Tambah** (`btnAdd`) pada daftar Proses Akhir Bulan.

### Info Utama

| Field | Input | Tipe | Wajib | Keterangan |
| --- | --- | --- | --- | --- |
| Bulan | `monthPE` | select | Ya | Wajib memilih salah satu bulan; placeholder/nilai awal `[Pilih Bulan]`. |
| Tahun | `yearPE` | select | Tidak | Opsi tahun tersedia sesuai data konfigurasi periode. |

### Tab

| Tab | Isi | Keterangan |
| --- | --- | --- |
| Nilai Tukar Mata Uang | SlickGrid nilai tukar | Kolom: **Nama Mata Uang** dan **Nilai Tukar**. Baris dapat dibuka/diatur; capture menampilkan `Indonesian Rupiah = 1`. |
| Catatan | `description` | Textarea, maksimal 5.000 karakter. |

## Filter & Kolom Daftar

### Label

- Data Baru
- Bulan : Semua
- Tahun : Semua
- Nama
- Tanggal Input
- Keterangan
- Memiliki dokumen
- Bulan
- Tahun

### Input Fields

| Nama | Tipe | Placeholder |
|------|------|-------------|
| searchFilter | text | Cari/Pilih... |
| selectedColumn | checkbox |  |
| keyword | text | Ketik dan [Enter] |
| monthPE | select |  |
| yearPE | select |  |
| description | textarea |  |

### Dropdown Options

**monthPE:**

- [Pilih Bulan]
- Januari
- Februari
- Maret
- April
- Mei
- Juni
- Juli
- Agustus
- September
- Oktober
- November
- Desember

**yearPE:**

- 2027
- 2026


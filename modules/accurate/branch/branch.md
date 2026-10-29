# Cabang

**Module:** `#accurate__company__branch`

## Fitur

- **Data Baru**: Membuat entri cabang baru
- **Cetak**: Mencetak daftar cabang
- **Unduh XLS**: Ekspor daftar ke format Excel
- **Unduh PDF**: Ekspor daftar ke format PDF

## Form Data Baru (Tambah Cabang)

Wajib diisi: **Nama**.

### Info Umum

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Nama | name | text | Ya | |
| No. Telepon | phoneNumber | text | - | |
| Non Aktif | suspended | checkbox | - | |

### Info Lainnya

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Alamat | street + city + zipCode + province + country | textarea + 4x text | - | Jalan, Kota, K.Pos, Provinsi, Negara |

## Filter & Kolom Daftar

### Label

- Data Baru
- Non Aktif : Semua
- Info Umum
- Nama
- No. Telepon
- Non Aktif
- Ya
- Info Lainnya
- Alamat
- Akses Pengguna
- Semua Pengguna

### Input Fields

| Nama | Tipe | Placeholder |
|------|------|-------------|
| keyword | text | Ketik dan [Enter] |
| name | text |  |
| phoneNumber | text |  |
| suspended | checkbox |  |
| street | textarea |  |
| city | text |  |
| zipCode | text |  |
| province | text |  |
| country | text |  |
| usedAllUser | checkbox |  |


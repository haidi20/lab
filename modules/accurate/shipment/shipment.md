# Pengiriman

**Module:** `#accurate__company__shipment`

## Fitur

- **Data Baru**: Membuat entri pengiriman baru
- **Cetak**: Mencetak daftar pengiriman
- **Unduh XLS**: Ekspor daftar ke format Excel
- **Unduh PDF**: Ekspor daftar ke format PDF

## Form Data Baru (Tambah Pengiriman)

Wajib diisi: **Nama**.

### Info Umum

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Nama | name | text | Ya | |
| PIC | picName | text | - | |
| No. Telp | picPhoneNumber | text | - | |
| Non Aktif | suspended | checkbox | - | |

### Info Lainnya

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Alamat Pengiriman | shipAddressStreet + shipAddressCity + shipAddressZipCode + shipAddressProvince + shipAddressCountry | textarea + 4x text | - | Jalan, Kota, K.Pos, Provinsi, Negara |

## Filter & Kolom Daftar

### Label

- Data Baru
- Non Aktif : Semua
- Info Umum
- Nama
- PIC
- No. Telp
- Non Aktif
- Ya
- Info Lainnya
- Alamat Pengiriman

### Input Fields

| Nama | Tipe | Placeholder |
|------|------|-------------|
| keyword | text | Ketik dan [Enter] |
| name | text |  |
| picName | text |  |
| picPhoneNumber | text | ________________ |
| suspended | checkbox |  |
| shipAddressStreet | textarea |  |
| shipAddressCity | text |  |
| shipAddressZipCode | text |  |
| shipAddressProvince | text |  |
| shipAddressCountry | text |  |


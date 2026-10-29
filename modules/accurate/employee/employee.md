# Karyawan

**Module:** `#accurate__company__employee`

## Fitur

- **Data Baru**: Membuat entri karyawan baru
- **Cetak**: Mencetak daftar karyawan
- **Unduh XLS**: Ekspor daftar ke format Excel
- **Unduh PDF**: Ekspor daftar ke format PDF

## Form Data Baru (Tambah Karyawan)

Form tambah karyawan terbagi menjadi 4 tab. Hanya **Nama Lengkap** yang wajib diisi.

### Tab Info Umum — Data Pribadi

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Sapaan | salutation | select | - | Bapak, Ibu |
| Nama Lengkap | name | text | Ya | |
| No. KTP | nikNo | text | - | |
| Email | email | text | - | |
| Handphone | mobilePhone | text | - | |
| No. Telp. Bisnis | workPhone | text | - | |
| No. Telp. Rumah | homePhone | text | - | |
| No. WhatsApp | bbmPin | text | - | Nama input internal: bbmPin |
| Website | website | text | - | |
| Kewarganegaraan | domisiliType | select | - | 63 opsi negara (lihat Dropdown Options) |

### Tab Info Umum — Data Karyawan

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| ID Karyawan | btnManualNumber + typeAutoNumber | checkbox + select | - | Centang untuk isi manual; select: Karyawan (penomoran otomatis) |
| Posisi Jabatan | position | text | - | |
| Tgl Masuk | joinDate | date | - | Datepicker |
| Cabang | branch | select | - | Kantor Pusat |
| Departemen | department | lookup | - | Cari/Pilih dari daftar departemen |
| Penjual | salesman | checkbox | - | |
| Catatan | notes | textarea | - | |
| Non Aktif | suspended | checkbox | - | |

### Tab Info Alamat

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Alamat (Jalan) | street | textarea | - | |
| Kota | city | text | - | |
| K.Pos | zipCode | text | - | |
| Provinsi | province | text | - | |
| Negara | country | text | - | |

### Tab Pajak Penghasilan

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Dikenakan PPh 21 | pph | checkbox | - | |
| No. NPWP | npwpNo | text | - | Format mask NPWP |
| Status Pekerja | employeeWorkStatus | select | - | 9 opsi (lihat Dropdown Options) |
| Status PTKP | employeeTaxStatus | select | - | 8 opsi K/TK + tanggungan |

### Tab Pajak Penghasilan — Perhitungan PPh

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| PPh mulai dihitung (Bulan) | startMonthPayment | select | - | Januari-Desember |
| PPh mulai dihitung (Tahun) | startYearPayment | select | - | 2021-2027 |
| Penghasilan Sebelumnya | nettoIncomeBefore | number | - | |
| PPh Sebelumnya | pphBefore | number | - | |

### Tab Info Akun

| Field | Input | Tipe | Wajib | Keterangan |
|-------|-------|------|-------|------------|
| Nama Bank | bank | lookup | - | Cari/Pilih bank |
| No Rekening | bankAccount | text | - | Mask 16 digit |
| Atas Nama Rekening | bankAccountName | text | - | |

## Filter & Kolom Daftar

### Label

- Data Baru
- Non Aktif : Semua
- Status Pekerja : Semua
- Penjual : Semua
- Cabang
- Nama
- Posisi Jabatan
- Email
- Handphone
- Tgl Masuk
- Dikenakan PTKP
- No. KTP
- Non Aktif
- Rekening Gaji
- Atas Nama Rekening
- Nama Bank
- No. NPWP
- Memiliki dokumen
- Penjual
- ID Karyawan
- No. Telp. Bisnis
- No. Telp. Rumah
- Status PTKP
- Status Pekerja
- Utang
- Login Penjual
- Data Pribadi
- Nama Lengkap
- No. WhatsApp
- Website
- Kewarganegaraan
- Data Karyawan
- Departemen
- Ya
- Catatan
- Rp 0
- Info Alamat
- Alamat
- Pajak Penghasilan
- Dikenakan PPh 21
- Perhitungan PPh
- PPh mulai dihitung
- Penghasilan Sebelumnya
- PPh Sebelumnya
- Info Akun
- No Rekening
- s/d

### Input Fields

| Nama | Tipe | Placeholder |
|------|------|-------------|
| searchFilter | text | Cari/Pilih... |
| selectedColumn | checkbox |  |
| keyword | text | Ketik dan [Enter] |
| salutation | select |  |
| name | text |  |
| nikNo | text |  |
| email | text |  |
| mobilePhone | text |  |
| workPhone | text |  |
| homePhone | text |  |
| bbmPin | text |  |
| website | text |  |
| domisiliType | select |  |
| btnManualNumber--24--0 | checkbox |  |
| typeAutoNumber | select |  |
| position | text |  |
| joinDate | text |  |
| branch | select |  |
| department | text | Cari/Pilih... |
| salesman | checkbox |  |
| notes | text |  |
| suspended | checkbox |  |
| street | textarea |  |
| city | text |  |
| zipCode | text |  |
| province | text |  |
| country | text |  |
| pph | checkbox |  |
| npwpNo | text | ________________ |
| employeeWorkStatus | select |  |
| employeeTaxStatus | select |  |
| startMonthPayment | select |  |
| startYearPayment | select |  |
| nettoIncomeBefore | text |  |
| pphBefore | text |  |
| bank | text | Cari/Pilih... |
| bankAccount | text |  |
| bankAccountName | text |  |
| fromDate | text |  |
| toDate | text |  |

### Dropdown Options

**salutation:**

- - Sapaan -
- Bapak
- Ibu

**domisiliType:**

- Afrika Selatan
- Aljazair
- Amerika Serikat
- Australia
- Austria
- Bangladesh
- Belanda
- Belgia
- Brunei Darussalam
- Bulgaria
- China
- Denmark
- Finlandia
- Hong Kong
- Hungaria
- India
- Indonesia
- Inggris
- Iran
- Italia
- Jepang
- Jerman
- Kanada
- Korea Selatan
- Korea Utara
- Kuwait
- Luxembourg
- Malaysia
- Maroko
- Mesir
- Mongolia
- Norwegia
- Pakistan
- Perancis
- Philipina
- Polandia
- Portugal
- Qatar
- Republik Ceko
- Romania
- Rusia
- Saudi Arabia
- Selandia Baru
- Seychelles
- Singapura
- Slovakia
- Spanyol
- Sri Lanka
- Sudan
- Suriah
- Swedia
- Swiss
- Taiwan
- Thailand
- Tunisia
- Turki
- Ukraina
- Uni Emirat Arab
- Uzbekistan
- Venezuela
- Vietnam
- Yordania
- Timor Leste

**typeAutoNumber:**

- Karyawan

**branch:**

- [Semua Cabang]
- Kantor Pusat

**employeeWorkStatus:**

- Pegawai Tetap
- Pegawai Tidak Tetap
- Bukan Pegawai - Distributor MLM
- Bukan Pegawai - Petugas Dinas Luar Asuransi
- Bukan Pegawai -  Penjaja Barang Dagangan
- Bukan Pegawai -  Tenaga Ahli
- Anggota Dewan Komisaris atau dewan pengawas
- Bukan Pegawai yang menerima imbalan yang bersifat berkesinambungan
- Bukan Pegawai yang menerima imbalan yang tidak bersifat berkesinambungan

**employeeTaxStatus:**

- Tidak Kawin (Tidak ada tanggungan)
- Tidak Kawin (1 Tanggungan)
- Tidak Kawin (2 Tanggungan)
- Tidak Kawin (3 Tanggungan)
- Kawin (Tidak ada tanggungan)
- Kawin (1 Tanggungan)
- Kawin (2 Tanggungan)
- Kawin (3 Tanggungan)

**startMonthPayment:**

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

**startYearPayment:**

- 2021
- 2022
- 2023
- 2024
- 2025
- 2026
- 2027


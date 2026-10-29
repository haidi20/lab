# SmartLink Virtual Account

## Fitur
- Menu `#accurate__company__application-virtual-account` membuka Accurate Store kategori e-Banking.
- Konten utama berupa katalog aplikasi add-on, bukan tabel data perusahaan.
- Navigasi Accurate Store: Katalog, Aplikasi Saya, dan API Token.
- Pencarian aplikasi tersedia pada field `keywords`.
- Kategori e-Banking menampilkan: SmartLink BCA, SmartLink Mandiri, dan SmartLink UOB.
- Setiap aplikasi memiliki tombol/link `Lihat »` menuju halaman detail `application-view.do`.

## Form Data Baru
- Tidak tersedia. Modul ini adalah katalog Accurate Store, bukan form input data transaksi/master.

## Daftar & Filter
### Navigasi
| Menu | Endpoint |
| --- | --- |
| Katalog | `/marketplace/user/index.do` |
| Aplikasi Saya | `/marketplace/user/application-installed.do` |
| API Token | `/marketplace/user/application-api-token.do` |

### Filter Kategori
- Filter kategori tersedia pada parameter `category`, nilai aktif: `EBANKING`.
- Pencarian aplikasi menggunakan field `keywords`.

### Aplikasi Tampil
| Aplikasi | appKey |
| --- | --- |
| SmartLink BCA | `BCA_SMARTLINK_APPLICATION` |
| SmartLink Mandiri | `MANDIRI_SMARTLINK_APPLICATION` |
| SmartLink UOB | `UOB_SMARTLINK_APPLICATION` |

## Kolom Tabel
- Tidak ada tabel data pada halaman induk maupun iframe Accurate Store.

## Sumber Data
- `/accurate/company/application-virtual-account.do`
- `https://account.accurate.id/marketplace/user/index.do?category=EBANKING`
- `/marketplace/user/application-view.do`

## Catatan Analisa
- Capture REA selesai tanpa langkah gagal.
- Konten iframe Accurate Store dibuka langsung melalui URL iframe dan DOM-nya tercapture lengkap.
- Tidak ada tabel/grid data, sehingga `data.json` berisi `record_count: 0`.

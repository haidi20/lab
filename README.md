# random

Contoh Python untuk memberi akses WiFi Hotspot setelah pembayaran melalui RouterOS API.

Setiap pembayaran menghasilkan username baru dan password acak. Satu `payment_id`
hanya bisa dipakai satu kali, dan akses default berlaku 24 jam.

## Menjalankan

```bash
python main.py
```

## Mode simulator/mock

Tanpa perangkat:

```bash
python main.py
```

## Mode Mikrotik asli

Gunakan RouterOS v7 dengan REST API aktif. Salin `.env.example` menjadi `.env`,
lalu isi credential di `.env`:

```powershell
Copy-Item .env.example .env
python main.py
```

`main.py` otomatis membaca `.env`, tetapi environment variable yang sudah ada
tidak ditimpa. Untuk sertifikat self-signed di lab, set:

```bash
set MIKROTIK_VERIFY_TLS=false
```

## Integrasi pembayaran

Setelah payment gateway memanggil webhook kamu, panggil:

```python
from modules.payment_wifi_access import PaymentConfirmation, RouterOSRestAdapter, WifiAccessService

service = WifiAccessService(adapter, paid_payments)
access = service.grant_access_after_payment(
    PaymentConfirmation(
        payment_id=data['payment_id'],
        invoice_id=data['invoice_id'],
        duration_hours=24,
    )
)
print(access.username, access.password)
```

`paid_payments` sebaiknya disimpan di database, bukan di memori, untuk production.

## Simulator Mikrotik

Mikrotik CHR dapat dipakai sebagai RouterOS virtual di VirtualBox, VMware, Proxmox, atau cloud. Kode tidak perlu dirombak; cukup ubah host, user, password, dan profil Hotspot. CHR gratis untuk testing dengan batas kecepatan 1 Mbps per interface.

### Uji CHR + login WiFi

CHR tidak punya radio WiFi, jadi CHR tidak memancarkan SSID. Untuk login dari perangkat WiFi nyata, gunakan CHR sebagai hotspot/gateway dan gunakan WiFi router/AP yang sudah ada.

Topologi lab sederhana:

```text
Phone/laptop -- WiFi router/AP -- CHR virtual -- Internet
```

Contoh konfigurasi CHR sekali saja:

```routeros
/ip address add address=192.168.1.10/24 interface=ether1
/ip route add dst-address=0.0.0.0/0 gateway=192.168.1.1
/ip dns set servers=1.1.1.1,8.8.8.8 allow-remote-requests=yes
/ip firewall nat add chain=srcnat action=masquerade out-interface=ether1

/certificate add name=rest-cert common-name=chr
/certificate sign rest-cert
/ip service set www-ssl certificate=rest-cert disabled=no

/ip hotspot setup
```

Jalankan `/ip hotspot setup` pada interface `ether1`, gunakan network `192.168.1.0/24` dan gateway `192.168.1.10`. Hindari mengaktifkan DHCP CHR jika router utama sudah DHCP agar tidak konflik.

Pada perangkat WiFi, pakai IP statis:

- IP: `192.168.1.50`
- Netmask: `255.255.255.0`
- Gateway: `192.168.1.10`
- DNS: `192.168.1.10`

Lalu isi `.env`:

```env
MIKROTIK_HOST=192.168.1.10
MIKROTIK_USER=admin
MIKROTIK_PASSWORD=secret
MIKROTIK_VERIFY_TLS=false
```

Jalankan:

```bash
python main.py
```

Gunakan `username` dan `password` dari output `Mode RouterOS`, lalu buka `http://192.168.1.10/login` di perangkat WiFi. Setelah login, coba akses internet. Scheduler akan menghapus user setelah 24 jam.

## Halaman login custom

Modul `modules/payment_wifi_access` menyediakan tampilan login sendiri, bukan tampilan bawaan Mikrotik. Halaman ini tetap mengirim `username` dan `password` ke endpoint login Hotspot Mikrotik, sehingga sesi tetap dikelola router.

Contoh:

```python
from modules.payment_wifi_access import render_login_page

html = render_login_page(
    login_url='http://192.168.1.10/login',
    next_url='https://example.com/berhasil',
    error_message=None,
    brand_name='WiFi Kafe',
    support_message='Butuh bantuan? Hubungi kasir.',
)
```

### Supaya custom login bisa diakses customer

Cara paling sederhana adalah meng-host halaman ini langsung di Hotspot Mikrotik.

1. Generate file router-ready:

```bash
python -m modules.payment_wifi_access.build --output public/login.html --brand 'WiFi Access'
```

2. Upload `public/login.html` ke folder Hotspot di Mikrotik, lalu gunakan sebagai `login.html`. Di CHR biasanya foldernya `/hotspot/`.
3. Set Hotspot profile agar menerima login PAP dari form custom:

```routeros
/ip hotspot profile set [find] login-by=http-pap
```

4. Pastikan Hotspot server aktif:

```routeros
/ip hotspot print
/ip hotspot enable [find disabled=yes]
```

5. Customer connect ke WiFi publik, buka browser, lalu captive portal akan menampilkan `login.html` custom tersebut.
6. Customer memasukkan username/password dari hasil pembayaran. Mikrotik memvalidasi kredensial dan membuka akses internet.

Jika memakai web portal terpisah, daftarkan domain/IP portal di Hotspot Walled Garden agar bisa dibuka sebelum login:

```routeros
/ip hotspot walled-garden ip add action=accept disabled=no dst-host=portal.example.com
/ip hotspot walled-garden add action=accept disabled=no dst-host=portal.example.com
```

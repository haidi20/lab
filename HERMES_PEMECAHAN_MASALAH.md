# Pemecahan Masalah Hermes

Dokumen ini merangkum permasalahan yang terjadi saat mengintegrasikan Hermes
sebagai worker Trello dan asisten bot Telegram, beserta solusi yang diterapkan
agar generasi berikutnya tidak mengulang debugging yang sama.

## Konteks

- Hermes Agent berjalan di laptop Windows sebagai gateway sekaligus cron worker.
- Cron worker mengerjakan todo Trello board Inventory di workspace
  `D:\projects\klinik-git`.
- Bot Telegram di repo ini (`modules/telegram_store`) memantau status Hermes,
  menampilkan monitoring live, dan menyediakan mode chat `Hubungi Hermes`.

## Daftar Permasalahan dan Solusi

### 1. Jendela CMD kosong muncul sesaat setiap menit

Permasalahan: setiap menit muncul jendela CMD kosong yang langsung tertutup.

Penyebab: Scheduled Task `Hermes Cron Tick` menjalankan
`cmd.exe /c hermes.cmd cron tick` di session user, sehingga console-nya tampil.

Solusi:

- Membuat wrapper tersembunyi `Hermes_Cron_Tick.vbs` yang memanggil tick dengan
  window style hidden.
- Mengganti action task menjadi `wscript.exe` (GUI host, tanpa console).
- Untuk pemanggilan Hermes dari bot, `cli.py` memakai flag
  `CREATE_NO_WINDOW`, dan default binary memakai wrapper
  `modules/telegram_store/bin/hermes-hidden.cmd` yang memanggil Node Hermes
  langsung tanpa npm `.cmd`.

### 2. Chat Hermes tidak punya akses tool

Permasalahan: saat dihubungi lewat bot, Hermes menjawab tidak bisa membaca
`AGENTS.md`, menjalankan command, atau mengakses Trello.

Penyebab: gateway berjalan di Windows session 0 lewat Scheduled Task elevated,
sedangkan bot berjalan di session user. Kondisi ini memicu error
`gateway_other_session`, lalu bot jatuh ke fallback provider biasa yang hanya
model teks tanpa tool.

Solusi:

- Task `Hermes Agent Gateway` (session 0) dinonaktifkan.
- Gateway dijalankan ulang di session user lewat startup VBS tersembunyi.
- Fallback provider hanya dipakai untuk error `gateway_other_session`.

### 3. Gateway tidak bisa dihentikan dari session biasa

Permasalahan: `hermes gateway stop --yes` dan `Stop-Process` gagal dengan
Access denied karena proses session 0 berjalan dengan token elevated.

Solusi:

- Task session 0 di-disable lewat `schtasks /Change /TN ... /DISABLE`.
- Gateway digantikan proses session user yang bisa dikendalikan penuh.
- Restart di kemudian hari cukup dengan `hermes gateway restart --yes`.

### 4. Job cron paused dan run hantu `Fire claim lost`

Permasalahan: setelah gateway mati terpaksa, job otomatis di-pause dan log
banjir `No jobs due`. Setelah resume, setiap menit muncul run baru yang gagal
dengan `Fire claim lost; execution was not started`.

Penyebab: occurrence lama terus di-restore sebagai catch-up, dan dua ticker
(ticker internal gateway plus task `Hermes Cron Tick`) berebut claim job sama.

Solusi:

- `hermes cron resume` untuk mengaktifkan kembali job.
- Task `Hermes Cron Tick` di-disable karena gateway sudah punya ticker internal
  60 detik.
- Pause lalu resume sekali untuk me-re-anchor jadwal.
- Run hantu berhenti setelah ticker ganda dihilangkan.

### 5. Chat timeout terlalu pendek

Permasalahan: tugas Hermes yang berat terpotong pada 180 detik.

Solusi: default `HERMES_CHAT_TIMEOUT_SECONDS` menjadi 900, termasuk untuk
request fallback provider. Nilai bisa dioverride lewat `.env`.

### 6. Salah Python saat menjalankan gateway manual

Permasalahan: `python -m hermes_cli.main gateway run` gagal dengan
`ModuleNotFoundError` saat memakai Python Laragon atau Python tools Hermes.

Solusi: gunakan venv install Hermes:

```powershell
C:\Users\nhaid\AppData\Local\hermes\installs\3d67dd8fb9241f53\environments\6a6c1674c4534aba9bfff232fc512c6a\venv\Scripts\python.exe -m hermes_cli.main gateway run
```

### 7. Output Unicode gagal dicetak di console

Permasalahan: jawaban Hermes berisi karakter seperti panah, console cp1252
melempar `UnicodeEncodeError`.

Solusi: cetak lewat `sys.stdout.buffer.write(answer.encode('utf-8'))`, bukan
`print` langsung.

### 8. Model alias membuat eksekusi lambat

Permasalahan: model `cd` adalah alias combo; latency API call sering 4 sampai
172 detik sehingga fase analisa terasa menggantung.

Solusi: arahkan langsung ke model Z.ai GLM 5.2:

- Cron job: `hermes cron edit 442bba7081d8 --model cd/z-ai/glm-5.2`.
- Default global: `hermes config set model cd/z-ai/glm-5.2`.
- Fallback bot: `HERMES_PROVIDER_MODEL=cd/z-ai/glm-5.2` di `.env`.

### 9. Worker berhenti di analisa setelah kartu masuk Review

Permasalahan: setelah commit dan push, kartu dipindahkan ke Review, tetapi
Hermes kadang masuk fase eksplorasi panjang lagi atau berhenti sebelum mengambil
kartu berikutnya. Akibatnya remote terlihat berhenti meskipun kartu lama sudah
selesai.

Penyebab: instruksi lama menyebut kartu berikutnya harus dikerjakan, tetapi tidak
menjadi checkpoint tegas setelah aksi Review. Model bisa menafsirkan push dan
Review sebagai akhir siklus, lalu memulai analisa baru tanpa jejak patch.

Solusi:

- Prompt cron diubah menjadi loop tegas dengan batas maksimal 3 kartu per run.
- Setelah kartu masuk Review, tool call berikutnya wajib membaca Progress/Trello
  atau mengambil kartu berikutnya; final answer sebelum itu dilarang.
- Eksplorasi maksimal 5 langkah per kartu, setelah itu patch wajib dimulai.
- Reasoning effort cron diturunkan dari medium ke low agar fase berpikir tidak
  mendominasi waktu eksekusi.

### 10. Proses Hermes hidup tetapi tidak ada progress

Permasalahan: cron dan gateway masih terlihat running, tetapi worker hanya
melakukan API call atau terminal eksplorasi tanpa patch, commit, atau perubahan
Trello.

Solusi:

- Modul `modules.hermes_watchdog` memeriksa log Hermes dan status git.
- Progress sah adalah event `tool patch`, `tool write_file`, atau perubahan
  fingerprint `git status`.
- Jika tidak ada progress selama 15 menit, watchdog mengirim notifikasi.
- Jika stale berulang, watchdog menjalankan `hermes gateway restart --yes`.
- Scheduled Task `Hermes Watchdog` menjalankan mode `--once` tiap 5 menit
  secara hidden dengan kebijakan `IgnoreNew`.
- Watchdog juga membersihkan session cron Hermes yang sudah ended dengan
  `hermes sessions prune --older-than 1d --yes`.
- Prune hanya berjalan maksimal sekali per 6 jam melalui state
  `last_prune_at`, sehingga tidak menambah beban pada setiap siklus.
- Interval dan umur session dapat diubah lewat
  `HERMES_WATCHDOG_PRUNE_INTERVAL_MINUTES` dan
  `HERMES_WATCHDOG_PRUNE_OLDER_THAN`.
- Perintah Hermes di-resolve dengan `shutil.which` sebelum dieksekusi karena
  Windows menjumpai `hermes.CMD`; tanpa resolver, `subprocess.run` bisa gagal
  dengan `FileNotFoundError`.
- Notifikasi Telegram aktif setelah `.env` berisi
  `HERMES_WATCHDOG_TELEGRAM_CHAT_ID`.

## Konfigurasi Final

- Gateway: satu proses di session user, hidden, auto-start lewat VBS Startup.
- Cron worker: aktif, interval 1 menit, continuity on, max_turns 250,
  reasoning low, model `cd/z-ai/glm-5.2`.
- Task Windows: `Hermes Agent Gateway` dan `Hermes Cron Tick` keduanya
  disabled; penggantinya startup VBS plus ticker internal gateway.
- Bot Telegram: menu Status Hermes, monitoring live 1 menit, mode
  `Hubungi Hermes` dengan akses penuh dan wajib baca `AGENTS.md` lebih dulu.

## Perintah Operasional

```powershell
hermes gateway status
hermes gateway restart --yes
hermes cron list
hermes cron resume 442bba7081d8
hermes cron runs 442bba7081d8
D:\learns\random\hermes-log.bat
python -m modules.hermes_watchdog --once
Get-ScheduledTask -TaskName 'Hermes Watchdog'
```

## Pelajaran Penting

- Jangan restart gateway saat ada run aktif kecuali memang perlu; continuity
  membuat run berikutnya melanjutkan pekerjaan, tetapi run aktif tetap terputus.
- Perubahan code Hermes berada di working tree sebelum commit; GitHub baru
  berubah setelah push, jadi jangan menganggap Hermes diam hanya karena
  remote belum berubah.
- Fallback provider tanpa tool tidak boleh dipakai untuk mengerjakan todo;
  ia hanya jawaban teks darurat.

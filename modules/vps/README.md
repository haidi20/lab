# modules/vps

Provisioning & deployment toolkit untuk replika VPS haidinata.my.id
(Ubuntu 24.04, nginx, Bun + Hono BE, PHP-FPM, Certbot, UFW).

## CLI

    python -m modules.vps audit    # snapshot kondisi VPS
    python -m modules.vps setup    # bootstrap penuh: packages, bun, repo, nginx, systemd, ufw, certbot, cicd
    python -m modules.vps setup --skip-certs --skip-clone
    python -m modules.vps deploy --local-dist D:/learns/haidi20/dist
    python -m modules.vps deploy --sites portfolio karta klinik
    python -m modules.vps health   # cek nginx, haidi20-be, HTTP 200

Deploy multi-site memakai git clone/pull langsung dari GitHub di VPS
(bukan upload dari lokal). Tidak ada file aplikasi yang dikirim dari laptop.

Repo yang di-pull saat `setup`:

- `haidi20/haidi20` -> `/var/www/portfolio` (portfolio, `fe/dist` langsung jadi webroot)
- `utamaweb/karta_spa` -> `/var/www/karta` (branch `main`)
- `haidi20/klinik` -> `/var/www/klinik` (branch `haidi`, app di `src/`)
- `haidi20/lab` -> `/var/www/ci-monitor-repo` (halaman `ci.haidinata.my.id`)

Repo karta dan klinik private, jadi butuh `GITHUB_TOKEN` (PAT dengan scope
`repo`). Setup menulis `/root/.git-credentials` (mode 600) dan
`KARTA_GIT_TOKEN` di `/etc/environment` (dipakai halaman ci-monitor). Tanpa
token, repo public tetap bisa di-pull tapi karta/klinik akan gagal.

`setup` juga menyiapkan Laravel otomatis: database + user MySQL, `.env`
production (APP_URL, DB, redis, reverb/JWT untuk klinik), `key:generate`,
`composer install`, `npm ci` + build asset, `migrate --force`, permission
`www-data`, supervisor (worker/reverb/pulse), cron scheduler, lalu certbot
untuk semua subdomain.

`python -m modules.vps setup` memerlukan `GITHUB_TOKEN` di environment
(atau `.env`) untuk private repo.
Portfolio (bun build), karta dan klinik (composer + artisan) otomatis
sesuai tipe project. CI/CD workflow deploy.yml di-generate untuk semua
project: haidi20 (main), karta (main), klinik (haidi).

Kredensial dibaca dari .env: VPS_HOST, VPS_PORT, VPS_USER,
VPS_PASSWORD, VPS_SSH_KEY, VPS_DEPLOY_ROOT. Tidak ada password default di
source: VPS_PASSWORD wajib diisi, kalau kosong skrip gagal cepat
(`RuntimeError`) sebelum membuka koneksi.

`modules/vps/vps_run.py` adalah helper SSH manual dan aturan yang sama
berlaku (env-only).

Integration test `tests/test_integration.py::test_04_repo_dirs_exist`
memakai `expected_repo_dirs()` dari `config.py`. Default-nya
`DEFAULT_REPO_DIRS` (`monitoring-ph-air`, sesuai isi `/var/www` saat ini);
override lewat `VPS_EXPECTED_REPO_DIRS=haidi,karta,skripsi` bila server
dipulihkan ke layout lama.

## Struktur

- config.py - dataclass VPSConfig + loader .env
- ssh.py - SSHRunner (paramiko): run, read/write file, upload tree
- templates.py - nginx sites & systemd unit, sama persis dengan server berjalan
- setup.py - VPSSetupper, langkah idempoten
- audit.py / health.py - snapshot & health check
- deploy.py - upload folder dist + reload nginx
- tests/ - unit test dengan FakeSSHRunner (tanpa jaringan)

## Test

    python -m unittest modules.vps.tests.test_vps_setup modules.vps.tests.test_vps_tools

# PLAN

## Task: Semua subdomain live di VPS UC (172.232.96.174), deploy pull dari GitHub

Target subdomain: haidinata.my.id (+www), be., ci., karta., inventory., skripsi.

Sumber deploy = git clone/pull dari GitHub (tanpa upload file lokal).
Repo: haidi20/haidi20 (portfolio), utamaweb/karta_spa (private), haidi20/klinik
(private), haidi20/lab (ci-monitor), haidi20/monitoring-ph-air (sudah live).

- [x] 1. Tulis PLAN.md
- [x] 2. TDD: test setup.py (kredensial git, clone 4 repo, laravel env/DB, ci-monitor dari repo, urutan run)
- [x] 3. Implementasi config.py (ci repo, branch, github token, db name) + templates nginx
- [x] 4. Implementasi setup.py (ensure_git_credentials, clone_repos, prepare_laravel_projects, supervisor, run)
- [x] 5. Implementasi deploy.py (ci-monitor pull, branch per site)
- [x] 6. Unit test hijau (`python -m unittest`)
- [x] 7. Jalankan setup ke VPS UC (apt, node/bun, clone, build, nginx http, certbot)
- [x] 8. Verifikasi semua subdomain HTTP 200 + integration test
- [x] 9. Perbaiki temuan runtime sampai semua hijau
- [ ] 10. Update README + commit + push

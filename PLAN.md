# PLAN

## Task: Rename portfolio (hello-repo -> portfolio, hapus /var/www/hello)

Keputusan: repo `/var/www/portfolio`, webroot nginx langsung
`/var/www/portfolio/fe/dist` (tanpa copy), folder `/var/www/hello` dihapus.

- [x] 1. Tulis PLAN.md
- [x] 2. TDD: test gagal untuk path portfolio di config, templates, deploy
- [x] 3. Implementasi config.py (repo_dir, deploy_root)
- [x] 4. Implementasi templates.py (nginx default, BE service, CICD)
- [x] 5. Implementasi deploy.py + setup.py (tanpa copy dist)
- [x] 6. Update test lama + README + .env.example
- [x] 7. Unit test hijau (`python -m unittest`)
- [x] 8. Migrasi VPS: mv repo, rm /var/www/hello, rebuild, nginx, BE service
- [x] 9. Verifikasi subdomain 200
- [ ] 10. Lapor perubahan (tanpa auto commit)

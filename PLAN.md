# PLAN

## Task: gitpush semua perubahan (12 Nov 2026)

- [x] 1. Tulis PLAN.md (file ini)
- [x] 2. TDD: test gagal untuk `expected_repo_dirs()` di modules/vps/config.py
- [x] 3. Implementasi `expected_repo_dirs()` + pakai di integration test_04
- [x] 4. TDD: test gagal "tidak ada password hardcoded" (modules/skripsi + modules/vps)
- [x] 5. Hapus password hardcoded, wajib dari env (fail fast bila kosong)
- [x] 6. .gitignore untuk artifact `skripsi_setup.log`
- [x] 7. Update README modules/vps + catatan skripsi (env-only kredensial)
- [x] 8. Jalankan `python -m unittest` penuh sampai hijau
- [ ] 9. Commit granular + push ke origin

## Arsip: task sebelumnya (selesai)

- [x] 1. Fix nginx nesting bug, SSL semua subdomain, certbot semua project
- [x] 2. Deploy git-pull based di VPS (portfolio, karta, klinik)
- [x] 3. CI/CD workflow untuk semua project
- [x] 4. Setup dari nol: composer, clone 3 repo, be bun install, php-fpm/redis, ci-monitor, laravel env
- [x] 5. Load .env file di config.py (`load_env` + `from_env(env_file=)`)
- [x] 6. Update .env.example dengan VPS placeholder
- [x] 7. Buat integration test file (`test_integration.py`)
- [x] 8. Fix ssh.py: pass password untuk decrypt encrypted SSH key
- [x] 9. Jalankan integration test ke VPS real (nginx, services, certs, subdomains)
- [x] 10. Run `python -m unittest` full suite
- [x] 11. Commit + push
- [x] 12. Buat 9 gap card Trello klinik dari trello-gap-cards.md (dengan labels, checklist AC, detail lengkap)
- [x] 13. Buat 22 pecahan card Trello klinik (parse dari trello-gap-cards.md) + AGENTS.md rule loading animation

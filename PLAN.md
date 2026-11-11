# PLAN

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

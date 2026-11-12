# Project Rules

## payload
- jangan sampai Payload too large (3555060 chars). Max 3000000. Kurangi history.

## Git: Jangan Auto Commit / Push

- JANGAN `git commit` atau `git push` atas inisiatif sendiri, termasuk setelah
  task selesai, test hijau, atau PLAN tercentang.
- Selesaikan pekerjaan sampai file di disk, lalu LAPORKAN perubahan
  (daftar file + ringkasan) dan TANYAKAN apakah boleh di-commit.
- Hanya commit/push setelah user memberi izin eksplisit pada giliran itu.
  Izin sekali tidak berlaku untuk task berikutnya.
- Jika user meminta commit, tetap commit granular per topik dengan pesan
  `[Tipe] deskripsi` dan jangan mencampur file yang tidak terkait.

## Testing

- Use Test-Driven Development (TDD) for every feature, bug fix, and task in this repository.
- Before writing implementation code, add or update a failing test that describes the expected behavior.
- Run the relevant tests first and confirm they fail for the expected reason.
- Implement the smallest useful change needed to make the tests pass.
- Run `python -m unittest` before finishing a task.
- Refactor only while keeping tests green.
- Do not add implementation-only changes without test coverage unless the change is documentation, configuration, or generated files.

## Modules

- Keep each feature inside its own module under `modules/`.
- Expose a module through its `__init__.py`.
- Place module-specific tests inside the module under a `tests/` folder, for example `modules/<module_name>/tests/test_<feature>.py`.

## Accurate Automation

- Before automating, accessing, testing, or analyzing Accurate, you MUST
  read and follow `skills/accurate-human-automation/SKILL.md`.
- Accurate analysis MUST use REA MCP or the REA CLI command
  `capture-browser-scenario`; do not rely on assumptions alone.
- Accurate automation must run at a human pace and MUST NOT appear bot-like
  through rapid sequential actions.
- The browser may run headless, but timing, action order, and interaction
  must remain natural.
- Credentials may only come from `ACCURATE_EMAIL` and `ACCURATE_PASSWORD`
  in `.env`; do not write actual values into scenarios, skills, or
  documentation.
- Retries MUST NOT run quickly; use randomized delays and limit the number
  of attempts.
- dont capture image and dont analisa from image

## Accurate Documentation Files

- `modules/accurate/<menu>/data.json` MUST contain only the actual table
  records captured from Accurate (`table.columns`, `table.record_count`,
  `table.records`). It MUST NOT contain column documentation, filters,
  inputs, buttons, or form structure.
- Column, filter, form, and button documentation belongs in
  `modules/accurate/<menu>/<menu>.json` and `<menu>.md` only.
- If the table is empty, write `record_count: 0` and `records: []`.
  Never fill `data.json` with structural documentation as a substitute
  for missing data.

## Skill Routing (Wajib)

- Setiap task WAJIB TDD: test gagal dulu, baru implementasi (lihat bagian
  Testing di atas). Skill yang dipakai tidak mengubah aturan TDD ini.
- Sebelum mengerjakan task, cocokkan konteks task dengan tabel routing di
  bawah, lalu BACA `SKILL.md` skill yang dipetakan sebelum menulis kode.
- Task yang menyentuh `modules/accurate/` dalam bentuk apa pun WAJIB baca
  `skills/accurate-human-automation/SKILL.md` terlebih dahulu.
- Pemetaan menu Accurate sumber rujukan:
  `modules/accurate/accurate-sidebar-menu.md` bagian Skill Untuk
  Pengerjaan Fitur.

### Pemetaan Konteks Task ke Skill

| Kata kunci / konteks task | Skill | Menu Accurate terkait |
| --- | --- | --- |
| jurnal, posting, GL, buku besar | `journal-entries` | Buku Besar |
| klasifikasi transaksi, coding ke akun | `classify-transactions` | Buku Besar, Kas & Bank |
| COA, daftar akun, chart of accounts | `chart-of-accounts` | Buku Besar |
| neraca saldo, trial balance, ATB | `adjusted-trial-balance` | Buku Besar |
| depresiasi, akrual, prabayar, AJE, akhir tahun | `year-end-adjustments` | Buku Besar, Perusahaan (Proses Akhir Bulan) |
| bank, rekening koran, statement, saldo bank | `extract-bank-statement`, `bank-reconciliation` | Kas & Bank |
| rekonsiliasi AR/AP, subledger, umur piutang | `subledger-reconciliations` | Penjualan, Pembelian |
| pembukuan multi-stream, register transaksi | `record-transactions` | Kas & Bank, Penjualan, Pembelian |
| pendapatan, cut-off penjualan, principal/agent | `revenue-recognition` | Penjualan |
| kapitalisasi, PPE, renovasi, perbaikan aset | `capitalise-or-expense`, `capex` | Aset Tetap, Pembelian |
| pajak, PPN, Form C, SPT, e-Faktur | `tax-computation` | SmartLink Tax |
| pembukuan penuh end-to-end | `do-books` | Semua menu |
| ragu memilih skill akuntansi | `ask-accounting` | Semua menu |

- Jika satu task menyentuh beberapa konteks, pakai semua skill yang
  dipetakan; urutan kerja ikuti alur `do-books` bila end-to-end.
- Skill UI (`emotion-ui-ux`, `web-design-guidelines`) tetap wajib untuk
  task UI/UX sesuai bagian UI/UX Animation Standard: Emotion.

## UI/UX Animation Standard: Emotion

- **Emotion adalah standar WAJIB untuk semua styling dan animasi UI/UX**
  (Emotion is the mandatory standard for all UI/UX styling and animation)
  in this repository. Use `@emotion/css` for static HTML and
  `@emotion/react` for React.
- This standard MUST be used together with the
  `skills/emotion-ui-ux/SKILL.md` skill.
- Agent TIDAK BOLEH memakai blok `<style>` lama, file CSS global manual,
  inline `style`, atau framework styling lain untuk UI tanpa keputusan
  baru dari user.
- Setiap tombol yang mengirim data ke server (form submit, POST/PUT/DELETE
  via fetch/axios) WAJIB menggunakan disabled loading animation: button
  dinonaktifkan selama request berjalan, dibarengi indikator visual
  spinner atau progress feedback. Tombol kembali aktif setelah response
  diterima atau gagal. Wajib memakai Emotion `css` dan `keyframes`.
- UI animation MUST use Emotion's `css`, `keyframes`, and/or
  `injectGlobal`, remain readable, and respect `prefers-reduced-motion`.
- For UI/UX, animation, motion smoothness, and interactivity, you MUST
  follow `public/ssstik.io_1793164540873.mp4` as the 100% motion reference.
  Do not change style, timing, easing, or interactive feedback without a
  new user decision.

## Deploy & Push Workflow (VPS haidinata.my.id)

- Setelah `git push`, tugas dianggap SELESAI. Jangan menunggu, sleeping,
  atau SSH verifikasi ke VPS setelah push — pipeline GitHub Actions yang
  menangani deploy, statusnya ada di tab Actions masing-masing repo.
- Semua project di VPS UC sudah CI/CD: klinik (branch `haidi`/`main`),
  karta (`dev`/`main`), portfolio haidi20 (`main`).
- Build dilakukan SEBELUM commit (portfolio: `npm run build` di `fe/`),
  bukan setelah push. CI yang melakukan build ulang untuk pipeline baru.
- Modul `modules/vps` (`python -m modules.vps audit|health|deploy|setup`)
  hanya untuk inspeksi darurat atau deploy manual - bukan bagian dari
  alur push normal.

# Project Rules

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

## Konten Video: Generator & Pipeline TikTok

- Tool video AI yang dipakai untuk generate konten adalah **Kling AI**
  (keputusan user, 2026-10-21). Jangan gunakan tool generator video lain
  (Runway, Hailuo, Pika, dll) untuk fitur project ini tanpa keputusan
  baru dari user.
- Alur konten yang disepakati: generate video via Kling AI -> upload ke
  TikTok sebagai draft/private via jalur resmi (Postiz atau Content
  Posting API) -> publish final manual oleh user dari app TikTok.
- Automation video hanya sampai status draft/private di TikTok.
  Publish final TIDAK BOLEH diotomasi dan tetap dilakukan manual oleh user.
- Agent TIDAK BOLEH membuat otomasi publish public tanpa app yang sudah
  lolos audit TikTok; publish final adalah keputusan manual user.
- Kredensial (API key Kling, token TikTok, kredensial Postiz) WAJIB di
  `.env` dan tidak boleh di-commit.
- Video Kaltim memakai format pembahasan lengkap 3 berita terbaru:
  setiap berita punya scene pengantar dan scene detail, lalu ditutup
  kesimpulan yang menjelaskan dampak serta tindak lanjut.
- Target durasi default adalah minimum 60 detik. Durasi final tetap
  mengikuti audio sampai pembahasan selesai; agent TIDAK BOLEH memaksa
  scene ke slot tetap sampai muncul keheningan panjang.
- Narasi WAJIB dibangun dari isi lengkap halaman artikel, bukan hanya
  judul atau ringkasan RSS. Penyampaian harus jelas, tidak singkat,
  tidak terpotong secara berlebihan, dan menjelaskan konteks, fakta
  utama, dampak, serta tindak lanjut.
- Dubbing TIDAK BOLEH hanya membaca ulang judul berita. Gunakan narasi
  pembahasan yang menjelaskan konteks, fakta, dampak, dan tindak lanjut.
- Visual video TIDAK BOLEH memunculkan indikator "Scene x/y". Footer
  cukup menampilkan sumber dan progress video.
- Animasi konten WAJIB terus bergerak secara halus dan punya variasi
  motion per layout; jangan hanya sekali reveal lalu diam seperti PPT.
- Animasi TIDAK BOLEH terlihat seperti PPT. Setiap layout WAJIB punya
  motif gerak khas yang terus berjalan, gerakan konten harus terlihat
  jelas, dan transisi antar elemen harus dinamis namun tetap mudah dibaca.
- Gunakan skill animasi lokal di `skills/emilkowalski/` sebagai acuan
  motion. Token wajib memakai `ease-out` kuat untuk entrance,
  `ease-in-out` kuat untuk movement on-screen, entrance 200ms, stagger
  50ms, dan hindari gerakan yang mengganggu keterbacaan data.
- Tiga detik pertama video WAJIB memakai hook konkret sesuai skill
  `skills/linkedin-hook-generator/SKILL.md`. Hook harus pendek, langsung,
  punya angka atau janji hasil, tidak mengulang judul berita, dan tetap
  tampil sebagai overlay hanya dalam 3 detik pertama.
- Jika isi artikel gagal diambil, pipeline harus gagal jelas atau
  memakai fallback ringkasan dengan penandaan sumber; jangan membuat
  narasi yang terdengar lengkap padahal hanya dari judul.


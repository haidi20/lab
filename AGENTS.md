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
- Agent TIDAK BOLEH membuat otomasi publish public tanpa app yang sudah
  lolos audit TikTok; publish final adalah keputusan manual user.
- Kredensial (API key Kling, token TikTok, kredensial Postiz) WAJIB di
  `.env` dan tidak boleh di-commit.

